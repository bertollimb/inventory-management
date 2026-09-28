"""Authentication endpoints: login and access token refresh."""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.exceptions import InvalidCredentialsError
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.models.user_model import User
from app.schemas.auth_schema import RefreshTokenRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsError("Incorrect email or password.")

    return Token(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


@router.post("/refresh", response_model=Token)
async def refresh(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    payload = decode_token(data.refresh_token, expected_type="refresh")

    user = await db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise InvalidCredentialsError("User no longer exists or is inactive.")

    return Token(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=data.refresh_token,
    )