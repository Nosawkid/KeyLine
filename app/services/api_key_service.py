from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import api_key_matches, hash_api_key
from app.models.api_key import APIKey
from app.models.application import Application
from app.utils.api_key_generator import generate_api_key


async def create_api_key(session: AsyncSession, application_id: UUID, name: str, expires_at: datetime | None) -> tuple[APIKey, str]:
    if expires_at and expires_at.tzinfo is None:
        raise ValueError("expiration must include a timezone")
    if expires_at and expires_at <= datetime.now(UTC):
        raise ValueError("expiration must be in the future")
    plaintext, prefix = generate_api_key()
    api_key = APIKey(application_id=application_id, name=name, key_prefix=prefix, key_hash=hash_api_key(plaintext), expires_at=expires_at)
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return api_key, plaintext


async def get_owned_key(session: AsyncSession, key_id: UUID, user_id: UUID) -> APIKey | None:
    statement = select(APIKey).join(Application).where(APIKey.id == key_id, Application.user_id == user_id)
    return await session.scalar(statement)


async def list_application_keys(session: AsyncSession, application_id: UUID) -> list[APIKey]:
    rows = await session.scalars(select(APIKey).where(APIKey.application_id == application_id).order_by(APIKey.created_at.desc()))
    return list(rows)


async def verify_api_key(session: AsyncSession, raw_key: str) -> tuple[APIKey | None, str | None]:
    if not raw_key.startswith("sk_live_") or len(raw_key) < 30:
        return None, "invalid"
    prefix = raw_key[:16]
    key = await session.scalar(select(APIKey).where(APIKey.key_prefix == prefix))
    if not key or not api_key_matches(raw_key, key.key_hash):
        return None, "invalid"
    now = datetime.now(UTC)
    if not key.is_active or key.revoked_at:
        return None, "revoked"
    expires_at = key.expires_at
    # SQLite (used only in tests) returns naive values for timezone columns;
    # PostgreSQL preserves the UTC offset. Treat a stored naive value as UTC.
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at and expires_at <= now:
        return None, "expired"
    key.last_used_at = now
    await session.commit()
    return key, None


async def revoke_key(session: AsyncSession, key: APIKey) -> APIKey:
    key.is_active = False
    key.revoked_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(key)
    return key
