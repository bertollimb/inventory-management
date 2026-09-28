"""Reporting endpoints: alert-style and aggregate queries.

Filtered movement history is not duplicated here: it lives at
GET /movements, which already supports product and date filters.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.schemas.product_schema import ProductRead, StockValueRead
from app.services import product_service

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/low-stock", response_model=list[ProductRead])
async def low_stock(db: AsyncSession = Depends(get_db)):
    return await product_service.list_low_stock_products(db)


@router.get("/stock-value", response_model=StockValueRead)
async def stock_value(db: AsyncSession = Depends(get_db)):
    total = await product_service.get_total_stock_value(db)
    return StockValueRead(total_value=total)