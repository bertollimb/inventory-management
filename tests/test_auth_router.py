"""Tests for the /auth endpoints."""
from httpx import AsyncClient

from app.models.user_model import User


async def test_login_with_correct_credentials(client: AsyncClient, test_user: User):
    # `client` already carries a Bearer token by default, but /auth/login
    # itself requires no authentication -- exercised directly here.
    response = await client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "test-password-123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_with_wrong_password_returns_401(client: AsyncClient, test_user: User):
    response = await client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_login_with_unknown_email_returns_same_401(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "whatever123"},
    )
    assert response.status_code == 401


async def test_refresh_issues_new_access_token(client: AsyncClient, test_user: User):
    login_response = await client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "test-password-123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_refresh_with_invalid_token_returns_401(client: AsyncClient):
    response = await client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401