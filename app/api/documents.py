from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.document import DocumentOut
from app.schemas.ai import ProcessedInvoiceResponse
from app.models import User, Document
from app.api.deps import get_current_user
from app.services.document_service import save_upload_file
from app.services.ai_service import extract_invoice_data
from app.services.transaction_service import process_ai_result
from uuid import UUID

router = APIRouter()

@router.post("/upload", response_model=List[DocumentOut])
def upload_document(
    files: List[UploadFile] = File(...), 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user.role not in ["CEO", "FINANCE"]:
        raise HTTPException(status_code=403, detail="Not authorized to upload")
    
    documents = []
    for file in files:
        document = save_upload_file(file, current_user)
        db.add(document)
        documents.append(document)
        
    db.commit()
    for doc in documents:
        db.refresh(doc)
    return documents

@router.get("", response_model=list[DocumentOut])
def get_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Document).filter(Document.company_id == current_user.company_id).all()

@router.get("/{id}", response_model=DocumentOut)
def get_document(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id, Document.company_id == current_user.company_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

from fastapi.responses import FileResponse

@router.get("/{id}/file")
def get_document_file(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id, Document.company_id == current_user.company_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return FileResponse(doc.file_path, media_type=doc.file_type, filename=doc.file_name)

@router.post("/{id}/process", response_model=ProcessedInvoiceResponse)
def process_document(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["CEO", "FINANCE"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    doc = db.query(Document).filter(Document.id == id, Document.company_id == current_user.company_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.status in ["PROCESSED", "NEEDS_REVIEW", "READY", "APPROVED"]:
        raise HTTPException(status_code=400, detail="Document already processed")

    doc.status = "PROCESSING"
    db.commit()
    
    try:
        # Extract data using AI
        ai_data = extract_invoice_data(doc.file_path, doc.file_type)
        
        # Process result, validate and create Transaction Draft
        tx, anomalies, is_duplicate, amounts_valid_status = process_ai_result(db, doc, ai_data, current_user)
        
        return {
            "document_id": str(doc.id),
            "transaction_id": str(tx.id),
            "document_status": doc.status,
            "transaction_status": tx.status,
            "vendor_customer": tx.vendor_customer,
            "invoice_number": tx.invoice_number,
            "date": tx.date,
            "currency": ai_data.currency,
            "category": {
                "id": str(tx.category_id),
                "name": tx.category.name if tx.category else None,
                "confidence": ai_data.confidence
            },
            "amounts": {
                "net": float(tx.net_amount),
                "tax": float(tx.gst_amount),
                "total": float(tx.total_amount)
            },
            "tax": {
                "cgst": float(tx.cgst),
                "sgst": float(tx.sgst),
                "igst": float(tx.igst),
                "gst_rate": float(tx.gst_rate) if tx.gst_rate else None,
                "vendor_gstin": tx.vendor_gstin,
                "customer_gstin": tx.customer_gstin
            },
            "payment_status": tx.payment_status,
            "validation": {
                "amounts_valid": amounts_valid_status,
                "is_valid": len(anomalies) == 0,
                "warnings": anomalies
            },
            "possible_duplicate": is_duplicate,
            "anomalies": anomalies
        }

    except Exception as e:
        doc.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
