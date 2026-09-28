"""Business logic for Category."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateCategoryError, NotFoundError
from app.models.category_model import Category
from app.schemas.category_schema import CategoryCreate, CategoryUpdate


async def _ensure_name_is_unique(db: AsyncSession, name: str, exclude_id: int | None = None) -> None:
    stmt = select(Category).where(Category.name == name)
    if exclude_id is not None:
        stmt = stmt.where(Category.id != exclude_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise DuplicateCategoryError(f"Category with name '{name}' already exists.")


async def create_category(db: AsyncSession, data: CategoryCreate) -> Category:
    await _ensure_name_is_unique(db, data.name)

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

    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data:
        await _ensure_name_is_unique(db, update_data["name"], exclude_id=category_id)

    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    return category