import pytest
from app.services import ai_service
from app.schemas.ai import AIProcessedTransaction
from datetime import date
from decimal import Decimal

# Helper mock generators
def mock_clean_invoice(inv_num="CLN-123") -> AIProcessedTransaction:
    return AIProcessedTransaction(
        document_type="purchase_invoice",
        type="EXPENSE",
        vendor_customer=f"Clean Vendor {inv_num}",
        invoice_number=inv_num,
        invoice_date=date(2026, 1, 1),
        currency="INR",
        net_amount=Decimal("1000"),
        gst_amount=Decimal("180"),
        cgst=Decimal("90"),
        sgst=Decimal("90"),
        total_amount=Decimal("1180"),
        category="Software, AI & SaaS",
        confidence=0.95
    )

def mock_missing_field() -> AIProcessedTransaction:
    return AIProcessedTransaction(
        document_type="purchase_invoice",
        type="EXPENSE",
        vendor_customer="Missing Vendor",
        invoice_number=None, # Missing required field
        invoice_date=date(2026, 1, 1),
        currency="INR",
        net_amount=Decimal("1000"),
        gst_amount=Decimal("180"),
        total_amount=Decimal("1180"),
        category="Software, AI & SaaS",
        confidence=0.95
    )

def mock_amount_mismatch() -> AIProcessedTransaction:
    return AIProcessedTransaction(
        document_type="purchase_invoice",
        type="EXPENSE",
        vendor_customer="Mismatch Vendor",
        invoice_number="MIS-123",
        invoice_date=date(2026, 1, 1),
        currency="INR",
        net_amount=Decimal("1000"),
        gst_amount=Decimal("100"), # 1100 != 1180
        total_amount=Decimal("1180"),
        category="Software, AI & SaaS",
        confidence=0.95
    )

def upload_and_process(client, auth_headers, filename="test.pdf"):
    # Generate unique content to ensure unique file_hash
    unique_content = f"mock content {filename}".encode()
    upload_resp = client.post("/api/v1/documents/upload", files=[("files", (filename, unique_content, "application/pdf"))], headers=auth_headers)
    
    doc_id = upload_resp.json()[0]["id"]
    process_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers)
    assert process_resp.status_code == 200
    return process_resp.json()

def test_clean_invoice_status(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.api.documents.extract_invoice_data", lambda f, m: mock_clean_invoice("CLN-001"))
    
    result = upload_and_process(client, auth_headers, "clean1.pdf")
    assert result["document_status"] == "READY"
    assert result["transaction_status"] == "NEEDS_REVIEW"

def test_missing_required_field_status(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.api.documents.extract_invoice_data", lambda f, m: mock_missing_field())
    
    result = upload_and_process(client, auth_headers, "missing1.pdf")
    assert result["document_status"] == "NEEDS_REVIEW"
    assert result["transaction_status"] == "NEEDS_REVIEW"
    assert any(a["type"] == "MISSING_INVOICE_NUMBER" for a in result["anomalies"])

def test_amount_mismatch_status(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.api.documents.extract_invoice_data", lambda f, m: mock_amount_mismatch())
    
    result = upload_and_process(client, auth_headers, "mismatch1.pdf")
    assert result["document_status"] == "NEEDS_REVIEW"
    assert result["transaction_status"] == "NEEDS_REVIEW"
    assert result["validation"]["amounts_valid"] == "MISMATCH"

def test_potential_duplicate_status(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.api.documents.extract_invoice_data", lambda f, m: mock_clean_invoice("DUP-001"))
    
    # Process once
    result1 = upload_and_process(client, auth_headers, "dup1.pdf")
    assert result1["document_status"] == "READY"
    
    # Process again with same invoice number and vendor
    result2 = upload_and_process(client, auth_headers, "dup2.pdf")
    assert result2["document_status"] == "NEEDS_REVIEW"
    assert result2["transaction_status"] == "NEEDS_REVIEW"
    assert result2["possible_duplicate"] == True

def test_explicit_user_approval(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.api.documents.extract_invoice_data", lambda f, m: mock_clean_invoice("APP-001"))
    
    result = upload_and_process(client, auth_headers, "approve1.pdf")
    tx_id = result["transaction_id"]
    
    # Transaction is initially NEEDS_REVIEW
    assert result["transaction_status"] == "NEEDS_REVIEW"
    
    # Approve
    approve_resp = client.post(f"/api/v1/expenses/{tx_id}/approve", headers=auth_headers)
    assert approve_resp.status_code == 200
    
    # Fetch to verify
    get_resp = client.get(f"/api/v1/expenses/{tx_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "APPROVED"
    
    # Document status should still be independent (READY)
    doc_resp = client.get("/api/v1/documents", headers=auth_headers)
    docs = [d for d in doc_resp.json() if d["id"] == result["document_id"]]
    assert docs[0]["status"] == "READY"
