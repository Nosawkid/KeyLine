from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "API Key Management Service"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://apikey:apikey@db:5432/apikey_management"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = Field(min_length=16)
    api_key_hmac_secret: str = Field(min_length=16)
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"
    rate_limit_per_minute: int = 100

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DATABASE_URL is missing")

        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql://", 1)

        if value.startswith("postgresql://"):
            value = value.replace(
                "postgresql://",
                "postgresql+asyncpg://",
                1
            )

        return value
    
    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("REDIS_URL is missing or empty")

        if not value.startswith(("redis://", "rediss://", "unix://")):
            raise ValueError("REDIS_URL must start with redis://, rediss://, or unix://")

        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
