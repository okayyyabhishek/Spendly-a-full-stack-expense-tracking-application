"""Create budget alerts only at meaningful state changes to avoid notification spam."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.enums import NotificationKind, TransactionType
from app.models.notification import Notification
from app.models.transaction import Transaction
from app.services.analytics_service import money, month_bounds, percentage


def maybe_create_budget_alert(session: Session, user_id: int, expense_date: date) -> None:
    start, end = month_bounds(expense_date.year, expense_date.month)
    budgets = list(
        session.scalars(
            select(Budget).where(Budget.user_id == user_id, Budget.month == expense_date.month, Budget.year == expense_date.year)
        )
    )
    for budget in budgets:
        statement = select(Transaction.amount).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
        )
        if budget.category_id is not None:
            statement = statement.where(Transaction.category_id == budget.category_id)
        spent = sum((money(value) for value in session.scalars(statement)), Decimal("0.00"))
        used = percentage(spent, money(budget.amount))
        if used < 80:
            continue
        kind = NotificationKind.BUDGET_EXCEEDED if used > 100 else NotificationKind.BUDGET_WARNING
        scope = "Your overall" if budget.category_id is None else "A category"
        title = f"{scope} budget is {used}% used"
        recent_duplicate = session.scalar(
            select(Notification.id).where(
                Notification.user_id == user_id,
                Notification.kind == kind,
                Notification.title == title,
                Notification.created_at >= start,
            )
        )
        if recent_duplicate is None:
            session.add(
                Notification(
                    user_id=user_id,
                    kind=kind,
                    title=title,
                    body=f"You have spent ₹{spent:.2f} of your ₹{money(budget.amount):.2f} budget.",
                )
            )
