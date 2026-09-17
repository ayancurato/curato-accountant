import pytest
from app.models.audit import AuditLog
from app.models.transaction import Transaction
from uuid import uuid4

def test_audit_trail_updates(client, auth_headers, db_session):
    from app.models import Company, Document
    from datetime import date
    from decimal import Decimal
    
    company = db_session.query(Company).first()
    
    doc = Document(
        company_id=company.id,
        file_name="mock.pdf",
        file_path="mock/path.pdf",
        file_type="application/pdf",
        file_size=1024,
        file_hash="audit-mock-hash",
        status="PROCESSED",
        uploaded_by=company.id
    )
    db_session.add(doc)
    
    # 1. Base tx
    base_tx = Transaction(
        company_id=company.id,
        document_id=doc.id,
        type="EXPENSE",
        vendor_customer="Original Vendor",
        invoice_number="INV-001",
        date=date(2030, 1, 1),
        total_amount=Decimal("1000.50"),
        status="NEEDS_REVIEW",
        anomalies=[{"type": "CATEGORY_MISSING", "message": "Missing category"}]
    )
    db_session.add(base_tx)
    db_session.commit()
    
    tx_id = base_tx.id
    
    # A. Change one field -> exactly one audit record (plus TRANSACTION_UPDATED)
    patch_resp = client.patch(f"/api/v1/expenses/{tx_id}", json={"vendor_customer": "New Vendor"}, headers=auth_headers)
    assert patch_resp.status_code == 200
    
    logs = db_session.query(AuditLog).filter(AuditLog.entity_id == tx_id, AuditLog.action == "FIELD_UPDATE").all()
    assert len(logs) == 1
    assert logs[0].field == "vendor_customer"
    assert logs[0].old_value == "Original Vendor"
    assert logs[0].new_value == "New Vendor"
    
    # B. Change three fields -> exactly three audit records
    patch_resp2 = client.patch(f"/api/v1/expenses/{tx_id}", json={
        "invoice_number": "INV-002",
        "date": "2030-01-02",
        "total_amount": "1000.60"
    }, headers=auth_headers)
    assert patch_resp2.status_code == 200
    
    logs_b = db_session.query(AuditLog).filter(AuditLog.entity_id == tx_id, AuditLog.action == "FIELD_UPDATE").all()
    assert len(logs_b) == 4 # 1 from previous + 3 new
    fields = [log.field for log in logs_b]
    assert "invoice_number" in fields
    assert "date" in fields
    assert "total_amount" in fields
    
    # C. Submit unchanged value -> zero audit records
    patch_resp3 = client.patch(f"/api/v1/expenses/{tx_id}", json={
        "invoice_number": "INV-002"
    }, headers=auth_headers)
    assert patch_resp3.status_code == 200
    
    logs_c = db_session.query(AuditLog).filter(AuditLog.entity_id == tx_id, AuditLog.action == "FIELD_UPDATE").all()
    assert len(logs_c) == 4 # no new records
    
    # E. Fix anomaly
    from app.models import Category
    cat = db_session.query(Category).first()
    patch_resp4 = client.patch(f"/api/v1/expenses/{tx_id}", json={
        "category_id": str(cat.id),
        "net_amount": "1000.60", # match total to avoid amount mismatch
        "gst_amount": "0"
    }, headers=auth_headers)
    assert patch_resp4.status_code == 200
    
    # Anomaly should be cleared
    tx_updated = patch_resp4.json()
    assert len(tx_updated["anomalies"]) == 0
    
    # But audit record remains
    logs_e = db_session.query(AuditLog).filter(AuditLog.entity_id == tx_id, AuditLog.action == "FIELD_UPDATE").all()
    assert len(logs_e) > 4 # new records added for category_id, net_amount, gst_amount
    
    fields = [log.field for log in logs_e]
    assert "category_id" in fields
