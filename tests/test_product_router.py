"""Tests for the /products endpoints."""
from httpx import AsyncClient

from app.models.category_model import Category
from app.models.product_model import Product


async def test_create_product(client: AsyncClient, test_category: Category):
    response = await client.post(
        "/products",
        json={
            "name": "Notebook",
            "sku": "NB-001",
            "category_id": test_category.id,
            "unit_price": "1500.00",
            "min_stock_threshold": 2,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Notebook"
    assert body["current_stock"] == 0


async def test_create_product_with_nonexistent_category_returns_404(client: AsyncClient):
    response = await client.post(
        "/products",
        json={
            "name": "Notebook",
            "sku": "NB-002",
            "category_id": 9999,
            "unit_price": "1500.00",
        },
    )
    assert response.status_code == 404


async def test_duplicate_sku_returns_409(client: AsyncClient, test_category: Category):
    payload = {
        "name": "Notebook",
        "sku": "NB-DUP",
        "category_id": test_category.id,
        "unit_price": "1500.00",
    }
    await client.post("/products", json=payload)
    response = await client.post("/products", json=payload)
    assert response.status_code == 409


async def test_list_products(client: AsyncClient, test_product: Product):
    response = await client.get("/products")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["sku"] == test_product.sku


async def test_get_nonexistent_product_returns_404(client: AsyncClient):
    response = await client.get("/products/9999")
    assert response.status_code == 404


async def test_update_product(client: AsyncClient, test_product: Product):
    response = await client.patch(f"/products/{test_product.id}", json={"unit_price": "20.00"})
    assert response.status_code == 200
    assert response.json()["unit_price"] == "20.00"


async def test_products_require_authentication(unauthenticated_client: AsyncClient):
    response = await unauthenticated_client.get("/products")
    assert response.status_code == 401