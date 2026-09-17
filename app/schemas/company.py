from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import Optional

class CompanyBase(BaseModel):
    name: str
    country: str
    currency: str
    tax_type: str
    financial_year_start: Optional[date] = None
    financial_year_end: Optional[date] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    tax_type: Optional[str] = None
    financial_year_start: Optional[date] = None
    financial_year_end: Optional[date] = None

class CompanyOut(CompanyBase):
    id: UUID

    model_config = {"from_attributes": True}
