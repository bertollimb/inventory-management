"""Product endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.schemas.common_schema import PaginatedResponse, PaginationParams
from app.schemas.product_schema import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service

router = APIRouter(
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await product_service.create_product(db, data)


@router.get("", response_model=PaginatedResponse[ProductRead])
async def list_products(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    products, total = await product_service.list_products(db, pagination)
    return PaginatedResponse[ProductRead](
        items=products,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await product_service.get_product(db, product_id)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    return await product_service.update_product(db, product_id, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    await product_service.delete_product(db, product_id)