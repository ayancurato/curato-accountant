from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from decimal import Decimal
import urllib.request
import json

def get_usd_to_inr_rate() -> Decimal:
    try:
        url = 'https://open.er-api.com/v6/latest/USD'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return Decimal(str(data['rates']['INR']))
    except Exception as e:
        print(f"Failed to fetch exchange rate: {e}")
        return Decimal('95.91') # Fallback


from app.models import (
    Document, Category, Transaction, User, AuditLog
)
from app.schemas.ai import AIProcessedTransaction

def match_category(db: Session, company_id, category_name: str, type: str) -> Category:
    if not category_name:
        return None
    category = db.query(Category).filter(
        Category.company_id == company_id,
        Category.type == type,
        Category.name.ilike(category_name),
        Category.is_archived == False
    ).first()
    return category

def check_duplicate(db: Session, company_id, vendor_customer, invoice_number, total_amount, invoice_date, document_hash, exclude_tx_id=None):
    # Hash check (if already processed on another document)
    if document_hash:
        q = db.query(Document).filter(
            Document.company_id == company_id,
            Document.file_hash == document_hash,
            Document.status.in_(["PROCESSED", "NEEDS_REVIEW", "READY", "APPROVED"])
        )
        # If exclude_tx_id is set, it means we are revalidating. 
        # But wait, document hash check is on document, not tx. 
        doc_exists = q.first()
        if doc_exists and (not exclude_tx_id or doc_exists.id != db.query(Transaction).filter(Transaction.id == exclude_tx_id).first().document_id):
            return True

    if not vendor_customer or not invoice_number:
        return False
    
    # Simple duplicate detection based on vendor and invoice_number
    # FIXED: Added Date and Total Amount matching to explicitly follow CEO PRD rules.
    q1 = db.query(Transaction).filter(
        Transaction.company_id == company_id,
        Transaction.vendor_customer == vendor_customer,
        Transaction.invoice_number == invoice_number,
        Transaction.date == invoice_date,
        Transaction.total_amount == total_amount
    )
    if exclude_tx_id:
        q1 = q1.filter(Transaction.id != exclude_tx_id)
    if q1.first():
        return True

    return False
def validate_amounts(ai_data: AIProcessedTransaction) -> (str, list):
    warnings = []
    
    if ai_data.net_amount is None or ai_data.total_amount is None:
        warnings.append({"type": "MISSING_AMOUNTS", "message": "Net Amount or Total Amount missing."})
        return "INSUFFICIENT_DATA", warnings

    tax = ai_data.gst_amount or Decimal('0')
    calculated_total = ai_data.net_amount + tax

    diff = abs(calculated_total - ai_data.total_amount)
    
    if diff > Decimal('0.1'):
        warnings.append({
            "type": "TOTAL_MISMATCH",
            "severity": "HIGH",
            "message": f"Invoice total {ai_data.total_amount} does not match net {ai_data.net_amount} plus tax {tax}."
        })
        return "MISMATCH", warnings
    elif diff > Decimal('0') and diff <= Decimal('0.1'):
        return "ROUNDING_DIFFERENCE", warnings
        
    return "VALID", warnings

def log_audit(db: Session, company_id, user_id, entity_type, entity_id, action, field=None, old_value=None, new_value=None):
    log = AuditLog(
        company_id=company_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        field=field,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None
    )
    db.add(log)

def process_ai_result(db: Session, document: Document, ai_data: AIProcessedTransaction, user: User):
    anomalies = []
    
    # Category
    category = match_category(db, document.company_id, ai_data.category, ai_data.type)
    if not category:
        anomalies.append({"type": "UNKNOWN_CATEGORY", "message": f"Category '{ai_data.category}' not recognized."})

    # Deterministic GST calculation
    if not ai_data.gst_amount and any([ai_data.cgst, ai_data.sgst, ai_data.igst]):
        ai_data.gst_amount = (ai_data.cgst or Decimal('0')) + (ai_data.sgst or Decimal('0')) + (ai_data.igst or Decimal('0'))

    # Amounts Validation
    amounts_valid_status, amount_warnings = validate_amounts(ai_data)
    anomalies.extend(amount_warnings)

    if not ai_data.invoice_number:
        anomalies.append({"type": "MISSING_INVOICE_NUMBER", "message": "Invoice number missing."})

    # Duplicate check
    is_duplicate = False
    is_duplicate = check_duplicate(
        db, 
        document.company_id, 
        ai_data.vendor_customer, 
        ai_data.invoice_number, 
        ai_data.total_amount, 
        ai_data.invoice_date,
        document.file_hash
    )
    if is_duplicate:
        anomalies.append({"type": "DUPLICATE_TRANSACTION", "message": "A possible duplicate transaction already exists."})

    category_id = category.id if category else None
    
    if not category_id:
        anomalies.append({
            "type": "CATEGORY_MISSING", 
            "message": f"Could not determine category. Original suggestion: {ai_data.category}, Confidence: {ai_data.confidence}"
        })
        
    if ai_data.confidence is None:
        anomalies.append({
            "type": "CONFIDENCE_UNAVAILABLE",
            "message": "AI confidence score is missing."
        })

    # Independent Statuses
    # 1. Transaction Status
    tx_status = "NEEDS_REVIEW"

    # 2. Document Status
    if len(anomalies) == 0 and amounts_valid_status == "VALID" and not is_duplicate:
        doc_status = "READY"
    else:
        doc_status = "NEEDS_REVIEW"

    net_amount = ai_data.net_amount or Decimal('0')
    gst_amount = ai_data.gst_amount or Decimal('0')
    total_amount = ai_data.total_amount or Decimal('0')
    cgst = ai_data.cgst or Decimal('0')
    sgst = ai_data.sgst or Decimal('0')
    igst = ai_data.igst or Decimal('0')

    usd_amount = None
    exchange_rate = None

    if ai_data.currency == "USD":
        usd_amount = total_amount
        exchange_rate = get_usd_to_inr_rate()
        
        net_amount = net_amount * exchange_rate
        gst_amount = gst_amount * exchange_rate
        total_amount = total_amount * exchange_rate
        cgst = cgst * exchange_rate
        sgst = sgst * exchange_rate
        igst = igst * exchange_rate
        
        ai_data.currency = "INR"

    tx = Transaction(
        company_id=document.company_id,
        document_id=document.id,
        type=ai_data.type,
        date=ai_data.invoice_date,
        due_date=ai_data.due_date,
        vendor_customer=ai_data.vendor_customer,
        invoice_number=ai_data.invoice_number,
        category_id=category_id,
        net_amount=net_amount,
        gst_amount=gst_amount,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        gst_rate=ai_data.gst_rate,
        total_amount=total_amount,
        vendor_gstin=ai_data.vendor_gstin,
        customer_gstin=ai_data.customer_gstin,
        itc_eligible=ai_data.itc_eligible,
        payment_account=ai_data.payment_account,
        payment_status="UNPAID" if ai_data.type == "EXPENSE" else "OUTSTANDING",
        business_personal=ai_data.business_personal or "BUSINESS",
        expense_type=ai_data.expense_type,
        tds_applicable=ai_data.tds_applicable,
        tds_amount=ai_data.tds_amount or Decimal('0'),
        currency=ai_data.currency,
        usd_amount=usd_amount,
        exchange_rate=exchange_rate,
        anomalies=anomalies,
        status=tx_status
    )

    db.add(tx)
    db.flush()

    document.status = doc_status

    log_audit(db, document.company_id, user.id, "DOCUMENT", document.id, "AI_PROCESSED")
    log_audit(db, document.company_id, user.id, "TRANSACTION", tx.id, "TRANSACTION_CREATED")

    db.commit()
    db.refresh(tx)

    return tx, anomalies, is_duplicate, amounts_valid_status

def revalidate_transaction(db: Session, tx: Transaction, document: Document):
    anomalies = []
    
    if not tx.category_id:
        anomalies.append({'type': 'CATEGORY_MISSING', 'message': 'Category is required.'})
        
    if tx.net_amount is None or tx.total_amount is None:
        anomalies.append({'type': 'MISSING_AMOUNTS', 'message': 'Net Amount or Total Amount missing.'})
    else:
        tax = tx.gst_amount or Decimal('0')
        calculated_total = tx.net_amount + tax
        diff = abs(calculated_total - tx.total_amount)
        if diff > Decimal('0.1'):
            anomalies.append({
                'type': 'TOTAL_MISMATCH',
                'severity': 'HIGH',
                'message': f'Invoice total {tx.total_amount} does not match net {tx.net_amount} plus tax {tax}.'
            })
            
    if not tx.invoice_number:
        anomalies.append({'type': 'MISSING_INVOICE_NUMBER', 'message': 'Invoice number missing.'})
        
    is_duplicate = check_duplicate(
        db, 
        tx.company_id, 
        tx.vendor_customer, 
        tx.invoice_number, 
        tx.total_amount, 
        tx.date,
        document.file_hash if document else None,
        exclude_tx_id=tx.id
    )
    if is_duplicate:
        anomalies.append({'type': 'DUPLICATE_TRANSACTION', 'message': 'A possible duplicate transaction already exists.'})
        
    if tx.gst_amount and tx.gst_amount > 0:
        if tx.type == "INCOME" and not tx.customer_gstin:
            anomalies.append({'type': 'MISSING_GSTIN', 'message': 'GST is present but Customer GSTIN is missing.'})
        elif tx.type != "INCOME" and not tx.vendor_gstin:
            anomalies.append({'type': 'MISSING_GSTIN', 'message': 'GST is present but Vendor GSTIN is missing.'})
        
    return anomalies
