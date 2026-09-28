"""Create the system's single user from values stored in .env.

Run from the project root:  python create_user.py

Required variables in .env (never commit .env):
  INITIAL_USER_EMAIL, INITIAL_USER_FULL_NAME, INITIAL_USER_PASSWORD
"""
import asyncio
from pathlib import Path

from dotenv import dotenv_values
from pydantic import ValidationError
from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import async_session_maker
from app.models.user_model import User
from app.schemas.user_schema import UserCreate

REQUIRED_VARS = ("INITIAL_USER_EMAIL", "INITIAL_USER_FULL_NAME", "INITIAL_USER_PASSWORD")


async def main():
    env = dotenv_values(Path(__file__).parent / ".env")

    missing = [name for name in REQUIRED_VARS if not env.get(name)]
    if missing:
        print("Missing variables in .env:", ", ".join(missing))
        return

    try:
        data = UserCreate(
            email=env["INITIAL_USER_EMAIL"],
            full_name=env["INITIAL_USER_FULL_NAME"],
            password=env["INITIAL_USER_PASSWORD"],
        )
    except ValidationError as exc:
        for error in exc.errors():
            print(f"- {error['loc'][0]}: {error['msg']}")
        return

    async with async_session_maker() as db:
        total = (await db.execute(select(func.count()).select_from(User))).scalar_one()
        if total > 0:
            print("A user already exists. This system is single-user; nothing was created.")
            return

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        db.add(user)
        await db.commit()
        print("User created:", user.id, user.email)


if __name__ == "__main__":
    asyncio.run(main())