"""Default category creation used only when a user opens a new account."""

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import TransactionType

DEFAULT_CATEGORIES: tuple[tuple[TransactionType, str, str, str], ...] = (
    (TransactionType.EXPENSE, "Food", "#F2994A", "utensils"),
    (TransactionType.EXPENSE, "Travel", "#3B82F6", "plane"),
    (TransactionType.EXPENSE, "Shopping", "#A855F7", "shopping-bag"),
    (TransactionType.EXPENSE, "Bills", "#FACC15", "receipt"),
    (TransactionType.EXPENSE, "Education", "#14B8A6", "graduation-cap"),
    (TransactionType.EXPENSE, "Entertainment", "#EC4899", "sparkles"),
    (TransactionType.EXPENSE, "Health", "#EF4444", "heart-pulse"),
    (TransactionType.EXPENSE, "Rent", "#64748B", "house"),
    (TransactionType.EXPENSE, "Subscriptions", "#6366F1", "repeat-2"),
    (TransactionType.EXPENSE, "Other", "#94A3B8", "circle-ellipsis"),
    (TransactionType.INCOME, "Salary", "#22C55E", "wallet-cards"),
    (TransactionType.INCOME, "Freelance", "#0EA5E9", "briefcase-business"),
    (TransactionType.INCOME, "Business", "#10B981", "store"),
    (TransactionType.INCOME, "Investment", "#8B5CF6", "chart-no-axes-combined"),
    (TransactionType.INCOME, "Pocket Money", "#84CC16", "hand-coins"),
    (TransactionType.INCOME, "Other", "#94A3B8", "circle-ellipsis"),
)


def create_default_categories(session: Session, user_id: int) -> None:
    session.add_all(
        [
            Category(user_id=user_id, type=category_type, name=name, color=color, icon=icon)
            for category_type, name, color, icon in DEFAULT_CATEGORIES
        ]
    )
