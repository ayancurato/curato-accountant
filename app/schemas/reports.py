from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
from datetime import date

class Period(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    preset: Optional[str] = None

class Metrics(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal
    gst_collected: Decimal
    gst_paid: Decimal
    outstanding_income: Decimal
    unpaid_expenses: Decimal

class CategoryBreakdown(BaseModel):
    category_name: str
    amount: Decimal

class CounterpartyBreakdown(BaseModel):
    name: str # vendor or customer
    amount: Decimal

class MonthlyTrend(BaseModel):
    month: str # e.g. "2026-04" or "April 2026"
    amount: Decimal

class ExpenseAnalysis(BaseModel):
    by_category: List[CategoryBreakdown]
    by_vendor: List[CounterpartyBreakdown]
    monthly_trend: List[MonthlyTrend]

class IncomeAnalysis(BaseModel):
    by_customer: List[CounterpartyBreakdown]
    by_category: List[CategoryBreakdown]
    monthly_trend: List[MonthlyTrend]

class TransactionReport(BaseModel):
    period: Period
    metrics: Metrics
    expenses: ExpenseAnalysis
    income: IncomeAnalysis
