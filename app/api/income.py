from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.models import User, Transaction, Document
from app.api.deps import get_current_user
from app.schemas.transaction import TransactionOut, TransactionCreate, TransactionUpdate
from app.services.transaction_service import log_audit, revalidate_transaction, clear_resolved_duplicate_anomaly

router = APIRouter()

from datetime import date
from sqlalchemy import or_

@router.get("", response_model=List[TransactionOut])
def get_incomes(
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    customer: str | None = None,
    invoice_number: str | None = None,
    category_id: UUID | None = None,
    payment_status: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(
        Transaction.company_id == current_user.company_id,
        Transaction.type == "INCOME"
    )
    if status:
        query = query.filter(Transaction.status == status)
    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)
    if customer:
        query = query.filter(Transaction.vendor_customer.ilike(f"%{customer}%"))
    if invoice_number:
        query = query.filter(Transaction.invoice_number.ilike(f"%{invoice_number}%"))
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if payment_status:
        query = query.filter(Transaction.payment_status == payment_status)
    if search:
        query = query.filter(
            or_(
                Transaction.vendor_customer.ilike(f"%{search}%"),
                Transaction.invoice_number.ilike(f"%{search}%"),
                Transaction.notes.ilike(f"%{search}%")
            )
        )
        
    return query.all()

@router.get("/{id}", response_model=TransactionOut)
def get_income(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    income = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "INCOME"
    ).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
        
    if income.status != "APPROVED":
        if clear_resolved_duplicate_anomaly(db, income):
            db.commit()
            db.refresh(income)

    return income

@router.post("", response_model=TransactionOut)
def create_income(income_in: TransactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_income = Transaction(
        **income_in.model_dump(exclude={'type'}), 
        company_id=current_user.company_id,
        type="INCOME"
    )
    db.add(db_income)
    db.flush()
    log_audit(db, current_user.company_id, current_user.id, "TRANSACTION", db_income.id, "TRANSACTION_CREATED")
    db.commit()
    db.refresh(db_income)
    return db_income

@router.patch("/{id}", response_model=TransactionOut)
def update_income(id: UUID, income_in: TransactionUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    income = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "INCOME"
    ).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
        
    update_data = income_in.model_dump(exclude_unset=True)
    
    changes_made = False
    for key, new_value in update_data.items():
        old_value = getattr(income, key)
        if old_value != new_value:
            log_audit(
                db,
                current_user.company_id,
                current_user.id,
                "TRANSACTION",
                income.id,
                "FIELD_UPDATE",
                field=key,
                old_value=old_value,
                new_value=new_value
            )
            setattr(income, key, new_value)
            changes_made = True
            
    if changes_made:
        new_anomalies = revalidate_transaction(db, income, income.document)
        income.anomalies = new_anomalies
        log_audit(db, current_user.company_id, current_user.id, "TRANSACTION", income.id, "TRANSACTION_UPDATED")
    db.commit()
    db.refresh(income)
    return income

@router.post("/{id}/approve")
def approve_income(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["CEO", "FINANCE"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    income = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "INCOME"
    ).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
        
    # Clear any resolved duplicate anomaly if the duplicate was deleted
    if income.status != "APPROVED":
        if clear_resolved_duplicate_anomaly(db, income):
            db.commit()
            db.refresh(income)

    if income.anomalies and len(income.anomalies) > 0:
        raise HTTPException(status_code=400, detail="Cannot approve transaction with unresolved anomalies")
        
    income.status = "APPROVED"
    log_audit(db, current_user.company_id, current_user.id, "TRANSACTION", income.id, "TRANSACTION_APPROVED")
    db.commit()
    db.refresh(income)
    
    return {"status": "APPROVED"}

@router.post("/{id}/reject")
def reject_income(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["CEO", "FINANCE"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    income = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "INCOME"
    ).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
        
    income.status = "REJECTED"
    db.commit()
    return {"status": "REJECTED"}

@router.delete("/{id}")
def delete_income(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    income = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "INCOME"
    ).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
        
    doc_id = income.document_id
    log_audit(db, current_user.company_id, current_user.id, "TRANSACTION", income.id, "TRANSACTION_DELETED")
    
    db.delete(income)
    
    if doc_id:
        other_tx = db.query(Transaction).filter(Transaction.document_id == doc_id, Transaction.id != id).first()
        if not other_tx:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                db.delete(doc)
                
    # Revalidate remaining unapproved transactions that were flagged with DUPLICATE_TRANSACTION
    peer_txs = db.query(Transaction).filter(
        Transaction.company_id == current_user.company_id,
        Transaction.status != "APPROVED"
    ).all()
    for peer in peer_txs:
        clear_resolved_duplicate_anomaly(db, peer)

    db.commit()
    return {"message": "Income deleted successfully"}

