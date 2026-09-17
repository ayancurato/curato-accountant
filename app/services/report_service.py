from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models import Transaction, Category
from decimal import Decimal
from datetime import date, timedelta
from calendar import monthrange

def resolve_date_preset(preset: str):
    today = date.today()
    date_from = None
    date_to = None
    
    if preset == "this_month":
        date_from = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        date_to = today.replace(day=last_day)
    elif preset == "this_quarter":
        # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
        quarter = (today.month - 1) // 3 + 1
        first_month = 3 * quarter - 2
        date_from = date(today.year, first_month, 1)
        last_month = first_month + 2
        last_day = monthrange(today.year, last_month)[1]
        date_to = date(today.year, last_month, last_day)
    elif preset == "financial_year":
        # April 1 to March 31
        if today.month >= 4:
            date_from = date(today.year, 4, 1)
            date_to = date(today.year + 1, 3, 31)
        else:
            date_from = date(today.year - 1, 4, 1)
            date_to = date(today.year, 3, 31)
            
    return date_from, date_to

def get_reports(db: Session, company_id, preset=None, date_from=None, date_to=None):
    if preset:
        p_from, p_to = resolve_date_preset(preset)
        date_from = p_from or date_from
        date_to = p_to or date_to

    base_query = db.query(Transaction).filter(
        Transaction.company_id == company_id,
        Transaction.status == "APPROVED"
    )

    if date_from:
        base_query = base_query.filter(Transaction.date >= date_from)
    if date_to:
        base_query = base_query.filter(Transaction.date <= date_to)

    # 1. Core Metrics
    # We do a single aggregation for all metrics
    metrics_query = db.query(
        func.coalesce(func.sum(case((Transaction.type == "INCOME", Transaction.total_amount), else_=0)), 0).label("total_income"),
        func.coalesce(func.sum(case((Transaction.type == "EXPENSE", Transaction.total_amount), else_=0)), 0).label("total_expenses"),
        func.coalesce(func.sum(case((Transaction.type == "INCOME", Transaction.gst_amount), else_=0)), 0).label("gst_collected"),
        func.coalesce(func.sum(case((Transaction.type == "EXPENSE", Transaction.gst_amount), else_=0)), 0).label("gst_paid"),
        func.coalesce(func.sum(case(((Transaction.type == "INCOME") & (Transaction.payment_status == "OUTSTANDING"), Transaction.total_amount), else_=0)), 0).label("outstanding_income"),
        func.coalesce(func.sum(case(((Transaction.type == "EXPENSE") & (Transaction.payment_status == "UNPAID"), Transaction.total_amount), else_=0)), 0).label("unpaid_expenses")
    ).filter(
        Transaction.company_id == company_id,
        Transaction.status == "APPROVED"
    )
    
    if date_from:
        metrics_query = metrics_query.filter(Transaction.date >= date_from)
    if date_to:
        metrics_query = metrics_query.filter(Transaction.date <= date_to)
        
    metrics_res = metrics_query.first()
    
    total_income = Decimal(metrics_res.total_income)
    total_expenses = Decimal(metrics_res.total_expenses)
    
    metrics_data = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net": total_income - total_expenses,
        "gst_collected": Decimal(metrics_res.gst_collected),
        "gst_paid": Decimal(metrics_res.gst_paid),
        "outstanding_income": Decimal(metrics_res.outstanding_income),
        "unpaid_expenses": Decimal(metrics_res.unpaid_expenses)
    }

    # Helper for group queries
    def get_group_query(type_filter, group_by_col):
        q = db.query(
            group_by_col,
            func.sum(Transaction.total_amount).label("amount")
        ).filter(
            Transaction.company_id == company_id,
            Transaction.status == "APPROVED",
            Transaction.type == type_filter
        )
        if date_from:
            q = q.filter(Transaction.date >= date_from)
        if date_to:
            q = q.filter(Transaction.date <= date_to)
        return q.group_by(group_by_col).order_by(func.sum(Transaction.total_amount).desc())

    # Expenses by Category
    exp_cat_q = get_group_query("EXPENSE", Transaction.category_id)
    exp_categories = []
    for cat_id, amount in exp_cat_q.all():
        cat = db.query(Category).get(cat_id) if cat_id else None
        cat_name = cat.name if cat else "Uncategorized"
        exp_categories.append({"category_name": cat_name, "amount": Decimal(amount)})

    # Expenses by Vendor
    exp_ven_q = get_group_query("EXPENSE", Transaction.vendor_customer)
    exp_vendors = []
    for vendor, amount in exp_ven_q.all():
        exp_vendors.append({"name": vendor or "Unknown", "amount": Decimal(amount)})

    # Income by Category
    inc_cat_q = get_group_query("INCOME", Transaction.category_id)
    inc_categories = []
    for cat_id, amount in inc_cat_q.all():
        cat = db.query(Category).get(cat_id) if cat_id else None
        cat_name = cat.name if cat else "Uncategorized"
        inc_categories.append({"category_name": cat_name, "amount": Decimal(amount)})

    # Income by Customer
    inc_cus_q = get_group_query("INCOME", Transaction.vendor_customer)
    inc_customers = []
    for cus, amount in inc_cus_q.all():
        inc_customers.append({"name": cus or "Unknown", "amount": Decimal(amount)})

    # Monthly Trends
    # We use SQLAlchemy's native cross-dialect func.extract() which works correctly on PostgreSQL (production) 
    # and SQLite (tests), safely extracting year and month without requiring string-specific hacks.
    def get_trend_query(type_filter):
        q = db.query(
            func.extract('year', Transaction.date).label("year"),
            func.extract('month', Transaction.date).label("month"),
            func.sum(Transaction.total_amount).label("amount")
        ).filter(
            Transaction.company_id == company_id,
            Transaction.status == "APPROVED",
            Transaction.type == type_filter,
            Transaction.date != None
        )
        if date_from:
            q = q.filter(Transaction.date >= date_from)
        if date_to:
            q = q.filter(Transaction.date <= date_to)
            
        return q.group_by(
            func.extract('year', Transaction.date),
            func.extract('month', Transaction.date)
        ).order_by(
            func.extract('year', Transaction.date).asc(),
            func.extract('month', Transaction.date).asc()
        )

    def format_month(y, m):
        return f"{int(y):04d}-{int(m):02d}"

    exp_trend_q = get_trend_query("EXPENSE")
    exp_trend = [{"month": format_month(y, m), "amount": Decimal(a)} for y, m, a in exp_trend_q.all()]

    inc_trend_q = get_trend_query("INCOME")
    inc_trend = [{"month": format_month(y, m), "amount": Decimal(a)} for y, m, a in inc_trend_q.all()]

    return {
        "period": {
            "date_from": date_from,
            "date_to": date_to,
            "preset": preset
        },
        "metrics": metrics_data,
        "expenses": {
            "by_category": exp_categories,
            "by_vendor": exp_vendors,
            "monthly_trend": exp_trend
        },
        "income": {
            "by_category": inc_categories,
            "by_customer": inc_customers,
            "monthly_trend": inc_trend
        }
    }
