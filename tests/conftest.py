import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from decimal import Decimal

# Mock GROQ API key for all tests
os.environ["GROQ_API_KEY"] = "mock-api-key"

from app.main import app
from app.core.database import get_db, Base
from app.models import Company, User, Category
from app.core.security import get_password_hash
from app.core.config import settings

settings.GROQ_API_KEY = "mock-api-key"

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

CATEGORIES = [
    "Legal, Compliance & Government Fees",
    "Software, AI & SaaS",
    "Salaries & Intern Stipends",
    "Freelancers & Professional Services",
    "Marketing & Advertising",
    "Office Supplies, Equipment & Furniture",
    "Travel, Meals & Entertainment",
    "Telecom & Internet",
    "Rent & Utilities",
    "Banking, Payment & Other Business Charges"
]

INCOME_CATEGORIES = [
    "Consulting Services",
    "Software Sales",
    "Interest & Dividends",
    "Other Income"
]

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    company = Company(name="Test Co", country="India", currency="INR", tax_type="GST")
    db.add(company)
    db.commit()
    
    user = User(company_id=company.id, name="CEO", email="test@test.com", password_hash=get_password_hash("password"), role="CEO")
    db.add(user)
    
    for cat_name in CATEGORIES:
        db.add(Category(company_id=company.id, name=cat_name, type="EXPENSE"))
    for cat_name in INCOME_CATEGORIES:
        db.add(Category(company_id=company.id, name=cat_name, type="INCOME"))
    db.commit()
    
    with open("tests/mock_invoice.pdf", "wb") as f:
        f.write(b"mock pdf content")
        
    with open("tests/mock_invoice.jpg", "wb") as f:
        f.write(b"mock image content")

    with open("tests/mock_invoice.png", "wb") as f:
        f.write(b"mock image content")
    
    yield
    Base.metadata.drop_all(bind=engine)
    for ext in ["pdf", "jpg", "png"]:
        if os.path.exists(f"tests/mock_invoice.{ext}"):
            os.remove(f"tests/mock_invoice.{ext}")

@pytest.fixture(scope="session")
def auth_headers(client):
    response = client.post("/api/v1/auth/login", data={"username": "test@test.com", "password": "password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
