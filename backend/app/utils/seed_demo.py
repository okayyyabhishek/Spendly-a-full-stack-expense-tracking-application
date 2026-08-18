"""Optional development-only sample data loader.

Run after migrations with a password you choose:
    python -m app.utils.seed_demo --password 'ChooseAStrongPassword9'
"""

import argparse
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.category import Category
from app.models.enums import PaymentMethod, TransactionType
from app.models.transaction import Transaction
from app.models.user import User
from app.services.category_service import create_default_categories


def seed(email: str, name: str, password: str) -> None:
    settings = get_settings()
    if settings.is_production:
        raise RuntimeError("Demo seed data is disabled in production.")
    with SessionLocal() as session:
        if session.scalar(select(User.id).where(User.email == email.lower())) is not None:
            raise RuntimeError(f"A user with {email} already exists; no data was changed.")
        user = User(name=name, email=email.lower(), password_hash=hash_password(password))
        session.add(user)
        session.flush()
        create_default_categories(session, user.id)
        session.flush()
        categories = {
            (category.type, category.name): category.id
            for category in session.scalars(select(Category).where(Category.user_id == user.id))
        }
        today = date.today()
        sample_rows = [
            (TransactionType.INCOME, "Salary", "Salary", "50000.00", PaymentMethod.BANK_TRANSFER, today.replace(day=1)),
            (TransactionType.EXPENSE, "Food", "Groceries", "4500.00", PaymentMethod.UPI, today - timedelta(days=2)),
            (TransactionType.EXPENSE, "Travel", "Metro and cabs", "2800.00", PaymentMethod.UPI, today - timedelta(days=5)),
            (TransactionType.EXPENSE, "Shopping", "Household shopping", "5000.00", PaymentMethod.CREDIT_CARD, today - timedelta(days=7)),
            (TransactionType.EXPENSE, "Bills", "Utility bill", "3500.00", PaymentMethod.BANK_TRANSFER, today - timedelta(days=9)),
            (TransactionType.EXPENSE, "Entertainment", "Weekend plans", "2000.00", PaymentMethod.DEBIT_CARD, today - timedelta(days=12)),
        ]
        session.add_all(
            [
                Transaction(
                    user_id=user.id,
                    type=transaction_type,
                    amount=Decimal(amount),
                    category_id=categories[(transaction_type, category_name)],
                    description=description,
                    payment_method=payment_method,
                    transaction_date=transaction_date,
                )
                for transaction_type, category_name, description, amount, payment_method, transaction_date in sample_rows
            ]
        )
        session.commit()
    print(f"Created development demo account: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create optional Spendly development demo data.")
    parser.add_argument("--email", default="demo@spendly.local")
    parser.add_argument("--name", default="Demo User")
    parser.add_argument("--password", required=True, help="A strong password for the optional demo user")
    args = parser.parse_args()
    seed(args.email, args.name, args.password)


if __name__ == "__main__":
    main()
