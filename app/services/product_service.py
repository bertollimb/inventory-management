"""Business logic for Product."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateSKUError, NotFoundError
from app.models.category_model import Category
from app.models.product_model import Product
from app.schemas.common_schema import PaginationParams
from app.schemas.product_schema import ProductCreate, ProductUpdate


async def _ensure_category_exists(db: AsyncSession, category_id: int) -> None:
    category = await db.get(Category, category_id)
    if category is None:
        raise NotFoundError(f"Category with id {category_id} not found.")


async def _ensure_sku_is_unique(db: AsyncSession, sku: str) -> None:
    result = await db.execute(select(Product).where(Product.sku == sku))
    if result.scalar_one_or_none() is not None:
        raise DuplicateSKUError(f"Product with SKU '{sku}' already exists.")


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    await _ensure_category_exists(db, data.category_id)
    await _ensure_sku_is_unique(db, data.sku)

    product = Product(**data.model_dump(), current_stock=0)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def get_product(db: AsyncSession, product_id: int) -> Product:
    product = await db.get(Product, product_id)
    if product is None:
        raise NotFoundError(f"Product with id {product_id} not found.")
    return product


async def list_products(db: AsyncSession, pagination: PaginationParams) -> tuple[list[Product], int]:
    total = (await db.execute(select(func.count()).select_from(Product))).scalar_one()

    offset = (pagination.page - 1) * pagination.page_size
    result = await db.execute(
        select(Product).order_by(Product.name).offset(offset).limit(pagination.page_size)
    )
    return list(result.scalars().all()), total


async def update_product(db: AsyncSession, product_id: int, data: ProductUpdate) -> Product:
    product = await get_product(db, product_id)

    update_data = data.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        await _ensure_category_exists(db, update_data["category_id"])

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product


async def list_low_stock_products(db: AsyncSession) -> list[Product]:
    result = await db.execute(
        select(Product)
        .where(Product.current_stock <= Product.min_stock_threshold)
        .order_by(Product.name)
    )
    return list(result.scalars().all())
