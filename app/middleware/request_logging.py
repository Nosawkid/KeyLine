import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.session import SessionLocal
from app.services.usage_service import record_usage


class UsageLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        api_key = getattr(request.state, "api_key", None)
        if api_key:
            response.headers["X-RateLimit-Remaining"] = str(getattr(request.state, "rate_limit_remaining", 0))
            response.headers["X-RateLimit-Reset"] = str(getattr(request.state, "rate_limit_reset", 0))
            try:
                async with SessionLocal() as session:
                    await record_usage(session, api_key.id, request.url.path, request.method, response.status_code, int((time.perf_counter() - start) * 1000))
            except Exception:
                # Usage accounting must never turn an otherwise successful request into an error.
                pass
        return response
