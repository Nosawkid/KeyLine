from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User


async def register_user(session: AsyncSession, email: str, password: str) -> User:
    existing = await session.scalar(select(User).where(User.email == email.lower()))
    if existing:
        raise ValueError("email already registered")
    user = User(email=email.lower(), hashed_password=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await session.scalar(select(User).where(User.email == email.lower()))
    if not user or not user.is_active or not verify_password(password, user.hashed_password):
        return None
    return user
