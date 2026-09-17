import pytest
from datetime import date
from decimal import Decimal
import uuid

def test_income_lifecycle(client, auth_headers):
    # Fetch a valid category
    cats_resp = client.get("/api/v1/categories?type=INCOME", headers=auth_headers)
    income_cats = cats_resp.json()
    cat_id = income_cats[0]["id"] if income_cats else "00000000-0000-0000-0000-000000000000"

    # 1. Create income transaction
    create_payload = {
        "type": "INCOME",
        "date": "2026-10-01",
        "due_date": "2026-10-15",
        "vendor_customer": "Acme Corp",
        "invoice_number": f"INC-{uuid.uuid4()}",
        "net_amount": 100000,
        "gst_amount": 18000,
        "cgst": 9000,
        "sgst": 9000,
        "total_amount": 118000,
        "customer_gstin": "27AADCB2230M1Z2",
        "payment_status": "OUTSTANDING",
        "notes": "Consulting work",
        "category_id": cat_id
    }
    
    resp = client.post("/api/v1/income", json=create_payload, headers=auth_headers)
    assert resp.status_code == 200
    income = resp.json()
    assert income["status"] == "DRAFT"
    assert income["type"] == "INCOME"
    assert income["vendor_customer"] == "Acme Corp"
    assert income["payment_status"] == "OUTSTANDING"
    assert income["customer_gstin"] == "27AADCB2230M1Z2"
    
    income_id = income["id"]
    
    # 2. Retrieve income transaction
    resp = client.get(f"/api/v1/income/{income_id}", headers=auth_headers)
    assert resp.status_code == 200
    
    # 3. Update income transaction (PATCH) + Test anomaly persistence
    patch_payload = {
        "payment_status": "RECEIVED",
        "net_amount": 100000,
        "gst_amount": 15000, # Math mismatch to trigger anomaly
        "total_amount": 118000
    }
    resp = client.patch(f"/api/v1/income/{income_id}", json=patch_payload, headers=auth_headers)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["payment_status"] == "RECEIVED"
    
    anomalies = updated.get("anomalies", [])
    assert any(a["type"] == "TOTAL_MISMATCH" for a in anomalies)
    
    # 5. Block approval when anomalies remain
    resp = client.post(f"/api/v1/income/{income_id}/approve", headers=auth_headers)
    assert resp.status_code == 400
    
    # Resolve anomaly
    resp = client.patch(f"/api/v1/income/{income_id}", json={"gst_amount": 18000}, headers=auth_headers)
    updated = resp.json()
    anomalies = updated.get("anomalies", [])
    assert len(anomalies) == 0
    
    # 4. Approve clean income transaction
    resp = client.post(f"/api/v1/income/{income_id}/approve", headers=auth_headers)
    assert resp.status_code == 200
    
    # Verify transaction status vs payment status separation
    resp = client.get(f"/api/v1/income/{income_id}", headers=auth_headers)
    final = resp.json()
    assert final["status"] == "APPROVED"
    assert final["payment_status"] == "RECEIVED"

def test_income_filtering(client, auth_headers):
    unique_inv = f"FLT-{uuid.uuid4()}"
    create_payload = {
        "type": "INCOME",
        "date": "2026-11-01",
        "vendor_customer": "SearchableCustomer",
        "invoice_number": unique_inv,
        "net_amount": 500,
        "total_amount": 500,
        "payment_status": "OUTSTANDING"
    }
    client.post("/api/v1/income", json=create_payload, headers=auth_headers)
    
    # Search by customer
    resp = client.get("/api/v1/income?customer=Searchable", headers=auth_headers)
    data = resp.json()
    assert len(data) >= 1
    assert any(tx["invoice_number"] == unique_inv for tx in data)
    
    # Search by invoice
    resp = client.get(f"/api/v1/income?invoice_number={unique_inv}", headers=auth_headers)
    data = resp.json()
    assert len(data) == 1
    
    # Search generic
    resp = client.get(f"/api/v1/income?search={unique_inv}", headers=auth_headers)
    assert len(resp.json()) == 1

def test_income_audit_trail(client, auth_headers):
    # Audit trail
    create_payload = {
        "type": "INCOME",
        "date": "2026-10-01",
        "due_date": "2026-10-15",
        "vendor_customer": "Audit Corp",
        "invoice_number": f"AUD-{uuid.uuid4()}",
        "net_amount": 1000,
        "gst_amount": 180,
        "total_amount": 1180,
        "customer_gstin": "27AADCB2230M1Z2",
        "payment_status": "RECEIVED",
        "category_id": "00000000-0000-0000-0000-000000000000" # Hack, or I can just provide a valid one if needed
    }
    # To avoid missing category, let's fetch a category first
    cats_resp = client.get("/api/v1/categories?type=INCOME", headers=auth_headers)
    income_cats = cats_resp.json()
    if income_cats:
        create_payload["category_id"] = income_cats[0]["id"]
        
    resp = client.post("/api/v1/income", json=create_payload, headers=auth_headers)
    income_id = resp.json()["id"]
    
    patch_resp = client.patch(f"/api/v1/income/{income_id}", json={"notes": "Audit note"}, headers=auth_headers)
    assert patch_resp.status_code == 200
    
    app_resp = client.post(f"/api/v1/income/{income_id}/approve", headers=auth_headers)
    assert app_resp.status_code == 200
    
    resp = client.get(f"/api/v1/audit/TRANSACTION/{income_id}", headers=auth_headers)
    audit = resp.json()
    assert len(audit) >= 2
    actions = [a["action"] for a in audit]
    assert "TRANSACTION_UPDATED" in actions
    assert "TRANSACTION_APPROVED" in actions
