"""Business logic for StockMovement.

The core rule of the project lives here: a stock movement is only ever
recorded by an atomic, conditional UPDATE on Product.current_stock,
computed and checked entirely in SQL. A naive read-then-write in Python
is vulnerable to lost updates under concurrent requests — see the
project's PR history for a reproduction of that bug.
"""
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientStockError, NotFoundError
from app.models.product_model import Product
from app.models.stock_movement_model import MovementType, StockMovement
from app.schemas.common_schema import DateRangeFilter, PaginationParams
from app.schemas.stock_movement_schema import StockMovementCreate


async def create_movement(db: AsyncSession, data: StockMovementCreate, created_by: int) -> StockMovement:
    if data.movement_type == MovementType.OUT:
        stmt = (
            update(Product)
            .where(Product.id == data.product_id, Product.current_stock >= data.quantity)
            .values(current_stock=Product.current_stock - data.quantity)
        )
    else:
        stmt = (
            update(Product)
            .where(Product.id == data.product_id)
            .values(current_stock=Product.current_stock + data.quantity)
        )

    result = await db.execute(stmt)

    if result.rowcount == 0:
        product = await db.get(Product, data.product_id)
        if product is None:
            raise NotFoundError(f"Product with id {data.product_id} not found.")
        raise InsufficientStockError(
            f"Insufficient stock for product {data.product_id}: "
            f"requested {data.quantity}, available {product.current_stock}."
        )

    movement = StockMovement(
        product_id=data.product_id,
        movement_type=data.movement_type,
        quantity=data.quantity,
        reason=data.reason,
        created_by=created_by,
    )
    db.add(movement)

    await db.commit()
    await db.refresh(movement)
    return movement


async def get_movement(db: AsyncSession, movement_id: int) -> StockMovement:
    movement = await db.get(StockMovement, movement_id)
    if movement is None:
        raise NotFoundError(f"Stock movement with id {movement_id} not found.")
    return movement


async def list_movements(
    db: AsyncSession,
    pagination: PaginationParams,
    product_id: int | None = None,
    date_range: DateRangeFilter | None = None,
) -> tuple[list[StockMovement], int]:
    filters = []
    if product_id is not None:
        filters.append(StockMovement.product_id == product_id)
    if date_range is not None:
        if date_range.start_date is not None:
            filters.append(StockMovement.created_at >= date_range.start_date)
        if date_range.end_date is not None:
            filters.append(StockMovement.created_at <= date_range.end_date)

    total = (
        await db.execute(select(func.count()).select_from(StockMovement).where(*filters))
    ).scalar_one()

    offset = (pagination.page - 1) * pagination.page_size
    result = await db.execute(
        select(StockMovement)
        .where(*filters)
        .order_by(StockMovement.created_at.desc())
        .offset(offset)
        .limit(pagination.page_size)
    )
    return list(result.scalars().all()), total