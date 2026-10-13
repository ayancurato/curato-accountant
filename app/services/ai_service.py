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

def convert_pdf_to_base64_images(file_path: str, max_images: int = 2) -> List[str]:
    """
    Converts key pages of a PDF file to a list of base64 encoded JPEG images.
    Groq Vision models support at most 3 images and have strict ITPM limits,
    so we strategically select up to max_images (default 2) pages with the highest financial relevance.
    """
    doc = fitz.open(file_path)
    total_pages = len(doc)
    
    if total_pages <= max_images:
        selected_pages = list(range(total_pages))
    else:
        # Page 0 (Page 1) almost always contains invoice title, vendor, buyer, invoice #, and dates
        selected_pages = [0]
        # From remaining pages, pick the page with the highest density of financial keywords (e.g. tax table or grand total)
        keywords = ["tax", "cgst", "sgst", "igst", "gst", "total", "amount", "summary", "hsn", "due", "balance", "payable"]
        best_page = 1
        best_score = -1
        
        for p in range(1, total_pages):
            txt = doc[p].get_text().lower()
            score = sum(txt.count(kw) for kw in keywords)
            if score > best_score:
                best_score = score
                best_page = p
                
        selected_pages.append(best_page)
        selected_pages = sorted(list(set(selected_pages)))
    
    base64_images = []
    for page_num in selected_pages:
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img_bytes = pix.tobytes("jpeg")
        base64_str = base64.b64encode(img_bytes).decode("utf-8")
        base64_images.append(f"data:image/jpeg;base64,{base64_str}")
        
    doc.close()
    return base64_images

def extract_pdf_text_summary(file_path: str) -> str:
    """Extracts text across all pages in the PDF to supplement vision images."""
    try:
        doc = fitz.open(file_path)
        snippets = []
        for i, page in enumerate(doc):
            t = page.get_text().strip()
            if t:
                snippets.append(f"--- Page {i + 1} ---\n{t}")
        doc.close()
        if not snippets:
            return ""
        full_text = "\n\n".join(snippets)
        if len(full_text) > 6000:
            full_text = full_text[:6000] + "\n...[truncated]..."
        return full_text
    except Exception:
        return ""

def extract_invoice_data(file_path: str, mime_type: str) -> AIProcessedTransaction:
    """Extracts structured invoice data using Groq Vision."""
    
    if settings.GROQ_API_KEY == "mock-api-key" or settings.GROQ_API_KEY is None:
        return mock_ai_response()
        
    prompt = """
    You are an expert financial AI assistant. Extract the requested invoice or income information from the uploaded document(s).
    Determine if this is an INCOME or EXPENSE transaction from the perspective of the company uploading the document.
    Read only the supplied document. Do not invent missing values.
    Do not infer tax values if they are not present unless mathematically derived from clearly stated invoice information.
    Preserve the currency.
    Extract GST/VAT separately. Identify CGST/SGST/IGST when explicitly shown. Identify VAT when explicitly shown.
    
    Explicitly search for Vendor GSTIN and Customer GSTIN. Look for keywords like "GSTIN", "GST No", "GST Identification Number", "Seller GSTIN", "Vendor GSTIN", "Buyer GSTIN", "Customer GSTIN". Do not hallucinate a GSTIN if it is genuinely absent. Distinguish carefully between vendor and customer GSTIN.
    
    Explicitly search for Due Date. Look for keywords like "Due Date", "Payment Due", "Pay By", "Payment Due Date". Do not hallucinate.
    
    Recommend one category exactly matching one from the following EXPENSE list if type is EXPENSE:
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
    
    If you cannot confidently classify the expense into one of these EXACT categories, return null for the category. Do NOT invent categories or assign an arbitrary one.
    
    Determine if the payment was made via Bank, Credit Card, UPI, Cash, or Other (payment_account).
    Determine if it is BUSINESS, PERSONAL, or MIXED (business_personal).
    Determine expense_type: OPERATING_EXPENSE, ASSET, or OTHER.
    Extract basic TDS tracking info if applicable.
    
    If you can determine confidence, return confidence values as a float between 0.0 and 1.0. If you cannot provide a reliable confidence score, return null. Do NOT fabricate confidence scores.
    Respond strictly in JSON format matching the requested schema.
    
    The JSON schema is:
    {schema}
    """
    
    prompt = prompt.format(schema=json.dumps(AIProcessedTransaction.model_json_schema(), indent=2))
    
    if mime_type == "application/pdf":
        text_summary = extract_pdf_text_summary(file_path)
        if text_summary:
            prompt += f"\n\n--- DOCUMENT TEXT ACROSS ALL PAGES ---\n{text_summary}"
    
    messages = [
        {
            "role": "system",
            "content": "You are an expert financial AI assistant. Respond strictly in JSON format."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        }
    ]
    
    if mime_type == "application/pdf":
        base64_images = convert_pdf_to_base64_images(file_path)
        for b64_img in base64_images:
            messages[1]["content"].append(
                {"type": "image_url", "image_url": {"url": b64_img}}
            )
    else:
        with open(file_path, "rb") as f:
            img_bytes = f.read()
        b64_str = base64.b64encode(img_bytes).decode("utf-8")
        messages[1]["content"].append(
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_str}"}}
        )

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        json_data = json.loads(content)
        return AIProcessedTransaction(**json_data)
        
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
