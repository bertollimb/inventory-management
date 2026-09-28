"""Application entry point.

Creates the FastAPI app, configures CORS, maps domain exceptions to HTTP
responses, and registers the routers.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    DuplicateSKUError,
    InsufficientStockError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
)
from app.routers import (
    auth_router,
    category_router,
    product_router,
    reports_router,
    stock_movement_router,
)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Domain exception -> HTTP status code.
EXCEPTION_STATUS: dict[type[Exception], int] = {
    NotFoundError: 404,
    DuplicateSKUError: 409,
    InsufficientStockError: 409,
    InvalidCredentialsError: 401,
    InvalidTokenError: 401,
}
AUTH_ERRORS = (InvalidCredentialsError, InvalidTokenError)


def _make_handler(status_code: int, with_auth_header: bool):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if with_auth_header else None
        return JSONResponse(status_code=status_code, content={"detail": str(exc)}, headers=headers)

    return handler


for exc_class, status_code in EXCEPTION_STATUS.items():
    app.add_exception_handler(exc_class, _make_handler(status_code, exc_class in AUTH_ERRORS))

app.include_router(auth_router.router)
app.include_router(category_router.router)
app.include_router(product_router.router)
app.include_router(stock_movement_router.router)
app.include_router(reports_router.router)