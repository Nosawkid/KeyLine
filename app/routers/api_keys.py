from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.core.dependencies import CurrentUser, DBSession
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyCreated, APIKeyRead, APIKeyUpdate
from app.services.api_key_service import create_api_key, get_owned_key, list_application_keys, revoke_key
from app.services.application_service import get_owned_application

router = APIRouter(tags=["API Keys"])


@router.post("/applications/{application_id}/keys", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED, summary="Create an API key (shown once)")
async def create_key(application_id: UUID, payload: APIKeyCreate, session: DBSession, user: CurrentUser) -> APIKeyCreated:
    app = await get_owned_application(session, application_id, user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    try:
        key, plaintext = await create_api_key(session, app.id, payload.name, payload.expires_at)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return APIKeyCreated(**APIKeyRead.model_validate(key).model_dump(), api_key=plaintext)


@router.get("/applications/{application_id}/keys", response_model=list[APIKeyRead])
async def get_application_keys(application_id: UUID, session: DBSession, user: CurrentUser) -> list[APIKey]:
    app = await get_owned_application(session, application_id, user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return await list_application_keys(session, app.id)


@router.get("/keys/{key_id}", response_model=APIKeyRead)
async def get_key(key_id: UUID, session: DBSession, user: CurrentUser) -> APIKey:
    key = await get_owned_key(session, key_id, user.id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key


@router.patch("/keys/{key_id}", response_model=APIKeyRead)
async def update_key(key_id: UUID, payload: APIKeyUpdate, session: DBSession, user: CurrentUser) -> APIKey:
    key = await get_owned_key(session, key_id, user.id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_active") is False:
        await revoke_key(session, key)
    else:
        if "name" in changes:
            key.name = changes["name"]
        if changes.get("is_active") is True and key.revoked_at:
            raise HTTPException(status_code=409, detail="Revoked API keys cannot be reactivated")
        await session.commit()
        await session.refresh(key)
    return key


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke an API key")
async def delete_key(key_id: UUID, session: DBSession, user: CurrentUser) -> Response:
    key = await get_owned_key(session, key_id, user.id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    await revoke_key(session, key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
