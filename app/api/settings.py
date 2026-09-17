from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User, Company
from app.api.deps import get_current_user
from pydantic import BaseModel

router = APIRouter()

class SettingsUpdate(BaseModel):
    currency: str | None = None
    tax_number: str | None = None
    industry: str | None = None

@router.get("")
def get_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = current_user.company
    return {
        "id": company.id,
        "name": company.name,
        "currency": company.currency,
        "tax_number": getattr(company, 'tax_number', None),
        "industry": getattr(company, 'industry', None)
    }

@router.patch("")
def update_settings(update_data: SettingsUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "CEO":
        raise HTTPException(status_code=403, detail="Only CEO can update settings")
        
    company = current_user.company
    
    if update_data.currency:
        company.currency = update_data.currency
    if update_data.tax_number is not None:
        if hasattr(company, 'tax_number'):
            company.tax_number = update_data.tax_number
    if update_data.industry is not None:
        if hasattr(company, 'industry'):
            company.industry = update_data.industry
            
    db.commit()
    db.refresh(company)
    
    return {
        "id": company.id,
        "name": company.name,
        "currency": company.currency,
        "tax_number": getattr(company, 'tax_number', None),
        "industry": getattr(company, 'industry', None)
    }
