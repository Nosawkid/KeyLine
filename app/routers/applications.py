from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.core.dependencies import CurrentUser, DBSession
from app.models.application import Application
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationUpdate
from app.services.application_service import get_owned_application, list_applications

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(payload: ApplicationCreate, session: DBSession, user: CurrentUser) -> Application:
    app = Application(user_id=user.id, **payload.model_dump())
    session.add(app)
    await session.commit()
    await session.refresh(app)
    return app


@router.get("", response_model=list[ApplicationRead])
async def get_applications(session: DBSession, user: CurrentUser) -> list[Application]:
    return await list_applications(session, user.id)


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(application_id: UUID, session: DBSession, user: CurrentUser) -> Application:
    app = await get_owned_application(session, application_id, user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application(application_id: UUID, payload: ApplicationUpdate, session: DBSession, user: CurrentUser) -> Application:
    app = await get_owned_application(session, application_id, user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(app, field, value)
    await session.commit()
    await session.refresh(app)
    return app


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(application_id: UUID, session: DBSession, user: CurrentUser) -> Response:
    app = await get_owned_application(session, application_id, user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    await session.delete(app)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
