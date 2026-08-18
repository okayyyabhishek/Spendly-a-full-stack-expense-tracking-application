"""Materialize due recurring schedules into durable transactions."""

from calendar import monthrange
from datetime import date, timedelta

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction


def advance_due_date(current: date, frequency: str) -> date:
    if frequency == "daily":
        return current + timedelta(days=1)
    if frequency == "weekly":
        return current + timedelta(weeks=1)
    if frequency == "monthly":
        year = current.year + (current.month // 12)
        month = (current.month % 12) + 1
        return current.replace(year=year, month=month, day=min(current.day, monthrange(year, month)[1]))
    year = current.year + 1
    return current.replace(year=year, day=min(current.day, monthrange(year, current.month)[1]))


def process_due_transactions(session: Session, user_id: int | None = None, as_of: date | None = None) -> int:
    """Create every overdue occurrence once and advance the schedule atomically in the caller transaction."""
    today = as_of or date.today()
    statement: Select[tuple[RecurringTransaction]] = select(RecurringTransaction).where(
        RecurringTransaction.active.is_(True), RecurringTransaction.next_due_date <= today
    )
    if user_id is not None:
        statement = statement.where(RecurringTransaction.user_id == user_id)

    created = 0
    for recurring in session.scalars(statement.with_for_update()):
        while recurring.active and recurring.next_due_date <= today:
            if recurring.end_date is not None and recurring.next_due_date > recurring.end_date:
                recurring.active = False
                break
            session.add(
                Transaction(
                    user_id=recurring.user_id,
                    type=recurring.type,
                    amount=recurring.amount,
                    category_id=recurring.category_id,
                    description=recurring.description,
                    payment_method=recurring.payment_method,
                    transaction_date=recurring.next_due_date,
                    recurring_transaction_id=recurring.id,
                )
            )
            created += 1
            recurring.next_due_date = advance_due_date(recurring.next_due_date, recurring.frequency.value)
            if recurring.end_date is not None and recurring.next_due_date > recurring.end_date:
                recurring.active = False
    return created
