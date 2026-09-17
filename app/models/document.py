import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    document_type = Column(String, nullable=False, default="purchase_invoice")
    status = Column(String, nullable=False, default="UPLOADED") # UPLOADED, PROCESSING, PROCESSED, NEEDS_REVIEW, APPROVED, REJECTED, FAILED
    file_hash = Column(String, nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company")
    uploader = relationship("User")
