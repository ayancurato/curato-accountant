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

@router.get("", response_model=List[TransactionOut])
def get_expenses(
    status: str | None = None,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(
        Transaction.company_id == current_user.company_id,
        Transaction.type == "EXPENSE"
    )
    if status:
        query = query.filter(Transaction.status == status)
    return query.all()

@router.get("/{id}", response_model=TransactionOut)
def get_expense(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "EXPENSE"
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    if expense.status != "APPROVED":
        if clear_resolved_duplicate_anomaly(db, expense):
            db.commit()
            db.refresh(expense)

    return expense

@router.post("", response_model=TransactionOut)
def create_expense(expense_in: TransactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_expense = Transaction(
        **expense_in.model_dump(exclude={'type'}), 
        company_id=current_user.company_id,
        type="EXPENSE"
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@router.patch("/{id}", response_model=TransactionOut)
def update_expense(id: UUID, expense_in: TransactionUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "EXPENSE"
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    update_data = expense_in.model_dump(exclude_unset=True)
    
    # Track original vs new for audit trail exactly according to PRD
    changes_made = False
    for key, new_value in update_data.items():
        old_value = getattr(expense, key)
        if old_value != new_value:
            log_audit(
                db, 
                current_user.company_id, 
                current_user.id, 
                "TRANSACTION", 
                expense.id, 
                "FIELD_UPDATE",
                field=key,
                old_value=old_value,
                new_value=new_value
            )
            setattr(expense, key, new_value)
            changes_made = True
            
    if changes_made:
        # Revalidate transaction
        new_anomalies = revalidate_transaction(db, expense, expense.document)
        expense.anomalies = new_anomalies
        log_audit(db, current_user.company_id, current_user.id, "TRANSACTION", expense.id, "TRANSACTION_UPDATED")
    db.commit()
    db.refresh(expense)
    return expense

@router.post("/{id}/approve")
def approve_expense(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["CEO", "FINANCE"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    expense = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "EXPENSE"
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    # Clear any resolved duplicate anomaly if the duplicate was deleted
    if expense.status != "APPROVED":
        if clear_resolved_duplicate_anomaly(db, expense):
            db.commit()
            db.refresh(expense)

    if expense.anomalies and len(expense.anomalies) > 0:
        raise HTTPException(status_code=400, detail="Cannot approve transaction with unresolved anomalies")
        
    expense.status = "APPROVED"
    log_audit(db, current_user.company_id, current_user.id, "TRANSACTION", expense.id, "TRANSACTION_APPROVED")
    db.commit()
    db.refresh(expense)
    
    return {"status": "APPROVED"}

@router.post("/{id}/reject")
def reject_expense(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["CEO", "FINANCE"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    expense = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "EXPENSE"
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    expense.status = "REJECTED"
    log_audit(db, current_user.company_id, current_user.id, "TRANSACTION", expense.id, "TRANSACTION_REJECTED")
    db.commit()
    return {"status": "REJECTED"}

@router.delete("/{id}")
def delete_expense(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.query(Transaction).filter(
        Transaction.id == id,
        Transaction.company_id == current_user.company_id,
        Transaction.type == "EXPENSE"
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    doc_id = expense.document_id
    log_audit(db, current_user.company_id, current_user.id, "TRANSACTION", expense.id, "TRANSACTION_DELETED")
    
    db.delete(expense)
    
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
    return {"message": "Expense deleted successfully"}

