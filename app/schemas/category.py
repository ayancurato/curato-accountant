from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    type: str # INCOME or EXPENSE
    description: Optional[str] = None
    is_archived: bool = False

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    is_archived: Optional[bool] = None

class CategoryOut(CategoryBase):
    id: UUID
    company_id: UUID

    model_config = {"from_attributes": True}
