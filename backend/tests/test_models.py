from app.database.base import Base
import app.models  # noqa: F401


def test_ledger_schema_contains_all_required_domain_tables() -> None:
    expected = {
        "users",
        "categories",
        "transactions",
        "budgets",
        "recurring_transactions",
        "notifications",
    }

    assert expected.issubset(Base.metadata.tables)


def test_transactions_have_user_scoped_lookup_indexes() -> None:
    indexes = {index.name for index in Base.metadata.tables["transactions"].indexes}

    assert {"ix_transactions_user_date", "ix_transactions_user_type_date", "ix_transactions_user_category_date"}.issubset(indexes)
