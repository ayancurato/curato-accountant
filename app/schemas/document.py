from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class DocumentBase(BaseModel):
    file_name: str
    document_type: str = "purchase_invoice"

class DocumentOut(DocumentBase):
    id: UUID
    company_id: UUID
    file_size: int
    file_type: str
    status: str
    file_hash: str
    uploaded_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
