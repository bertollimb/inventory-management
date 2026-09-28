"""Shared pytest fixtures: an isolated database session per test (SAVEPOINT
rollback pattern), and an authenticated async HTTP client wired to use that
same session, hitting the real FastAPI app.
"""
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.core.config import settings
from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.main import app
from app.models.category_model import Category
from app.models.product_model import Product
from app.models.user_model import User


def _test_db_url() -> str:
    if settings.TEST_DB_URL is None:
        raise RuntimeError(
            "TEST_DB_URL is not set in .env. The test suite needs a dedicated "
            "local database, separate from the one used for manual testing."
        )
    return str(settings.TEST_DB_URL)


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """One engine for the whole test session; (re)creates all tables once."""
    test_engine = create_async_engine(_test_db_url())
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """A session isolated in its own SAVEPOINT, rolled back after the test.

    Any commit the application code makes only releases the savepoint --
    it never reaches the database for real, so tests never leak data into
    each other, no matter how many commits happen inside one test.
    """
    async with engine.connect() as connection:
        outer_transaction = await connection.begin()
        await connection.begin_nested()

        session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

        yield session

        await session.close()
        await outer_transaction.rollback()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hash_password("test-password-123"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_category(db: AsyncSession) -> Category:
    category = Category(name="Test Category")
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@pytest_asyncio.fixture
async def test_product(db: AsyncSession, test_category: Category) -> Product:
    product = Product(
        name="Test Product",
        sku="TEST-SKU-001",
        category_id=test_category.id,
        unit_price=Decimal("10.00"),
        min_stock_threshold=5,
        current_stock=0,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@pytest_asyncio.fixture
async def client(db: AsyncSession, test_user: User) -> AsyncGenerator[AsyncClient, None]:
    """An authenticated async client hitting the real app, sharing `db`."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(subject=str(test_user.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauthenticated_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Same as `client`, but without a token -- for testing 401 responses."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()