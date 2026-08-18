from datetime import date, timedelta

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Jordan Lee",
            "email": email,
            "password": "StrongPass9",
            "confirm_password": "StrongPass9",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _category_id(client: TestClient, token: str, category_type: str, name: str) -> int:
    response = client.get("/api/v1/categories", params={"type": category_type}, headers=_headers(token))
    assert response.status_code == 200
    return next(category["id"] for category in response.json() if category["name"] == name)


def test_transaction_crud_search_filters_and_cross_user_isolation(client: TestClient) -> None:
    first_token = _register(client, "first@example.com")
    second_token = _register(client, "second@example.com")
    food_id = _category_id(client, first_token, "expense", "Food")

    created = client.post(
        "/api/v1/transactions",
        headers=_headers(first_token),
        json={
            "type": "expense",
            "amount": "245.50",
            "category_id": food_id,
            "description": "Sunday brunch",
            "payment_method": "upi",
            "transaction_date": date.today().isoformat(),
        },
    )
    assert created.status_code == 201, created.json()
    transaction = created.json()
    assert transaction["category"]["name"] == "Food"

    listing = client.get("/api/v1/transactions", params={"search": "brunch", "type": "expense"}, headers=_headers(first_token))
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    update = client.put(
        f"/api/v1/transactions/{transaction['id']}",
        headers=_headers(first_token),
        json={"amount": "300", "description": "Sunday family brunch"},
    )
    assert update.status_code == 200
    assert update.json()["description"] == "Sunday family brunch"

    inaccessible = client.get(f"/api/v1/transactions/{transaction['id']}", headers=_headers(second_token))
    assert inaccessible.status_code == 404

    deletion = client.delete(f"/api/v1/transactions/{transaction['id']}", headers=_headers(first_token))
    assert deletion.status_code == 204
    assert client.get("/api/v1/transactions", headers=_headers(first_token)).json()["total"] == 0


def test_categories_reject_duplicate_and_protect_historical_data(client: TestClient) -> None:
    token = _register(client, "categories@example.com")
    created = client.post(
        "/api/v1/categories",
        headers=_headers(token),
        json={"name": "Coffee", "type": "expense", "color": "#4A332D", "icon": "coffee"},
    )
    assert created.status_code == 201
    category_id = created.json()["id"]
    duplicate = client.post(
        "/api/v1/categories",
        headers=_headers(token),
        json={"name": "Coffee", "type": "expense"},
    )
    assert duplicate.status_code == 409

    transaction = client.post(
        "/api/v1/transactions",
        headers=_headers(token),
        json={
            "type": "expense",
            "amount": "99",
            "category_id": category_id,
            "payment_method": "cash",
            "transaction_date": date.today().isoformat(),
        },
    )
    assert transaction.status_code == 201
    assert client.delete(f"/api/v1/categories/{category_id}", headers=_headers(token)).status_code == 409


def test_budget_progress_uses_persisted_expense_data(client: TestClient) -> None:
    token = _register(client, "budget@example.com")
    today = date.today()
    food_id = _category_id(client, token, "expense", "Food")
    transaction = client.post(
        "/api/v1/transactions",
        headers=_headers(token),
        json={
            "type": "expense",
            "amount": "85",
            "category_id": food_id,
            "description": "Groceries",
            "payment_method": "debit_card",
            "transaction_date": today.isoformat(),
        },
    )
    assert transaction.status_code == 201
    created_budget = client.post(
        "/api/v1/budgets",
        headers=_headers(token),
        json={"amount": "100", "category_id": food_id, "month": today.month, "year": today.year},
    )
    assert created_budget.status_code == 201, created_budget.json()
    budget = created_budget.json()
    assert budget["spent"] == "85.00"
    assert budget["remaining"] == "15.00"
    assert budget["status"] == "warning"


def test_recurring_schedule_creates_due_transaction_once(client: TestClient) -> None:
    token = _register(client, "recurring@example.com")
    rent_id = _category_id(client, token, "expense", "Rent")
    created = client.post(
        "/api/v1/recurring",
        headers=_headers(token),
        json={
            "type": "expense",
            "amount": "12000",
            "category_id": rent_id,
            "description": "Apartment rent",
            "payment_method": "bank_transfer",
            "frequency": "daily",
            "start_date": date.today().isoformat(),
        },
    )
    assert created.status_code == 201, created.json()
    schedule = created.json()
    assert schedule["next_due_date"] == (date.today() + timedelta(days=1)).isoformat()

    first_process = client.post("/api/v1/recurring/process-due", headers=_headers(token))
    assert first_process.status_code == 200
    assert first_process.json()["created"] == 0
    transactions = client.get("/api/v1/transactions", params={"search": "Apartment rent"}, headers=_headers(token))
    assert transactions.status_code == 200
    assert transactions.json()["total"] == 1
