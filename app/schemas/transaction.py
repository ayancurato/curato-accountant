from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
import datetime as dt
from typing import Optional
from decimal import Decimal

class TransactionBase(BaseModel):
    type: str
    date: Optional[dt.date] = None
    due_date: Optional[dt.date] = None
    vendor_customer: Optional[str] = None
    invoice_number: Optional[str] = None
    category_id: Optional[UUID] = None
    currency: Optional[str] = "INR"
    usd_amount: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    
    net_amount: Decimal = Decimal('0')
    gst_amount: Decimal = Decimal('0')
    cgst: Decimal = Decimal('0')
    sgst: Decimal = Decimal('0')
    igst: Decimal = Decimal('0')
    gst_rate: Optional[Decimal] = None
    total_amount: Decimal = Decimal('0')
    
    vendor_gstin: Optional[str] = None
    customer_gstin: Optional[str] = None
    itc_eligible: Optional[bool] = None
    itc_status: Optional[str] = None
    
    payment_account: Optional[str] = None
    payment_status: Optional[str] = None
    
    business_personal: Optional[str] = None
    expense_type: Optional[str] = None
    
    tds_applicable: Optional[bool] = None
    tds_amount: Optional[Decimal] = Decimal('0')
    tds_deducted: Optional[bool] = None
    tds_deposited: Optional[bool] = None
    
    notes: Optional[str] = None
    status: str = "DRAFT"

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    document_id: Optional[UUID] = None
    date: Optional[dt.date] = None
    due_date: Optional[dt.date] = None
    vendor_customer: Optional[str] = None
    invoice_number: Optional[str] = None
    category_id: Optional[UUID] = None
    currency: Optional[str] = None
    usd_amount: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    
    net_amount: Optional[Decimal] = None
    gst_amount: Optional[Decimal] = None
    cgst: Optional[Decimal] = None
    sgst: Optional[Decimal] = None
    igst: Optional[Decimal] = None
    gst_rate: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    
    vendor_gstin: Optional[str] = None
    customer_gstin: Optional[str] = None
    itc_eligible: Optional[bool] = None
    itc_status: Optional[str] = None
    
    payment_account: Optional[str] = None
    payment_status: Optional[str] = None
    
    business_personal: Optional[str] = None
    expense_type: Optional[str] = None
    
    tds_applicable: Optional[bool] = None
    tds_amount: Optional[Decimal] = None
    tds_deducted: Optional[bool] = None
    tds_deposited: Optional[bool] = None
    
    notes: Optional[str] = None
    status: Optional[str] = None

class TransactionOut(TransactionBase):
    id: UUID
    company_id: UUID
    document_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    anomalies: Optional[list[dict]] = None

    model_config = ConfigDict(from_attributes=True)
