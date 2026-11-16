from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DBSession
from app.models.api_key import APIKey
from app.schemas.usage import UsageSummary
from app.services.api_key_service import get_owned_key
from app.services.application_service import get_owned_application
from app.services.usage_service import query_usage

router = APIRouter(tags=["Usage"])


async def _usage(session: DBSession, key_ids: list[UUID], skip: int, limit: int, start: datetime | None, end: datetime | None, endpoint: str | None) -> UsageSummary:
    total, successful, items = await query_usage(session, key_ids, skip, limit, start, end, endpoint)
    return UsageSummary(total=total, successful=successful, failed=total - successful, items=items)


@router.get("/applications/{application_id}/usage", response_model=UsageSummary)
async def application_usage(application_id: UUID, session: DBSession, user: CurrentUser, skip: int = 0, limit: int = Query(50, le=100), start: datetime | None = None, end: datetime | None = None, endpoint: str | None = None) -> UsageSummary:
    app = await get_owned_application(session, application_id, user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    key_ids = list(await session.scalars(select(APIKey.id).where(APIKey.application_id == app.id)))
    return await _usage(session, key_ids, skip, limit, start, end, endpoint)


@router.get("/keys/{key_id}/usage", response_model=UsageSummary)
async def key_usage(key_id: UUID, session: DBSession, user: CurrentUser, skip: int = 0, limit: int = Query(50, le=100), start: datetime | None = None, end: datetime | None = None, endpoint: str | None = None) -> UsageSummary:
    key = await get_owned_key(session, key_id, user.id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return await _usage(session, [key.id], skip, limit, start, end, endpoint)
