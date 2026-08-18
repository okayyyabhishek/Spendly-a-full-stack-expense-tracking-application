"""Database-backed financial metrics and report aggregation."""

from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.analytics import (
    BiggestTransaction,
    CategoryAnalysisItem,
    DashboardSummary,
    FinancialMetrics,
    MonthlySummary,
    TimeAnalysisItem,
)

ZERO = Decimal("0.00")


def money(value: Decimal | int | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def percentage(part: Decimal, total: Decimal) -> Decimal:
    if total == 0:
        return ZERO
    return (part / total * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def sum_transactions(
    session: Session, user_id: int, transaction_type: TransactionType, start: date | None = None, end: date | None = None
) -> Decimal:
    statement = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id, Transaction.type == transaction_type
    )
    if start is not None:
        statement = statement.where(Transaction.transaction_date >= start)
    if end is not None:
        statement = statement.where(Transaction.transaction_date <= end)
    return money(session.scalar(statement))


def category_analysis(
    session: Session, user_id: int, start: date | None = None, end: date | None = None
) -> list[CategoryAnalysisItem]:
    statement = (
        select(Category.id, Category.name, Category.color, func.coalesce(func.sum(Transaction.amount), 0).label("amount"))
        .join(Transaction, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id, Transaction.type == TransactionType.EXPENSE)
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.sum(Transaction.amount).desc())
    )
    if start:
        statement = statement.where(Transaction.transaction_date >= start)
    if end:
        statement = statement.where(Transaction.transaction_date <= end)
    rows = list(session.execute(statement))
    total = sum((money(row.amount) for row in rows), ZERO)
    return [
        CategoryAnalysisItem(
            category_id=row.id,
            category_name=row.name,
            color=row.color,
            amount=money(row.amount),
            percentage=percentage(money(row.amount), total),
        )
        for row in rows
    ]


def financial_metrics(session: Session, user_id: int) -> FinancialMetrics:
    income = sum_transactions(session, user_id, TransactionType.INCOME)
    expenses = sum_transactions(session, user_id, TransactionType.EXPENSE)
    first_expense, last_expense = session.execute(
        select(func.min(Transaction.transaction_date), func.max(Transaction.transaction_date)).where(
            Transaction.user_id == user_id, Transaction.type == TransactionType.EXPENSE
        )
    ).one()
    if first_expense and last_expense:
        days = max((last_expense - first_expense).days + 1, 1)
        months = max((last_expense.year - first_expense.year) * 12 + last_expense.month - first_expense.month + 1, 1)
    else:
        days, months = 1, 1
    categories = category_analysis(session, user_id)
    highest_expense = money(
        session.scalar(
            select(func.coalesce(func.max(Transaction.amount), 0)).where(
                Transaction.user_id == user_id, Transaction.type == TransactionType.EXPENSE
            )
        )
    )
    return FinancialMetrics(
        total_income=income,
        total_expenses=expenses,
        net_balance=income - expenses,
        average_daily_spending=(expenses / days).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        average_monthly_spending=(expenses / months).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        highest_spending_category=categories[0].category_name if categories else None,
        highest_individual_expense=highest_expense,
        savings_rate=percentage(income - expenses, income),
    )


def dashboard_summary(session: Session, user_id: int, month: int, year: int) -> DashboardSummary:
    start, end = month_bounds(year, month)
    total_income = sum_transactions(session, user_id, TransactionType.INCOME)
    total_expenses = sum_transactions(session, user_id, TransactionType.EXPENSE)
    monthly_income = sum_transactions(session, user_id, TransactionType.INCOME, start, end)
    monthly_expenses = sum_transactions(session, user_id, TransactionType.EXPENSE, start, end)
    overall_budget = session.scalar(
        select(Budget).where(
            Budget.user_id == user_id, Budget.category_id.is_(None), Budget.month == month, Budget.year == year
        )
    )
    monthly_budget = money(overall_budget.amount) if overall_budget else None
    return DashboardSummary(
        total_balance=total_income - total_expenses,
        total_income=total_income,
        total_expenses=total_expenses,
        current_month_spending=monthly_expenses,
        remaining_monthly_budget=monthly_budget - monthly_expenses if monthly_budget is not None else None,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_savings=monthly_income - monthly_expenses,
        budget_utilization=percentage(monthly_expenses, monthly_budget) if monthly_budget is not None else None,
    )


def monthly_timeseries(session: Session, user_id: int, months: int, end_year: int, end_month: int) -> list[TimeAnalysisItem]:
    periods: list[tuple[int, int]] = []
    year, month = end_year, end_month
    for _ in range(months):
        periods.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    points: list[TimeAnalysisItem] = []
    for year, month in reversed(periods):
        start, end = month_bounds(year, month)
        income = sum_transactions(session, user_id, TransactionType.INCOME, start, end)
        expenses = sum_transactions(session, user_id, TransactionType.EXPENSE, start, end)
        points.append(TimeAnalysisItem(period=f"{year}-{month:02d}", income=income, expenses=expenses, net=income - expenses))
    return points


def monthly_summary(session: Session, user_id: int, month: int, year: int) -> MonthlySummary:
    start, end = month_bounds(year, month)
    previous_year, previous_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prior_start, prior_end = month_bounds(previous_year, previous_month)
    income = sum_transactions(session, user_id, TransactionType.INCOME, start, end)
    expenses = sum_transactions(session, user_id, TransactionType.EXPENSE, start, end)
    prior_expenses = sum_transactions(session, user_id, TransactionType.EXPENSE, prior_start, prior_end)
    overall_budget = session.scalar(
        select(Budget).where(
            Budget.user_id == user_id, Budget.category_id.is_(None), Budget.month == month, Budget.year == year
        )
    )
    top_categories = category_analysis(session, user_id, start, end)[:5]
    biggest_rows = list(
        session.execute(
            select(Transaction, Category.name)
            .join(Category)
            .where(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            )
            .order_by(Transaction.amount.desc())
            .limit(5)
        )
    )
    change = percentage(expenses - prior_expenses, prior_expenses) if prior_expenses else None
    return MonthlySummary(
        month=month,
        year=year,
        total_income=income,
        total_expenses=expenses,
        savings=income - expenses,
        budget_utilization=percentage(expenses, money(overall_budget.amount)) if overall_budget else None,
        spending_change_percent=change,
        top_categories=top_categories,
        biggest_transactions=[
            BiggestTransaction(
                id=transaction.id,
                description=transaction.description,
                category_name=category_name,
                amount=money(transaction.amount),
                transaction_date=transaction.transaction_date,
            )
            for transaction, category_name in biggest_rows
        ],
    )
