"""User-owned transaction categories."""

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import TransactionType

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.recurring_transaction import RecurringTransaction
    from app.models.transaction import Transaction
    from app.models.user import User


class Category(TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("user_id", "type", "name", name="uq_category_user_type_name"),
        Index("ix_categories_user_type", "user_id", "type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType, native_enum=False, length=16), nullable=False)
    color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(40), nullable=True)

    user: Mapped["User"] = relationship(back_populates="categories")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category", passive_deletes=True)
    budgets: Mapped[list["Budget"]] = relationship(back_populates="category", passive_deletes=True)
    recurring_transactions: Mapped[list["RecurringTransaction"]] = relationship(back_populates="category", passive_deletes=True)
