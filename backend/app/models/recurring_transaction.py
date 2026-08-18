"""Schedules which materialize into actual transactions when due."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import Frequency, PaymentMethod, TransactionType

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class RecurringTransaction(TimestampMixin, Base):
    __tablename__ = "recurring_transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_recurring_positive_amount"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_recurring_valid_date_range"),
        Index("ix_recurring_due", "active", "next_due_date"),
        Index("ix_recurring_user_active", "user_id", "active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType, native_enum=False, length=16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=24), nullable=False
    )
    frequency: Mapped[Frequency] = mapped_column(Enum(Frequency, native_enum=False, length=16), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="recurring_transactions")
    category: Mapped["Category"] = relationship(back_populates="recurring_transactions")
