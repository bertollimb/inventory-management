"""Tests for the /categories endpoints."""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_model import Category
from app.models.product_model import Product


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


async def test_delete_category_removes_it(client: AsyncClient):
    create_response = await client.post("/categories", json={"name": "Descartável"})
    category_id = create_response.json()["id"]

    delete_response = await client.delete(f"/categories/{category_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/categories/{category_id}")
    assert get_response.status_code == 404


async def test_delete_category_with_products_returns_409(
    client: AsyncClient, test_category: Category, db: AsyncSession
):
    product = Product(
        name="Linked Product",
        sku="LINKED-001",
        category_id=test_category.id,
        unit_price=10,
        current_stock=0,
    )
    db.add(product)
    await db.commit()

    response = await client.delete(f"/categories/{test_category.id}")
    assert response.status_code == 409


async def test_delete_nonexistent_category_returns_404(client: AsyncClient):
    response = await client.delete("/categories/9999")
    assert response.status_code == 404