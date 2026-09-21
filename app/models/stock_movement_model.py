"""SQLAlchemy model for StockMovement.

Stock movements are an append-only ledger: created and read, never
updated or deleted. Product.current_stock is kept in sync with this
history by the service layer, inside the same transaction as the insert.
"""
import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product_model import Product
    from app.models.user_model import User


class MovementType(str, enum.Enum):
    """Direction of a stock movement."""

    IN = "IN"
    OUT = "OUT"


class MovementReason(str, enum.Enum):
    """Business reason behind a stock movement."""

    PURCHASE = "PURCHASE"
    SALE = "SALE"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN = "RETURN"


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_stock_movements_quantity_positive"),
        Index("ix_stock_movements_product_created_at", "product_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    product: Mapped["Product"] = relationship()

    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType, name="movement_type"))
    quantity: Mapped[int]
    reason: Mapped[MovementReason] = mapped_column(Enum(MovementReason, name="movement_reason"))

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    user: Mapped["User"] = relationship()

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())