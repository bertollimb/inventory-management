"""Tests for the /categories endpoints."""
from httpx import AsyncClient


async def test_create_category(client: AsyncClient):
    response = await client.post("/categories", json={"name": "Bebidas"})
    assert response.status_code == 201
    assert response.json()["name"] == "Bebidas"


async def test_list_categories_is_empty_by_default(client: AsyncClient):
    response = await client.get("/categories")
    assert response.status_code == 200
    assert response.json() == []


async def test_duplicate_category_name_returns_409(client: AsyncClient):
    await client.post("/categories", json={"name": "Bebidas"})
    response = await client.post("/categories", json={"name": "Bebidas"})
    assert response.status_code == 409


async def test_categories_require_authentication(unauthenticated_client: AsyncClient):
    response = await unauthenticated_client.get("/categories")
    assert response.status_code == 401