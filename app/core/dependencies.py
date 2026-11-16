from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.api_key import APIKey
from app.models.user import User
from app.services.api_key_service import verify_api_key
from app.services.rate_limit_service import RateLimitExceeded, enforce_rate_limit

bearer_scheme = HTTPBearer(auto_error=False)
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)], session: DBSession) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    user = await session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_api_key_principal(request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)], session: DBSession) -> APIKey:
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required", headers={"WWW-Authenticate": "Bearer"})
    api_key, reason = await verify_api_key(session, credentials.credentials)
    if not api_key:
        status_code = 403 if reason in {"revoked", "expired"} else 401
        raise HTTPException(status_code=status_code, detail="API key rejected")
    # Store the verified principal before limiting so a 429 is also accounted for.
    request.state.api_key = api_key
    try:
        remaining, reset = await enforce_rate_limit(request.app.state.redis, api_key.id)
    except RateLimitExceeded as error:
        request.state.rate_limit_remaining = 0
        request.state.rate_limit_reset = error.retry_after
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": str(error.retry_after)})
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset
    return api_key


APIKeyPrincipal = Annotated[APIKey, Depends(get_api_key_principal)]
