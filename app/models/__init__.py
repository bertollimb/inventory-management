"""Import every model here so they register on Base.metadata (used by Alembic)."""
from app.models.category_model import Category
from app.models.product_model import Product
from app.models.stock_movement_model import StockMovement
from app.models.user_model import User

__all__ = ["Category", "Product", "StockMovement", "User"]