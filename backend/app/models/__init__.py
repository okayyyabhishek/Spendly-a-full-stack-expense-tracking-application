"""Import all SQLAlchemy models so Alembic discovers their metadata."""

from app.models.budget import Budget
from app.models.category import Category
from app.models.notification import Notification
from app.models.recurring_transaction import RecurringTransaction
from app.models.revoked_token import RevokedToken
from app.models.transaction import Transaction
from app.models.user import User

__all__ = ["Budget", "Category", "Notification", "RecurringTransaction", "RevokedToken", "Transaction", "User"]
