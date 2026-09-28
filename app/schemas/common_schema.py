"""Shared schemas for pagination and filtering, reused across list endpoints."""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class DateRangeFilter(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = Field(
        default=None,
        description=(
            "Inclusive upper bound. To include an entire calendar day, "
            "pass its end-of-day time (e.g. 23:59:59), not just the date."
        ),
    )


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int