"""User-isolated transaction CRUD, pagination, search, and filters."""

from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionFilters, TransactionPage, TransactionResponse, TransactionUpdate
from app.services.ledger_service import get_owned_category
from app.services.notification_service import maybe_create_budget_alert
from app.services.recurring_service import process_due_transactions

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _apply_filters(statement: Select[tuple[Transaction]], user_id: int, filters: TransactionFilters) -> Select[tuple[Transaction]]:
    statement = statement.join(Category).where(Transaction.user_id == user_id)
    if filters.from_date:
        statement = statement.where(Transaction.transaction_date >= filters.from_date)
    if filters.to_date:
        statement = statement.where(Transaction.transaction_date <= filters.to_date)
    if filters.category_id:
        statement = statement.where(Transaction.category_id == filters.category_id)
    if filters.type:
        statement = statement.where(Transaction.type == filters.type)
    if filters.payment_method:
        statement = statement.where(Transaction.payment_method == filters.payment_method)
    if filters.min_amount is not None:
        statement = statement.where(Transaction.amount >= filters.min_amount)
    if filters.max_amount is not None:
        statement = statement.where(Transaction.amount <= filters.max_amount)
    if filters.search and filters.search.strip():
        search = f"%{filters.search.strip().lower()}%"
        statement = statement.where(
            or_(func.lower(func.coalesce(Transaction.description, "")).like(search), func.lower(Category.name).like(search))
        )
    return statement


def _get_owned_transaction(session: Session, user_id: int, transaction_id: int) -> Transaction:
    transaction = session.scalar(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    )
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    return transaction


@router.get("", response_model=TransactionPage, summary="List transactions with server-side filters and pagination")
def list_transactions(
    filters: TransactionFilters = Depends(),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionPage:
    process_due_transactions(session, current_user.id)
    session.commit()
    base_statement = _apply_filters(select(Transaction), current_user.id, filters)
    total = session.scalar(select(func.count()).select_from(base_statement.subquery())) or 0
    records = list(
        session.scalars(
            base_statement.options(selectinload(Transaction.category))
            .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
    )
    return TransactionPage(
        items=[TransactionResponse.model_validate(item) for item in records],
        page=filters.page,
        page_size=filters.page_size,
        total=total,
        total_pages=ceil(total / filters.page_size) if total else 0,
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, summary="Record an income or expense")
def create_transaction(
    payload: TransactionCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    get_owned_category(session, current_user.id, payload.category_id, payload.type)
    transaction = Transaction(user_id=current_user.id, **payload.model_dump())
    session.add(transaction)
    session.flush()
    if transaction.type.value == "expense":
        maybe_create_budget_alert(session, current_user.id, transaction.transaction_date)
    session.commit()
    session.refresh(transaction, attribute_names=["category"])
    return transaction


@router.get("/{transaction_id}", response_model=TransactionResponse, summary="Get a transaction owned by the signed-in user")
def get_transaction(
    transaction_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    return _get_owned_transaction(session, current_user.id, transaction_id)


@router.put("/{transaction_id}", response_model=TransactionResponse, summary="Update a transaction")
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    transaction = _get_owned_transaction(session, current_user.id, transaction_id)
    updates = payload.model_dump(exclude_unset=True)
    resulting_type = updates.get("type", transaction.type)
    resulting_category_id = updates.get("category_id", transaction.category_id)
    get_owned_category(session, current_user.id, resulting_category_id, resulting_type)
    for field, value in updates.items():
        setattr(transaction, field, value)
    session.flush()
    if transaction.type.value == "expense":
        maybe_create_budget_alert(session, current_user.id, transaction.transaction_date)
    session.commit()
    session.refresh(transaction, attribute_names=["category"])
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a transaction after client confirmation")
def delete_transaction(
    transaction_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    transaction = _get_owned_transaction(session, current_user.id, transaction_id)
    session.delete(transaction)
    session.commit()
