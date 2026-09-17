import uuid
from sqlalchemy import Column, String, DateTime, func, Date
from sqlalchemy import UUID
from app.core.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    tax_type = Column(String, nullable=False)
    financial_year_start = Column(Date, nullable=True)
    financial_year_end = Column(Date, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
