"""Authenticated category management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.budget import Budget
from app.models.category import Category
from app.models.enums import TransactionType
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


def _owned_category(session: Session, user_id: int, category_id: int) -> Category:
    category = session.scalar(select(Category).where(Category.id == category_id, Category.user_id == user_id))
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return category


@router.get("", response_model=list[CategoryResponse], summary="List the signed-in user's categories")
def list_categories(
    type: TransactionType | None = None,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Category]:
    statement = select(Category).where(Category.user_id == current_user.id)
    if type is not None:
        statement = statement.where(Category.type == type)
    return list(session.scalars(statement.order_by(Category.type, Category.name)))


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="Create a category")
def create_category(
    payload: CategoryCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Category:
    category = Category(user_id=current_user.id, **payload.model_dump())
    session.add(category)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with this name and type already exists.") from exc
    session.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryResponse, summary="Update a category")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Category:
    category = _owned_category(session, current_user.id, category_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return category
    if "type" in updates and updates["type"] != category.type:
        is_used = any(
            session.scalar(select(exists().where(model.category_id == category.id)))
            for model in (Transaction, RecurringTransaction)
        )
        if is_used:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A category type cannot change after it has been used. Create a new category instead.",
            )
    for field, value in updates.items():
        setattr(category, field, value)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with this name and type already exists.") from exc
    session.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an unused category")
def delete_category(
    category_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    category = _owned_category(session, current_user.id, category_id)
    is_used = any(
        session.scalar(select(exists().where(model.category_id == category.id)))
        for model in (Transaction, RecurringTransaction, Budget)
    )
    if is_used:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This category is in use and cannot be deleted. Keep it for your financial history.",
        )
    session.delete(category)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
