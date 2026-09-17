import pytest

def test_categories(client, auth_headers):
    # 1. Verify 10 categories exist
    resp = client.get("/api/v1/categories", headers=auth_headers)
    assert resp.status_code == 200
    categories = resp.json()
    assert len(categories) >= 10
    
    cat_names = [c["name"] for c in categories]
    assert "Software, AI & SaaS" in cat_names
    assert "Other" not in cat_names # other should not be seeded
    
    # User can create custom category
    create_resp = client.post("/api/v1/categories", json={"name": "Sales Revenue", "type": "INCOME"}, headers=auth_headers)
    assert create_resp.status_code == 200
    income_cat_id = create_resp.json()["id"]
    
    # Rename category
    patch_resp = client.patch(f"/api/v1/categories/{income_cat_id}", json={"name": "Consulting Revenue"}, headers=auth_headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Consulting Revenue"
    
    # Archive category
    del_resp = client.delete(f"/api/v1/categories/{income_cat_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    
    # Archived categories filtered out
    check_resp = client.get("/api/v1/categories?type=INCOME", headers=auth_headers)
    assert len(check_resp.json()) >= 4

from decimal import Decimal

def test_invoice_pipeline(client, auth_headers, monkeypatch):
    from app.services import ai_service
    # Force use of normal mock with unique ID
    import uuid
    unique_mock = ai_service.mock_ai_response()
    unique_mock.invoice_number = f"INV-12345-TX-{uuid.uuid4()}"
    unique_mock.total_amount = Decimal("118001")
    unique_mock.net_amount = Decimal("100001")
    monkeypatch.setattr(ai_service, "mock_ai_response", lambda: unique_mock)
    
    import uuid
    # Upload
    with open("tests/mock_invoice.pdf", "rb") as f:
        upload_resp = client.post("/api/v1/documents/upload", files=[("files", ("mock_pipeline_tx.pdf", str(uuid.uuid4()).encode(), "application/pdf"))], headers=auth_headers)
    
    doc_id = upload_resp.json()[0]["id"]
    
    # Process
    process_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers)
    assert process_resp.status_code == 200
    result = process_resp.json()
    
    # Valid mapping
    assert result["category"]["name"] == "Software, AI & SaaS"
    print(f"ANOMALIES: {result['anomalies']}")
    assert result["document_status"] == "READY"
    assert result["transaction_status"] == "NEEDS_REVIEW"
    assert result["amounts"]["net"] == 100001.0
    assert result["tax"]["gst_rate"] == 18.0
    
    tx_id = result["transaction_id"]
    
    # Check duplicate
    process_resp_dup = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers)
    assert process_resp_dup.status_code == 400
    
    # Edit tx
    patch_resp = client.patch(f"/api/v1/expenses/{tx_id}", json={"notes": "Test edit"}, headers=auth_headers)
    assert patch_resp.status_code == 200
    
    # Approve
    approve_resp = client.post(f"/api/v1/expenses/{tx_id}/approve", headers=auth_headers)
    assert approve_resp.status_code == 200
    
    # Audit log
    audit_resp = client.get(f"/api/v1/audit/TRANSACTION/{tx_id}", headers=auth_headers)
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) > 0

def test_uncertain_invoice_pipeline(client, auth_headers, monkeypatch):
    from app.services import ai_service
    # Force use of uncertain mock
    monkeypatch.setattr(ai_service, "mock_ai_response", ai_service.mock_ai_response_uncertain)
    
    with open("tests/mock_invoice.jpg", "rb") as f:
        upload_resp = client.post("/api/v1/documents/upload", files=[("files", ("uncertain.jpg", f, "image/jpeg"))], headers=auth_headers)
    
    doc_id = upload_resp.json()[0]["id"]
    process_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers)
    assert process_resp.status_code == 200
    result = process_resp.json()
    
    # Category should be missing
    assert result["category"]["name"] is None
    assert result["document_status"] == "NEEDS_REVIEW"
    assert result["transaction_status"] == "NEEDS_REVIEW"
    
    tx_id = result["transaction_id"]
    
    # Reject transaction
    reject_resp = client.post(f"/api/v1/expenses/{tx_id}/reject", headers=auth_headers)
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "REJECTED"

def test_duplicate_detection(client, auth_headers, db_session):
    from app.services.transaction_service import check_duplicate
    from app.models import Company, Transaction, Document
    from datetime import date
    from uuid import uuid4
    
    company = db_session.query(Company).first()
    
    # 1. Base tx
    base_tx = Transaction(
        company_id=company.id,
        type="EXPENSE",
        vendor_customer="DupVendor",
        invoice_number="INV-001",
        date=date(2030, 1, 1),
        total_amount=Decimal("1000.50"),
        status="APPROVED"
    )
    db_session.add(base_tx)
    
    # Mock document for hash
    doc = Document(
        company_id=company.id,
        file_name="mock.pdf",
        file_path="mock/path.pdf",
        file_type="application/pdf",
        file_size=1024,
        file_hash="mock-hash-123",
        status="PROCESSED",
        uploaded_by=company.id # using company ID as mock user ID
    )
    db_session.add(doc)
    db_session.commit()
    
    # A. Same everything -> DUPLICATE
    assert check_duplicate(db_session, company.id, "DupVendor", "INV-001", Decimal("1000.50"), date(2030, 1, 1), "new-hash") == True
    
    # B. Different date -> NOT DUPLICATE
    assert check_duplicate(db_session, company.id, "DupVendor", "INV-001", Decimal("1000.50"), date(2030, 1, 2), "new-hash") == False
    
    # C. Different amount -> NOT DUPLICATE
    assert check_duplicate(db_session, company.id, "DupVendor", "INV-001", Decimal("1000.60"), date(2030, 1, 1), "new-hash") == False
    
    # D. Different vendor -> NOT DUPLICATE
    assert check_duplicate(db_session, company.id, "OtherVendor", "INV-001", Decimal("1000.50"), date(2030, 1, 1), "new-hash") == False
    
    # E. Different invoice -> NOT DUPLICATE
    assert check_duplicate(db_session, company.id, "DupVendor", "INV-002", Decimal("1000.50"), date(2030, 1, 1), "new-hash") == False
    
    # F. Same hash -> DUPLICATE
    assert check_duplicate(db_session, company.id, "DupVendor", "INV-999", Decimal("500"), date(2030, 1, 1), "mock-hash-123") == True
