from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category


def register(client: TestClient, email: str = "alex@example.com") -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alex Morgan",
            "email": email,
            "password": "StrongPass9",
            "confirm_password": "StrongPass9",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_user_default_categories_and_jwt(client: TestClient, session: Session) -> None:
    payload = register(client)

    assert payload["token_type"] == "bearer"
    assert isinstance(payload["access_token"], str)
    assert payload["user"]["email"] == "alex@example.com"
    assert session.scalar(select(func.count(Category.id))) == 16


def test_register_rejects_duplicate_email_and_weak_password(client: TestClient) -> None:
    register(client)
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Another Person",
            "email": "ALEX@example.com",
            "password": "StrongPass9",
            "confirm_password": "StrongPass9",
        },
    )
    weak = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Weak Password",
            "email": "weak@example.com",
            "password": "weakpass",
            "confirm_password": "weakpass",
        },
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["message"] == "An account with this email already exists."
    assert weak.status_code == 422
    assert weak.json()["error"]["code"] == "validation_error"


def test_login_profile_and_logout_revoke_current_token(client: TestClient) -> None:
    register(client)
    login = client.post("/api/v1/auth/login", json={"email": "alex@example.com", "password": "StrongPass9"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    profile = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert profile.status_code == 200
    assert profile.json()["name"] == "Alex Morgan"

    logout = client.post("/api/v1/auth/logout", headers=auth_headers(token))
    assert logout.status_code == 204

    blocked_profile = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert blocked_profile.status_code == 401
    assert blocked_profile.json()["error"]["message"] == "This session has ended. Please sign in again."
