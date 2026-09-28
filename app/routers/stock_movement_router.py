"""Stock movement endpoints.

Movements are an append-only ledger: there is intentionally no update
or delete endpoint. Corrections are new compensating movements.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user_model import User
from app.schemas.common_schema import DateRangeFilter, PaginatedResponse, PaginationParams
from app.schemas.stock_movement_schema import StockMovementCreate, StockMovementRead
from app.services import stock_movement_service

router = APIRouter(
    prefix="/movements",
    tags=["movements"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=StockMovementRead, status_code=status.HTTP_201_CREATED)
async def create_movement(
    data: StockMovementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await stock_movement_service.create_movement(db, data, created_by=current_user.id)


@router.get("", response_model=PaginatedResponse[StockMovementRead])
async def list_movements(
    pagination: PaginationParams = Depends(),
    date_range: DateRangeFilter = Depends(),
    product_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    movements, total = await stock_movement_service.list_movements(
        db, pagination, product_id, date_range
    )
    return PaginatedResponse[StockMovementRead](
        items=movements,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{movement_id}", response_model=StockMovementRead)
async def get_movement(movement_id: int, db: AsyncSession = Depends(get_db)):
    return await stock_movement_service.get_movement(db, movement_id)