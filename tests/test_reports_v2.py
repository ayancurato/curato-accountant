import pytest
from datetime import date
from decimal import Decimal
import uuid
from app.models import Transaction

def create_mock_tx(db, type="EXPENSE", status="APPROVED", date_val=None, amount=1000, gst=180, payment_status=None, vendor="Mock Entity"):
    from app.models import Company
    company = db.query(Company).first()
    
    tx = Transaction(
        company_id=company.id,
        type=type,
        status=status,
        date=date_val or date(2030, 5, 15),
        total_amount=Decimal(amount),
        net_amount=Decimal(amount) - Decimal(gst),
        gst_amount=Decimal(gst),
        vendor_customer=vendor,
        invoice_number=f"MOCK-{uuid.uuid4()}",
        payment_status=payment_status or ("PAID" if type == "EXPENSE" else "RECEIVED")
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

from tests.conftest import TestingSessionLocal

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_empty_reports(client, auth_headers, db_session):
    resp = client.get("/api/v1/reports?date_from=2031-01-01&date_to=2031-12-31", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["metrics"]["total_income"]) == 0.0
    assert float(data["metrics"]["total_expenses"]) == 0.0
    assert float(data["metrics"]["net"]) == 0.0
    assert float(data["metrics"]["gst_collected"]) == 0.0
    assert float(data["metrics"]["gst_paid"]) == 0.0
    assert float(data["metrics"]["outstanding_income"]) == 0.0
    assert float(data["metrics"]["unpaid_expenses"]) == 0.0
    
def test_approved_filtering_and_payment_status(client, auth_headers, db_session):
    # DRAFT should be ignored
    create_mock_tx(db_session, type="INCOME", status="DRAFT", amount=5000)
    create_mock_tx(db_session, type="EXPENSE", status="NEEDS_REVIEW", amount=2000)
    
    # APPROVED but paid
    create_mock_tx(db_session, type="INCOME", status="APPROVED", amount=10000, payment_status="RECEIVED", date_val=date(2030, 6, 1))
    # APPROVED and outstanding/unpaid
    create_mock_tx(db_session, type="INCOME", status="APPROVED", amount=2000, payment_status="OUTSTANDING", date_val=date(2030, 6, 2))
    create_mock_tx(db_session, type="EXPENSE", status="APPROVED", amount=3000, payment_status="UNPAID", date_val=date(2030, 6, 3))
    create_mock_tx(db_session, type="EXPENSE", status="APPROVED", amount=1500, payment_status="PAID", date_val=date(2030, 6, 4))

    resp = client.get("/api/v1/reports?date_from=2030-01-01&date_to=2030-12-31", headers=auth_headers)
    data = resp.json()
    
    assert float(data["metrics"]["total_income"]) == 12000.0
    assert float(data["metrics"]["total_expenses"]) == 4500.0
    assert float(data["metrics"]["net"]) == 7500.0
    
    assert float(data["metrics"]["outstanding_income"]) == 2000.0
    assert float(data["metrics"]["unpaid_expenses"]) == 3000.0

def test_reports_aggregation_groupings(client, auth_headers, db_session):
    u_vendor = f"Unique {uuid.uuid4()}"
    create_mock_tx(db_session, type="EXPENSE", status="APPROVED", amount=1000, date_val=date(2030, 4, 1), vendor=u_vendor)
    create_mock_tx(db_session, type="EXPENSE", status="APPROVED", amount=2000, date_val=date(2030, 4, 15), vendor=u_vendor)
    create_mock_tx(db_session, type="EXPENSE", status="APPROVED", amount=5000, date_val=date(2030, 5, 10), vendor=u_vendor)

    resp = client.get("/api/v1/reports?date_from=2030-01-01&date_to=2030-12-31", headers=auth_headers)
    data = resp.json()
    
    # Check expense vendors
    vendors = data["expenses"]["by_vendor"]
    assert any(v["name"] == u_vendor and float(v["amount"]) == 8000.0 for v in vendors)
    
    # Check expense monthly trends
    trends = data["expenses"]["monthly_trend"]
    assert len(trends) >= 2
    april = next(t for t in trends if t["month"] == "2030-04")
    may = next(t for t in trends if t["month"] == "2030-05")
    assert float(april["amount"]) == 3000.0
    assert float(may["amount"]) == 5000.0

def test_reports_date_filtering_custom(client, auth_headers, db_session):
    create_mock_tx(db_session, type="INCOME", status="APPROVED", amount=100, date_val=date(2030, 1, 15))
    create_mock_tx(db_session, type="INCOME", status="APPROVED", amount=200, date_val=date(2030, 2, 1))
    create_mock_tx(db_session, type="INCOME", status="APPROVED", amount=300, date_val=date(2030, 2, 28))
    create_mock_tx(db_session, type="INCOME", status="APPROVED", amount=400, date_val=date(2030, 3, 1))
    
    # Custom dates exact match boundaries (inclusive)
    resp = client.get("/api/v1/reports?date_from=2030-02-01&date_to=2030-02-28", headers=auth_headers)
    data = resp.json()
    
    assert float(data["metrics"]["total_income"]) == 500.0

def test_reports_preset_financial_year(client, auth_headers, db_session):
    resp = client.get("/api/v1/reports?preset=financial_year", headers=auth_headers)
    data = resp.json()
    assert data["period"]["date_from"] is not None
    assert data["period"]["date_to"] is not None
    
    # Assuming today is 2026, if month >= 4, FY is 2026-04-01 to 2027-03-31
    # Check that boundaries make sense
    df = date.fromisoformat(data["period"]["date_from"])
    dt = date.fromisoformat(data["period"]["date_to"])
    
    assert df.month == 4 and df.day == 1
    assert dt.month == 3 and dt.day == 31
    assert dt.year - df.year == 1
