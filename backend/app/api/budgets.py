"""Monthly overall and category-specific budget endpoints."""

from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.budget import Budget
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate
from app.schemas.category import CategoryResponse
from app.services.ledger_service import get_owned_category
from app.services.recurring_service import process_due_transactions

router = APIRouter(prefix="/budgets", tags=["budgets"])


def _period_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def _as_decimal(value: Decimal | int | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _serialize_budget(session: Session, budget: Budget) -> BudgetResponse:
    start, end = _period_bounds(budget.year, budget.month)
    statement = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == budget.user_id,
        Transaction.type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start,
        Transaction.transaction_date <= end,
    )
    if budget.category_id is not None:
        statement = statement.where(Transaction.category_id == budget.category_id)
    spent = _as_decimal(session.scalar(statement))
    amount = _as_decimal(budget.amount)
    remaining = amount - spent
    percent = (spent / amount * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    state = "exceeded" if percent > 100 else "warning" if percent >= 80 else "on_track"
    return BudgetResponse(
        id=budget.id,
        amount=amount,
        month=budget.month,
        year=budget.year,
        category=CategoryResponse.model_validate(budget.category) if budget.category else None,
        spent=spent,
        remaining=remaining,
        percent_used=percent,
        status=state,
        created_at=budget.created_at,
    )


def _owned_budget(session: Session, user_id: int, budget_id: int) -> Budget:
    budget = session.scalar(
        select(Budget).options(selectinload(Budget.category)).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    return budget


@router.get("", response_model=list[BudgetResponse], summary="List budgets and their live spending progress")
def list_budgets(
    month: int | None = None,
    year: int | None = None,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BudgetResponse]:
    today = date.today()
    selected_month, selected_year = month or today.month, year or today.year
    if not 1 <= selected_month <= 12 or not 2000 <= selected_year <= 2100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose a valid budget month and year.")
    process_due_transactions(session, current_user.id)
    session.commit()
    budgets = list(
        session.scalars(
            select(Budget)
            .options(selectinload(Budget.category))
            .where(Budget.user_id == current_user.id, Budget.month == selected_month, Budget.year == selected_year)
            .order_by(Budget.category_id.is_(None).desc(), Budget.created_at)
        )
    )
    return [_serialize_budget(session, budget) for budget in budgets]


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED, summary="Create a monthly budget")
def create_budget(
    payload: BudgetCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    if payload.category_id is not None:
        get_owned_category(session, current_user.id, payload.category_id, TransactionType.EXPENSE)
        matching_category = Budget.category_id == payload.category_id
    else:
        matching_category = Budget.category_id.is_(None)
    existing = session.scalar(
        select(Budget).where(
            Budget.user_id == current_user.id,
            matching_category,
            Budget.month == payload.month,
            Budget.year == payload.year,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A budget for this period already exists.")
    budget = Budget(user_id=current_user.id, **payload.model_dump())
    session.add(budget)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A budget for this period already exists.") from exc
    session.refresh(budget, attribute_names=["category"])
    return _serialize_budget(session, budget)


@router.put("/{budget_id}", response_model=BudgetResponse, summary="Change a budget amount")
def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    budget = _owned_budget(session, current_user.id, budget_id)
    budget.amount = payload.amount
    session.commit()
    session.refresh(budget, attribute_names=["category"])
    return _serialize_budget(session, budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a budget")
def delete_budget(
    budget_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    budget = _owned_budget(session, current_user.id, budget_id)
    session.delete(budget)
    session.commit()
