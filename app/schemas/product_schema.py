"""Pydantic schemas for Product."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    sku: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    category_id: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    min_stock_threshold: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    category_id: int | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, gt=0)
    min_stock_threshold: int | None = Field(default=None, ge=0)


class ProductRead(ProductBase):
    id: int
    current_stock: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)