"""Pydantic schemas for StockMovement."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.stock_movement_model import MovementReason, MovementType


class StockMovementBase(BaseModel):
    product_id: int = Field(gt=0)
    movement_type: MovementType
    quantity: int = Field(gt=0)
    reason: MovementReason


class StockMovementCreate(StockMovementBase):
    pass


class StockMovementRead(StockMovementBase):
    id: int
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)