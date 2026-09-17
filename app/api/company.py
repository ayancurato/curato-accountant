from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.company import CompanyOut, CompanyUpdate
from app.models import User, Company
from app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=CompanyOut)
def get_company(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    return company

@router.patch("", response_model=CompanyOut)
def update_company(company_update: CompanyUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "CEO":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    
    update_data = company_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)
        
    db.commit()
    db.refresh(company)
    return company
