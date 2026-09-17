import pytest
from uuid import uuid4
import json
from decimal import Decimal

def test_anomalies_workflow(client, auth_headers):
    # 1. Clean transaction: anomalies = []
    file_content = b"fake pdf content"
    files = {"files": ("clean.pdf", file_content, "application/pdf")}
    resp = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    assert resp.status_code == 200
    doc_id = resp.json()[0]["id"]
    
    # Process it.
    resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers)
    assert resp.status_code == 200
    process_data = resp.json()
    assert len(process_data["anomalies"]) == 0
    tx_id = process_data["transaction_id"]
    
    # Check due_date
    resp = client.get(f"/api/v1/expenses/{tx_id}", headers=auth_headers)
    tx_data = resp.json()
    assert tx_data["due_date"] == "2026-10-15"
    # I'll check mock_ai_response. It returns no due_date currently! I'll patch the transaction instead.
    
    # 2. Missing GSTIN: anomalies contains MISSING_GSTIN
    patch_data = {
        "vendor_gstin": None,
        "gst_amount": 100,
        "net_amount": 1000,
        "total_amount": 1100
    }
    resp = client.patch(f"/api/v1/expenses/{tx_id}", json=patch_data, headers=auth_headers)
    assert resp.status_code == 200
    tx_data = resp.json()
    types = [a["type"] for a in tx_data["anomalies"]]
    assert "MISSING_GSTIN" in types
    
    # 3. User fixes GSTIN through PATCH: MISSING_GSTIN disappears
    resp = client.patch(f"/api/v1/expenses/{tx_id}", json={"vendor_gstin": "27AADCB2230M1Z2"}, headers=auth_headers)
    tx_data = resp.json()
    types = [a["type"] for a in tx_data["anomalies"]]
    assert "MISSING_GSTIN" not in types
    
    # 4. User fixes only one of multiple issues
    patch_data_multi = {
        "invoice_number": None,
        "total_amount": 5000 # Mismatch
    }
    resp = client.patch(f"/api/v1/expenses/{tx_id}", json=patch_data_multi, headers=auth_headers)
    types = [a["type"] for a in resp.json()["anomalies"]]
    assert "MISSING_INVOICE_NUMBER" in types
    assert "TOTAL_MISMATCH" in types
    
    resp = client.patch(f"/api/v1/expenses/{tx_id}", json={"invoice_number": "INV-NEW"}, headers=auth_headers)
    types = [a["type"] for a in resp.json()["anomalies"]]
    assert "MISSING_INVOICE_NUMBER" not in types
    assert "TOTAL_MISMATCH" in types
    
    # 5. Refresh/retrieve transaction
    resp = client.get(f"/api/v1/expenses/{tx_id}", headers=auth_headers)
    types = [a["type"] for a in resp.json()["anomalies"]]
    assert "TOTAL_MISMATCH" in types
    
    # 9. Approval cannot bypass blocking validation issues
    resp = client.post(f"/api/v1/expenses/{tx_id}/approve", headers=auth_headers)
    assert resp.status_code == 400
    assert "Cannot approve transaction with unresolved anomalies" in resp.json()["detail"]
    
    # 8. GST mismatch is recalculated after edits
    resp = client.patch(f"/api/v1/expenses/{tx_id}", json={"total_amount": 1100}, headers=auth_headers)
    assert len(resp.json()["anomalies"]) == 0
    
    # 10. Clean transaction can still be approved
    resp = client.post(f"/api/v1/expenses/{tx_id}/approve", headers=auth_headers)
    assert resp.status_code == 200
    
    # 7. Duplicate anomaly persists
    files2 = {"files": ("dup.pdf", file_content, "application/pdf")}
    resp = client.post("/api/v1/documents/upload", files=files2, headers=auth_headers)
    doc_id2 = resp.json()[0]["id"]
    resp = client.post(f"/api/v1/documents/{doc_id2}/process", headers=auth_headers)
    tx_id2 = resp.json()["transaction_id"]
    
    # Trigger duplicate
    resp = client.patch(f"/api/v1/expenses/{tx_id2}", json={
        "vendor_customer": resp.json()["vendor_customer"],
        "invoice_number": "INV-NEW" # matches the updated one
    }, headers=auth_headers)
    
    types = [a["type"] for a in resp.json()["anomalies"]]
    assert "DUPLICATE_TRANSACTION" in types
