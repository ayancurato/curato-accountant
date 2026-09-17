from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
import io
import csv
import zipfile
import os
import openpyxl

from app.core.database import get_db
from app.models import User, Transaction
from app.api.deps import get_current_user
from app.services.report_service import get_reports, resolve_date_preset

router = APIRouter()

def get_base_tx_query(db, company_id, start_date, end_date):
    query = db.query(Transaction).filter(Transaction.company_id == company_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    return query

def has_anomaly_type(tx, anomaly_types: List[str]):
    if not tx.anomalies:
        return False
    return any(a.get("type") in anomaly_types for a in tx.anomalies)

@router.get("/readiness")
def ca_readiness(
    preset: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if preset and preset != "custom":
        start_date, end_date = resolve_date_preset(preset)
        
    query = get_base_tx_query(db, current_user.company_id, start_date, end_date)
    txs = query.all()
    
    missing_docs = []
    needs_review = []
    duplicates = []
    gst_issues = []
    
    for t in txs:
        if t.document_id is None:
            missing_docs.append(t)
        if t.status == "NEEDS_REVIEW":
            needs_review.append(t)
        if has_anomaly_type(t, ["DUPLICATE_TRANSACTION"]):
            duplicates.append(t)
        if has_anomaly_type(t, ["MISSING_GSTIN", "TOTAL_MISMATCH"]):
            gst_issues.append(t)
            
    def map_tx(t):
        return {
            "id": str(t.id),
            "date": str(t.date) if t.date else None,
            "type": t.type,
            "vendor_customer": t.vendor_customer or "Unknown",
            "total_amount": float(t.total_amount)
        }
            
    return {
        "transaction_count": len(txs),
        "needs_review_count": len(needs_review),
        "missing_documents_count": len(missing_docs),
        "potential_duplicates_count": len(duplicates),
        "gst_issues_count": len(gst_issues),
        "needs_review": [map_tx(t) for t in needs_review],
        "missing_documents": [map_tx(t) for t in missing_docs],
        "potential_duplicates": [map_tx(t) for t in duplicates],
        "gst_issues": [map_tx(t) for t in gst_issues]
    }

def create_csv_buffer(headers, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode('utf-8')

@router.get("/export")
def export_ca_pack(
    preset: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if preset and preset != "custom":
        start_date, end_date = resolve_date_preset(preset)
        
    txs = get_base_tx_query(db, current_user.company_id, start_date, end_date).all()
    approved_txs = [t for t in txs if t.status == "APPROVED"]
    
    # Reports Aggregation
    reports = get_reports(db, current_user.company_id, preset=preset, date_from=start_date, date_to=end_date)
    
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    
    def add_sheet(title, headers, rows):
        ws = wb.create_sheet(title=title)
        ws.append(headers)
        for r in rows:
            ws.append(r)
            
    # 1. Income Ledger
    add_sheet("Income Ledger", 
        ["ID", "Date", "Customer", "Invoice Number", "Category", "Net Amount", "GST Amount", "Total Amount"],
        [[str(t.id), str(t.date), t.vendor_customer, t.invoice_number, t.category.name if t.category else "", float(t.net_amount), float(t.gst_amount), float(t.total_amount)] for t in approved_txs if t.type == "INCOME"]
    )
    
    # 2. Expense Ledger
    add_sheet("Expense Ledger",
        ["ID", "Date", "Vendor", "Invoice Number", "Category", "Net Amount", "GST Amount", "Total Amount"],
        [[str(t.id), str(t.date), t.vendor_customer, t.invoice_number, t.category.name if t.category else "", float(t.net_amount), float(t.gst_amount), float(t.total_amount)] for t in approved_txs if t.type == "EXPENSE"]
    )
    
    # 3. Asset Transactions
    add_sheet("Asset Transactions",
        ["ID", "Date", "Vendor", "Invoice Number", "Category", "Total Amount"],
        [[str(t.id), str(t.date), t.vendor_customer, t.invoice_number, t.category.name if t.category else "", float(t.total_amount)] for t in approved_txs if t.type == "EXPENSE" and t.expense_type == "ASSET"]
    )
    
    # 4. Category-wise Expenses
    add_sheet("Category-wise Expenses", ["Category", "Amount"], [[c["category_name"], float(c["amount"])] for c in reports["expenses"]["by_category"]])
    
    # 5. Vendor-wise Expenses
    add_sheet("Vendor-wise Expenses", ["Vendor", "Amount"], [[c["name"], float(c["amount"])] for c in reports["expenses"]["by_vendor"]])
    
    # 6. Customer-wise Income
    add_sheet("Customer-wise Income", ["Customer", "Amount"], [[c["name"], float(c["amount"])] for c in reports["income"]["by_customer"]])
    
    # 7. Monthly Summary
    add_sheet("Monthly Summary", ["Metric", "Amount"], [[k, float(v)] for k, v in reports["metrics"].items()])
    
    # 8. GST Summary
    add_sheet("GST Summary", 
        ["ID", "Type", "Date", "Vendor/Customer", "Net", "CGST", "SGST", "IGST", "Total GST", "GST Rate", "Vendor GSTIN", "Customer GSTIN", "ITC Status"],
        [[str(t.id), t.type, str(t.date), t.vendor_customer, float(t.net_amount), float(t.cgst), float(t.sgst), float(t.igst), float(t.gst_amount), float(t.gst_rate) if t.gst_rate else 0, t.vendor_gstin, t.customer_gstin, t.itc_status] for t in approved_txs]
    )
    
    # 9. TDS Summary
    add_sheet("TDS Summary", 
        ["ID", "Type", "Date", "Vendor/Customer", "TDS Applicable", "TDS Amount", "TDS Deducted", "TDS Deposited", "Notes"],
        [[str(t.id), t.type, str(t.date), t.vendor_customer, str(t.tds_applicable), float(t.tds_amount) if t.tds_amount else 0, str(t.tds_deducted), str(t.tds_deposited), t.notes] for t in approved_txs if t.tds_applicable]
    )
    
    # 10. Complete Transaction Ledger
    add_sheet("Complete Ledger", 
        ["ID", "Type", "Status", "Date", "Vendor/Customer", "Invoice Number", "Category", "Net Amount", "GST Amount", "Total Amount"],
        [[str(t.id), t.type, t.status, str(t.date), t.vendor_customer, t.invoice_number, t.category.name if t.category else "", float(t.net_amount), float(t.gst_amount), float(t.total_amount)] for t in approved_txs]
    )

    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('CA_Pack.xlsx', excel_buffer.getvalue())
        
        # Exception Reports (Include ALL txs)
        missing_docs = [t for t in txs if t.document_id is None]
        needs_review = [t for t in txs if t.status == "NEEDS_REVIEW"]
        duplicates = [t for t in txs if has_anomaly_type(t, ["DUPLICATE_TRANSACTION"])]
        gst_issues = [t for t in txs if has_anomaly_type(t, ["MISSING_GSTIN", "TOTAL_MISMATCH"])]
        other_flagged = [t for t in txs if t.anomalies and not has_anomaly_type(t, ["DUPLICATE_TRANSACTION", "MISSING_GSTIN", "TOTAL_MISMATCH"])]
        
        exc_headers = ["ID", "Status", "Type", "Date", "Vendor/Customer", "Total Amount"]
        def tx_rows(tx_list):
            return [[str(t.id), t.status, t.type, str(t.date), t.vendor_customer, str(t.total_amount)] for t in tx_list]
            
        zf.writestr('exceptions/missing_documents.csv', create_csv_buffer(exc_headers, tx_rows(missing_docs)))
        zf.writestr('exceptions/needs_review.csv', create_csv_buffer(exc_headers, tx_rows(needs_review)))
        zf.writestr('exceptions/duplicates.csv', create_csv_buffer(exc_headers, tx_rows(duplicates)))
        zf.writestr('exceptions/gst_issues.csv', create_csv_buffer(exc_headers, tx_rows(gst_issues)))
        zf.writestr('exceptions/other_flagged.csv', create_csv_buffer(exc_headers, tx_rows(other_flagged)))
        
        # Original Documents
        for t in txs:
            if t.document_id and t.document.file_path and os.path.exists(t.document.file_path):
                ext = os.path.splitext(t.document.file_name)[1]
                short_id = str(t.id)[:8]
                filename = f"docs/{t.type}_{t.date}_{t.vendor_customer}_{short_id}{ext}"
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '/', '-'))
                zf.write(t.document.file_path, filename)
                
    zip_buffer.seek(0)
    filename = f"CA_Pack_{start_date or 'ALL'}_to_{end_date or 'ALL'}.zip"
    
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
