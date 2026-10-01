"""Tests for the /movements endpoints.

The last test in this file, test_concurrent_out_movements_do_not_corrupt_stock,
intentionally does NOT use the shared `client`/`db` fixtures: those give every
test one single AsyncSession, which cannot be used by two coroutines at once.
To prove the race condition is actually handled at the database level, that
test opens two independent sessions and fires two real concurrent requests
directly through the service layer, then cleans up manually, since it
doesn't rely on the SAVEPOINT rollback pattern the other tests use.
"""
import asyncio
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.exceptions import InsufficientStockError
from app.core.security import hash_password
from app.models.category_model import Category
from app.models.product_model import Product
from app.models.stock_movement_model import StockMovement
from app.models.user_model import User
from app.schemas.stock_movement_schema import StockMovementCreate
from app.services import stock_movement_service


async def test_create_in_movement_increases_stock(client: AsyncClient, test_product: Product):
    response = await client.post(
        "/movements",
        json={
            "product_id": test_product.id,
            "movement_type": "IN",
            "quantity": 20,
            "reason": "PURCHASE",
        },
    )
    assert response.status_code == 201

    product_response = await client.get(f"/products/{test_product.id}")
    assert product_response.json()["current_stock"] == 20


async def test_create_out_movement_decreases_stock(client: AsyncClient, test_product: Product):
    await client.post(
        "/movements",
        json={"product_id": test_product.id, "movement_type": "IN", "quantity": 20, "reason": "PURCHASE"},
    )
    response = await client.post(
        "/movements",
        json={"product_id": test_product.id, "movement_type": "OUT", "quantity": 5, "reason": "USE"},
    )
    assert response.status_code == 201

    product_response = await client.get(f"/products/{test_product.id}")
    assert product_response.json()["current_stock"] == 15


async def test_out_movement_insufficient_stock_returns_409(client: AsyncClient, test_product: Product):
    # test_product starts with current_stock=0
    response = await client.post(
        "/movements",
        json={"product_id": test_product.id, "movement_type": "OUT", "quantity": 1, "reason": "USE"},
    )
    assert response.status_code == 409


async def test_movement_uses_authenticated_user_as_created_by(
    client: AsyncClient, test_product: Product, test_user: User
):
    response = await client.post(
        "/movements",
        json={"product_id": test_product.id, "movement_type": "IN", "quantity": 10, "reason": "PURCHASE"},
    )
    assert response.json()["created_by"] == test_user.id


async def test_list_movements_filtered_by_product(client: AsyncClient, test_product: Product, db):
    other_product = Product(
        name="Other Product",
        sku="OTHER-001",
        category_id=test_product.category_id,
        unit_price=Decimal("5.00"),
        current_stock=0,
    )
    db.add(other_product)
    await db.commit()
    await db.refresh(other_product)

    await client.post(
        "/movements",
        json={"product_id": test_product.id, "movement_type": "IN", "quantity": 10, "reason": "PURCHASE"},
    )
    await client.post(
        "/movements",
        json={"product_id": other_product.id, "movement_type": "IN", "quantity": 5, "reason": "PURCHASE"},
    )

    response = await client.get("/movements", params={"product_id": test_product.id})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["product_id"] == test_product.id


async def test_movements_require_authentication(unauthenticated_client: AsyncClient):
    response = await unauthenticated_client.get("/movements")
    assert response.status_code == 401


async def test_concurrent_out_movements_do_not_corrupt_stock(engine: AsyncEngine):
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as setup_session:
        user = User(email="race@example.com", full_name="Race User", hashed_password=hash_password("x"))
        category = Category(name="Race Category")
        setup_session.add_all([user, category])
        await setup_session.commit()

        product = Product(
            name="Race Product",
            sku="RACE-001",
            category_id=category.id,
            unit_price=Decimal("10.00"),
            current_stock=10,
        )
        setup_session.add(product)
        await setup_session.commit()
        await setup_session.refresh(product)
        product_id, category_id, user_id = product.id, category.id, user.id

    try:
        async def do_out_movement():
            async with session_factory() as session:
                data = StockMovementCreate(
                    product_id=product_id, movement_type="OUT", quantity=7, reason="USE"
                )
                return await stock_movement_service.create_movement(session, data, created_by=user_id)

        results = await asyncio.gather(do_out_movement(), do_out_movement(), return_exceptions=True)

        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, InsufficientStockError)]
        assert len(successes) == 1
        assert len(failures) == 1

        async with session_factory() as check_session:
            refreshed = await check_session.get(Product, product_id)
            assert refreshed.current_stock == 3  # 10 - 7, the second movement correctly rejected
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.execute(delete(StockMovement).where(StockMovement.product_id == product_id))
            await cleanup_session.execute(delete(Product).where(Product.id == product_id))
            await cleanup_session.execute(delete(Category).where(Category.id == category_id))
            await cleanup_session.execute(delete(User).where(User.id == user_id))
            await cleanup_session.commit()