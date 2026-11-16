from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from redis.asyncio import from_url

from app.core.config import get_settings
from app.middleware.request_logging import UsageLoggingMiddleware
from app.routers import api_keys, applications, auth, protected, usage


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = from_url(get_settings().redis_url, decode_responses=True)
    yield
    await app.state.redis.aclose()


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", description="Secure, multi-tenant API key management with usage analytics.", lifespan=lifespan)
app.add_middleware(UsageLoggingMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["Authorization", "Content-Type"])
app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(api_keys.router)
app.include_router(usage.router)
app.include_router(protected.router)

frontend_dir = Path(__file__).parent / "frontend"
app.mount("/assets", StaticFiles(directory=frontend_dir), name="assets")


@app.get("/", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/health", tags=["Operations"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
