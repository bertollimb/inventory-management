"""SQLAlchemy model for Product."""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category_model import Category


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("current_stock >= 0", name="ck_products_current_stock_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), default=None)

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    category: Mapped["Category"] = relationship(back_populates="products")

    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    current_stock: Mapped[int] = mapped_column(default=0)
    min_stock_threshold: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())