from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import User, Company
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash

def create_user(db: Session, user_in: UserCreate) -> User:
    # Check if user exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system."
        )

    # For simplicity, create company if it doesn't exist (since this is internal tool)
    company = db.query(Company).filter(Company.name == user_in.company_name).first()
    if not company:
        company = Company(
            name=user_in.company_name,
            country=user_in.country,
            currency=user_in.currency,
            tax_type=user_in.tax_type
        )
        db.add(company)
        db.flush()

    user = User(
        company_id=company.id,
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
