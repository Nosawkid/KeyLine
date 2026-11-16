from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class UsageLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "usage_logs"

    api_key_id: Mapped[UUID] = mapped_column(ForeignKey("api_keys.id", ondelete="CASCADE"), index=True, nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    method: Mapped[str] = mapped_column(String(12), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now().astimezone(), index=True)
    api_key = relationship("APIKey", back_populates="usage_logs")
