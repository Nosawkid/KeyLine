from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UsageLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    api_key_id: UUID
    endpoint: str
    method: str
    status_code: int
    response_time_ms: int
    created_at: datetime


class UsageSummary(BaseModel):
    total: int
    successful: int
    failed: int
    items: list[UsageLogRead]
