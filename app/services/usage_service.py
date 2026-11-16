from datetime import datetime
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_log import UsageLog


async def record_usage(session: AsyncSession, api_key_id: UUID, endpoint: str, method: str, status_code: int, response_time_ms: int) -> None:
    session.add(UsageLog(api_key_id=api_key_id, endpoint=endpoint, method=method, status_code=status_code, response_time_ms=response_time_ms))
    await session.commit()


async def query_usage(session: AsyncSession, key_ids: list[UUID], skip: int, limit: int, start: datetime | None, end: datetime | None, endpoint: str | None):
    filters = [UsageLog.api_key_id.in_(key_ids)]
    if start:
        filters.append(UsageLog.created_at >= start)
    if end:
        filters.append(UsageLog.created_at <= end)
    if endpoint:
        filters.append(UsageLog.endpoint == endpoint)
    summary_query = select(func.count(), func.coalesce(func.sum(case((UsageLog.status_code < 400, 1), else_=0)), 0)).where(*filters)
    total, successful = (await session.execute(summary_query)).one()
    entries = await session.scalars(select(UsageLog).where(*filters).order_by(UsageLog.created_at.desc()).offset(skip).limit(limit))
    return int(total), int(successful), list(entries)
