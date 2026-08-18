"""Shared user-scoped ledger operations and category ownership checks."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import TransactionType


def get_owned_category(session: Session, user_id: int, category_id: int, expected_type: TransactionType | None = None) -> Category:
    category = session.scalar(select(Category).where(Category.id == category_id, Category.user_id == user_id))
    if category is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose a category from your account.")
    if expected_type is not None and category.type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Choose an {expected_type.value} category for this transaction.",
        )
    return category
