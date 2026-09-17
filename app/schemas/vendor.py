from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class VendorBase(BaseModel):
    name: str
    tax_number: Optional[str] = None
    country: Optional[str] = None

class VendorOut(VendorBase):
    id: UUID
    company_id: UUID
    normalized_name: str

    model_config = {"from_attributes": True}
