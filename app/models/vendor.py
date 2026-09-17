import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False, index=True)
    tax_number = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company")
