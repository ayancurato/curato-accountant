import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models import Category, Company, User
from app.core.security import get_password_hash

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

def run_seed():
    db = SessionLocal()
    try:
        # Create default company
        company = db.query(Company).filter(Company.name == "Curato").first()
        if not company:
            company = Company(
                name="Curato",
                country="India",
                currency="INR",
                tax_type="GST"
            )
            db.add(company)
            db.flush()
            print("Created default company 'Curato'")

        # Create admin user
        user = db.query(User).filter(User.email == "sarath@curato.ai").first()
        if not user:
            user = User(
                company_id=company.id,
                name="Curato CEO",
                email="sarath@curato.ai",
                password_hash=get_password_hash("password@123"),
                role="CEO"
            )
            db.add(user)
            print("Created default CEO user (sarath@curato.ai / password@123)")

        # Seed categories
        existing_categories = db.query(Category.name).filter(Category.company_id == company.id, Category.type == "EXPENSE").all()
        existing_names = [c[0] for c in existing_categories]

        for cat_name in CATEGORIES:
            if cat_name not in existing_names:
                db.add(Category(company_id=company.id, name=cat_name, type="EXPENSE"))
                print(f"Added expense category: {cat_name}")

        existing_income_cats = db.query(Category.name).filter(Category.company_id == company.id, Category.type == "INCOME").all()
        existing_income_names = [c[0] for c in existing_income_cats]

        for cat_name in INCOME_CATEGORIES:
            if cat_name not in existing_income_names:
                db.add(Category(company_id=company.id, name=cat_name, type="INCOME"))
                print(f"Added income category: {cat_name}")

        db.commit()
        print("Seed completed successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
