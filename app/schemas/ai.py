from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
import datetime as dt
from decimal import Decimal

class AIProcessedTransaction(BaseModel):
    document_type: str  # e.g., purchase_invoice, sales_invoice, receipt
    type: str  # INCOME or EXPENSE
    vendor_customer: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[dt.date] = None
    due_date: Optional[dt.date] = None
    currency: str = "INR"
    
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
    
    payment_account: Optional[str] = None # Bank, Credit Card, UPI, Cash, Other
    business_personal: Optional[str] = None # BUSINESS, PERSONAL, MIXED
    expense_type: Optional[str] = None # OPERATING_EXPENSE, ASSET, OTHER
    
    tds_applicable: Optional[bool] = None
    tds_amount: Decimal = Decimal('0')
    
    category: Optional[str] = None
    confidence: Optional[float] = None

class ProcessedInvoiceResponse(BaseModel):
    document_id: str
    transaction_id: str
    document_status: str
    transaction_status: str
    vendor_customer: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[dt.date] = None
    currency: str
    category: Optional[dict] = None
    amounts: dict
    tax: dict
    payment_status: Optional[str] = None
    validation: dict
    possible_duplicate: bool
    anomalies: List[dict]
