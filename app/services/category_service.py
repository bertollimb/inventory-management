"""Business logic for Category."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.category_model import Category
from app.schemas.category_schema import CategoryCreate, CategoryUpdate


async def create_category(db: AsyncSession, data: CategoryCreate) -> Category:
    category = Category(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def get_category(db: AsyncSession, category_id: int) -> Category:
    category = await db.get(Category, category_id)
    if category is None:
        raise NotFoundError(f"Category with id {category_id} not found.")
    return category


async def list_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


async def update_category(db: AsyncSession, category_id: int, data: CategoryUpdate) -> Category:
    category = await get_category(db, category_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return category