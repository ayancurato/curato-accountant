from sqlalchemy import Column, String, ForeignKey, Date, DateTime, Numeric, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    type = Column(String, nullable=False)  # INCOME, EXPENSE
    
    date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    vendor_customer = Column(String, nullable=True)
    invoice_number = Column(String, nullable=True)
    
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    category = relationship("Category")
    
    net_amount = Column(Numeric, nullable=False, default=0)
    gst_amount = Column(Numeric, nullable=False, default=0)
    cgst = Column(Numeric, nullable=False, default=0)
    sgst = Column(Numeric, nullable=False, default=0)
    igst = Column(Numeric, nullable=False, default=0)
    gst_rate = Column(Numeric, nullable=True)
    total_amount = Column(Numeric, nullable=False, default=0)
    
    vendor_gstin = Column(String, nullable=True)
    customer_gstin = Column(String, nullable=True)
    itc_eligible = Column(Boolean, nullable=True)
    itc_status = Column(String, nullable=True)
    
    payment_account = Column(String, nullable=True)  # Bank, Credit Card, UPI, Cash, Other
    payment_status = Column(String, nullable=True)   # PAID, UNPAID, RECEIVED, OUTSTANDING
    
    business_personal = Column(String, nullable=True) # BUSINESS, PERSONAL, MIXED
    expense_type = Column(String, nullable=True)      # OPERATING_EXPENSE, ASSET, OTHER
    
    tds_applicable = Column(Boolean, nullable=True)
    tds_amount = Column(Numeric, nullable=True, default=0)
    tds_deducted = Column(Boolean, nullable=True)
    tds_deposited = Column(Boolean, nullable=True)
    
    notes = Column(String, nullable=True)
    status = Column(String, nullable=False, default="DRAFT") # DRAFT, NEEDS_REVIEW, APPROVED
    
    currency = Column(String, nullable=True, default="INR")
    usd_amount = Column(Numeric, nullable=True)
    exchange_rate = Column(Numeric, nullable=True)
    anomalies = Column(JSON, nullable=True)
    
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    document = relationship("Document")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
