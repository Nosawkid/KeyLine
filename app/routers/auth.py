from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token
from app.core.dependencies import CurrentUser, DBSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Create an account")
async def register(payload: RegisterRequest, session: DBSession) -> TokenResponse:
    try:
        user = await register_user(session, payload.email, payload.password)
    except ValueError:
        raise HTTPException(status_code=409, detail="Email is already registered")
    return TokenResponse(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenResponse, summary="Log in and receive a JWT")
async def login(payload: LoginRequest, session: DBSession) -> TokenResponse:
    user = await authenticate_user(session, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    return TokenResponse(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead, summary="Get the authenticated user")
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
