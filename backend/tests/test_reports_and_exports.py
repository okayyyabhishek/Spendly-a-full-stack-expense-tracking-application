from datetime import date

from fastapi.testclient import TestClient


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Report User",
            "email": "report@example.com",
            "password": "StrongPass9",
            "confirm_password": "StrongPass9",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _category(client: TestClient, token: str, type: str, name: str) -> int:
    categories = client.get("/api/v1/categories", params={"type": type}, headers=_headers(token)).json()
    return next(item["id"] for item in categories if item["name"] == name)


def test_analytics_notifications_and_exports_use_real_ledger_records(client: TestClient) -> None:
    token = _register(client)
    today = date.today()
    food_id = _category(client, token, "expense", "Food")
    salary_id = _category(client, token, "income", "Salary")
    budget = client.post(
        "/api/v1/budgets",
        headers=_headers(token),
        json={"amount": "100", "month": today.month, "year": today.year},
    )
    assert budget.status_code == 201
    for payload in (
        {
            "type": "income",
            "amount": "1000",
            "category_id": salary_id,
            "description": "August salary",
            "payment_method": "bank_transfer",
            "transaction_date": today.isoformat(),
        },
        {
            "type": "expense",
            "amount": "90",
            "category_id": food_id,
            "description": "Market groceries",
            "payment_method": "upi",
            "transaction_date": today.isoformat(),
        },
    ):
        response = client.post("/api/v1/transactions", headers=_headers(token), json=payload)
        assert response.status_code == 201, response.json()

    dashboard = client.get("/api/v1/analytics/summary", headers=_headers(token))
    assert dashboard.status_code == 200
    assert dashboard.json()["total_balance"] == "910.00"
    assert dashboard.json()["budget_utilization"] == "90.00"

    categories = client.get("/api/v1/analytics/categories", headers=_headers(token))
    assert categories.status_code == 200
    assert categories.json()[0]["category_name"] == "Food"
    assert categories.json()[0]["amount"] == "90.00"

    monthly_summary = client.get("/api/v1/analytics/monthly-summary", headers=_headers(token))
    assert monthly_summary.status_code == 200
    assert monthly_summary.json()["savings"] == "910.00"

    alerts = client.get("/api/v1/notifications", headers=_headers(token))
    assert alerts.status_code == 200
    assert alerts.json()["unread_count"] == 1
    assert alerts.json()["items"][0]["kind"] == "budget_warning"

    csv_file = client.get("/api/v1/export/csv", headers=_headers(token))
    assert csv_file.status_code == 200
    assert "Market groceries" in csv_file.text
    assert "text/csv" in csv_file.headers["content-type"]

    pdf_file = client.get("/api/v1/export/pdf", headers=_headers(token))
    assert pdf_file.status_code == 200
    assert pdf_file.content.startswith(b"%PDF")
