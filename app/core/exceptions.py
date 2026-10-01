"""Domain-level exceptions.

These are raised by services and translated into HTTP responses by
exception handlers registered in main.py — keeps the service layer free
of any FastAPI/HTTP-specific concern, so it stays easy to unit test.
"""


class NotFoundError(Exception):
    """Raised when a referenced entity does not exist in the database."""
    pass


class InsufficientStockError(Exception):
    """Raised when a stock movement would leave the product's stock negative."""
    pass


class DuplicateSKUError(Exception):
    """Raised when creating a product with an SKU that already exists."""
    pass


class DuplicateCategoryError(Exception):
    """Raised when creating or renaming a category to a name that already exists."""
    pass


class CategoryInUseError(Exception):
    """Raised when deleting a category that still has products linked to it."""
    pass


class ProductInUseError(Exception):
    """Raised when deleting a product that already has stock movements."""
    pass


class InvalidCredentialsError(Exception):
    """Raised when login email/password do not match a valid user."""
    pass


class InvalidTokenError(Exception):
    """Raised when a JWT (access or refresh) is invalid, expired, or revoked."""
    pass