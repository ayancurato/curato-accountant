import os
import json
import base64
from typing import Optional, List
from datetime import date
from decimal import Decimal
import fitz  # PyMuPDF
from groq import Groq

from app.core.config import settings
from app.schemas.ai import AIProcessedTransaction

# Groq client initialization
if settings.GROQ_API_KEY != "mock-api-key" and settings.GROQ_API_KEY is not None:
    client = Groq(api_key=settings.GROQ_API_KEY)
else:
    client = None

COMPACT_SCHEMA_TEMPLATE = """{
  "document_type": "purchase_invoice",
  "type": "EXPENSE",
  "vendor_customer": "Vendor Name",
  "invoice_number": "INV-12345",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "currency": "INR",
  "net_amount": 0.0,
  "gst_amount": 0.0,
  "cgst": 0.0,
  "sgst": 0.0,
  "igst": 0.0,
  "gst_rate": 0.0,
  "total_amount": 0.0,
  "vendor_gstin": "string",
  "customer_gstin": "string",
  "itc_eligible": true,
  "payment_account": "Bank",
  "business_personal": "BUSINESS",
  "expense_type": "OPERATING_EXPENSE",
  "tds_applicable": false,
  "tds_amount": 0.0,
  "category": "Telecom & Internet",
  "confidence": 0.95
}"""

EXTRACTION_RULES = f"""You are an expert financial AI assistant. Extract financial transaction data strictly in valid JSON format matching the schema.

RULES:
1. Determine if this is an INCOME or EXPENSE transaction from the perspective of the company uploading the document (e.g. if the company is the recipient/buyer/billed customer, it is EXPENSE; if the company is the seller/vendor/issuer, it is INCOME).
2. 'vendor_customer' must be a single string containing the primary counterparty name.
3. Preserve currency (default INR).
4. Extract GST/VAT separately: cgst, sgst, igst, and total gst_amount as numbers.
5. Extract vendor_gstin and customer_gstin if present. Distinguish carefully between seller/vendor and buyer/customer GSTINs.
6. Extract invoice_date and due_date in YYYY-MM-DD format (or null).
7. Category must strictly be one of:
- Legal, Compliance & Government Fees
- Software, AI & SaaS
- Salaries & Intern Stipends
- Freelancers & Professional Services
- Marketing & Advertising
- Office Supplies, Equipment & Furniture
- Travel, Meals & Entertainment
- Telecom & Internet
- Rent & Utilities
- Banking, Payment & Other Business Charges
(or null if none fit).
8. payment_account: 'Bank', 'Credit Card', 'UPI', 'Cash', or 'Other'.
9. business_personal: 'BUSINESS', 'PERSONAL', or 'MIXED'.
10. expense_type: 'OPERATING_EXPENSE', 'ASSET', or 'OTHER'.

Schema to follow:
{COMPACT_SCHEMA_TEMPLATE}"""

def extract_pdf_digital_text(file_path: str, max_chars: int = 3500) -> str:
    """Extracts digital text from key pages of a PDF to avoid heavy vision tokens."""
    try:
        doc = fitz.open(file_path)
        snippets = []
        for i in range(min(3, len(doc))):
            t = doc[i].get_text().strip()
            if t:
                snippets.append(f"--- Page {i + 1} ---\n{t}")
        doc.close()
        combined = "\n\n".join(snippets)
        return combined[:max_chars]
    except Exception:
        return ""

def convert_pdf_first_page_to_base64(file_path: str) -> str:
    """Renders ONLY the first page of a PDF at an optimized scale to strictly preserve ITPM token limits."""
    doc = fitz.open(file_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
    img_bytes = pix.tobytes("jpeg")
    doc.close()
    return base64.b64encode(img_bytes).decode("utf-8")

def normalize_ai_dict(data: dict) -> dict:
    """Sanitizes LLM outputs so Pydantic validation never breaks on unexpected formatting."""
    # 1. vendor_customer
    vc = data.get("vendor_customer")
    if isinstance(vc, dict):
        data["vendor_customer"] = vc.get("name") or vc.get("vendor") or vc.get("customer") or str(vc)
    
    # 2. category
    cat = data.get("category")
    if isinstance(cat, dict):
        data["category"] = cat.get("name") or str(cat)
        
    # 3. gst_rate
    gr = data.get("gst_rate")
    if isinstance(gr, str):
        cleaned = gr.replace("%", "").strip()
        try:
            data["gst_rate"] = float(cleaned)
        except ValueError:
            data["gst_rate"] = None
            
    # 4. payment_account
    pa = data.get("payment_account")
    if isinstance(pa, dict):
        data["payment_account"] = pa.get("type") or pa.get("bank_name") or "Bank"
    valid_accounts = ["Bank", "Credit Card", "UPI", "Cash", "Other"]
    if pa and str(pa) not in valid_accounts:
        matched = next((a for a in valid_accounts if a.lower() in str(pa).lower()), "Other")
        data["payment_account"] = matched
        
    # 5. business_personal
    bp = data.get("business_personal")
    if bp and str(bp).upper() in ["BUSINESS", "PERSONAL", "MIXED"]:
        data["business_personal"] = str(bp).upper()
        
    # 6. expense_type
    et = data.get("expense_type")
    if et and str(et).upper() in ["OPERATING_EXPENSE", "ASSET", "OTHER"]:
        data["expense_type"] = str(et).upper()
        
    # 7. type
    t = data.get("type")
    if t and "EXPENSE" in str(t).upper():
        data["type"] = "EXPENSE"
    elif t and "INCOME" in str(t).upper():
        data["type"] = "INCOME"
        
    return data

def extract_invoice_data(file_path: str, mime_type: str) -> AIProcessedTransaction:
    """
    Extracts structured invoice data using Groq AI.
    Optimized for Groq's 7,000 ITPM limit:
    - For PDFs with digital text: uses zero-image fast text mode (~1,700 tokens, 0.7s latency).
    - For scanned PDFs or direct images: uses 1 single optimized image (~2,200 tokens).
    """
    if settings.GROQ_API_KEY == "mock-api-key" or settings.GROQ_API_KEY is None:
        return mock_ai_response()
        
    digital_text = ""
    if mime_type == "application/pdf":
        digital_text = extract_pdf_digital_text(file_path)
        
    use_text_mode = len(digital_text.strip()) >= 80

    messages = [
        {
            "role": "system",
            "content": "You are an expert financial AI assistant. Respond strictly in valid JSON format."
        }
    ]
    
    if use_text_mode:
        prompt = f"{EXTRACTION_RULES}\n\nDOCUMENT TEXT:\n{digital_text}"
        messages.append({
            "role": "user",
            "content": prompt
        })
    else:
        # Vision mode with exactly 1 image
        prompt = f"{EXTRACTION_RULES}\n\nInspect the attached invoice document and extract all fields."
        if mime_type == "application/pdf":
            b64_str = convert_pdf_first_page_to_base64(file_path)
            image_url = f"data:image/jpeg;base64,{b64_str}"
        else:
            with open(file_path, "rb") as f:
                img_bytes = f.read()
            b64_str = base64.b64encode(img_bytes).decode("utf-8")
            image_url = f"data:{mime_type};base64,{b64_str}"
            
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        })

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=600
        )
        
        content = response.choices[0].message.content
        json_data = json.loads(content)
        normalized = normalize_ai_dict(json_data)
        return AIProcessedTransaction(**normalized)
        
    except Exception as e:
        print(f"AI Extraction failed: {e}")
        raise Exception(f"AI Error: {str(e)}")

def mock_ai_response() -> AIProcessedTransaction:
    # Used for automated testing
    return AIProcessedTransaction(
        document_type="purchase_invoice",
        type="EXPENSE",
        vendor_customer="AWS",
        invoice_number="INV-12345",
        invoice_date=date(2026, 9, 15),
        due_date=date(2026, 10, 15),
        currency="INR",
        net_amount=Decimal("100000"),
        gst_amount=Decimal("18000"),
        cgst=Decimal("9000"),
        sgst=Decimal("9000"),
        igst=Decimal("0"),
        gst_rate=Decimal("18"),
        total_amount=Decimal("118000"),
        vendor_gstin="27AADCB2230M1Z2",
        itc_eligible=True,
        payment_account="Credit Card",
        business_personal="BUSINESS",
        expense_type="OPERATING_EXPENSE",
        tds_applicable=False,
        tds_amount=Decimal("0"),
        category="Software, AI & SaaS",
        confidence=0.97
    )

def mock_ai_response_uncertain() -> AIProcessedTransaction:
    # Used for automated testing
    return AIProcessedTransaction(
        document_type="receipt",
        type="EXPENSE",
        vendor_customer="Unknown Cafe",
        currency="INR",
        net_amount=Decimal("500"),
        gst_amount=Decimal("25"),
        cgst=Decimal("12.5"),
        sgst=Decimal("12.5"),
        igst=Decimal("0"),
        gst_rate=Decimal("5"),
        total_amount=Decimal("525"),
        payment_account="Cash",
        business_personal="BUSINESS",
        expense_type="OPERATING_EXPENSE",
        category=None,
        confidence=0.4
    )
