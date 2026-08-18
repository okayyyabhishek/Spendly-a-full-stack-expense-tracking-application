from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class CategoryAnalysisItem(BaseModel):
    category_id: int
    category_name: str
    color: str | None
    amount: Decimal
    percentage: Decimal


class TimeAnalysisItem(BaseModel):
    period: str
    income: Decimal
    expenses: Decimal
    net: Decimal


class FinancialMetrics(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    average_daily_spending: Decimal
    average_monthly_spending: Decimal
    highest_spending_category: str | None
    highest_individual_expense: Decimal
    savings_rate: Decimal


class DashboardSummary(BaseModel):
    total_balance: Decimal
    total_income: Decimal
    total_expenses: Decimal
    current_month_spending: Decimal
    remaining_monthly_budget: Decimal | None
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_savings: Decimal
    budget_utilization: Decimal | None


class BiggestTransaction(BaseModel):
    id: int
    description: str | None
    category_name: str
    amount: Decimal
    transaction_date: date


class MonthlySummary(BaseModel):
    month: int
    year: int
    total_income: Decimal
    total_expenses: Decimal
    savings: Decimal
    budget_utilization: Decimal | None
    spending_change_percent: Decimal | None
    top_categories: list[CategoryAnalysisItem]
    biggest_transactions: list[BiggestTransaction]
