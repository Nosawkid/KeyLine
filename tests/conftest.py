import os

os.environ.update({
    "JWT_SECRET": "test-jwt-secret-that-is-long-enough",
    "API_KEY_HMAC_SECRET": "test-hmac-secret-that-is-long-enough",
    "DATABASE_URL": "sqlite+aiosqlite:///./test_api_keys.db",
    "REDIS_URL": "redis://unused",
    "RATE_LIMIT_PER_MINUTE": "2",
})

import pytest_asyncio
from fakeredis.aioredis import FakeRedis
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.session import get_db
from app.main import app
from app.models.base import Base
import app.main as main_module

get_settings.cache_clear()
test_engine = create_async_engine(os.environ["DATABASE_URL"])
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def database():
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    fake_redis = FakeRedis(decode_responses=True)
    main_module.from_url = lambda *args, **kwargs: fake_redis

    async def override_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    await fake_redis.aclose()
