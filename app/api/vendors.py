from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.models import User, Vendor
from app.api.deps import get_current_user
from app.schemas.vendor import VendorOut

router = APIRouter()

@router.get("", response_model=List[VendorOut])
def get_vendors(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Vendor).filter(Vendor.company_id == current_user.company_id).all()

@router.get("/{id}", response_model=VendorOut)
def get_vendor(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == id, Vendor.company_id == current_user.company_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor
