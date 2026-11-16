from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application


async def get_owned_application(session: AsyncSession, application_id: UUID, user_id: UUID) -> Application | None:
    return await session.scalar(select(Application).where(Application.id == application_id, Application.user_id == user_id))


async def list_applications(session: AsyncSession, user_id: UUID) -> list[Application]:
    result = await session.scalars(select(Application).where(Application.user_id == user_id).order_by(Application.created_at.desc()))
    return list(result)
