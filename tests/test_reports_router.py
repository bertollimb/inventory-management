"""Tests for the /reports endpoints."""
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_model import Category
from app.models.product_model import Product


async def test_low_stock_includes_product_at_or_below_threshold(client: AsyncClient, test_product: Product):
    # test_product starts with current_stock=0, min_stock_threshold=5 -> already low stock
    response = await client.get("/reports/low-stock")
    assert response.status_code == 200
    skus = [p["sku"] for p in response.json()]
    assert test_product.sku in skus


async def test_low_stock_excludes_product_above_threshold(
    client: AsyncClient, test_category: Category, db: AsyncSession
):
    well_stocked = Product(
        name="Well Stocked",
        sku="STOCKED-001",
        category_id=test_category.id,
        unit_price=Decimal("10.00"),
        min_stock_threshold=5,
        current_stock=100,
    )
    db.add(well_stocked)
    await db.commit()

    response = await client.get("/reports/low-stock")
    skus = [p["sku"] for p in response.json()]
    assert "STOCKED-001" not in skus


async def test_stock_value_sums_correctly(client: AsyncClient, test_category: Category, db: AsyncSession):
    db.add_all(
        [
            Product(
                name="A", sku="VAL-A", category_id=test_category.id,
                unit_price=Decimal("10.50"), current_stock=3,
            ),
            Product(
                name="B", sku="VAL-B", category_id=test_category.id,
                unit_price=Decimal("0.10"), current_stock=7,
            ),
        ]
    )
    await db.commit()

    response = await client.get("/reports/stock-value")
    assert response.status_code == 200
    assert response.json()["total_value"] == "32.20"


async def test_stock_value_is_zero_with_no_products(client: AsyncClient):
    response = await client.get("/reports/stock-value")
    assert response.status_code == 200
    assert response.json()["total_value"] == "0"


async def test_reports_require_authentication(unauthenticated_client: AsyncClient):
    response = await unauthenticated_client.get("/reports/low-stock")
    assert response.status_code == 401