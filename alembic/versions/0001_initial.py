"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-16
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("hashed_password", sa.String(512), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("applications", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("description", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_table("api_keys", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("application_id", sa.Uuid(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("key_prefix", sa.String(32), nullable=False), sa.Column("key_hash", sa.String(64), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True), sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True), sa.UniqueConstraint("key_hash"))
    op.create_index("ix_api_keys_application_id", "api_keys", ["application_id"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])
    op.create_index("ix_api_keys_expires_at", "api_keys", ["expires_at"])
    op.create_table("usage_logs", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("api_key_id", sa.Uuid(), sa.ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False), sa.Column("endpoint", sa.String(255), nullable=False), sa.Column("method", sa.String(12), nullable=False), sa.Column("status_code", sa.Integer(), nullable=False), sa.Column("response_time_ms", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_usage_logs_api_key_id", "usage_logs", ["api_key_id"])
    op.create_index("ix_usage_logs_endpoint", "usage_logs", ["endpoint"])
    op.create_index("ix_usage_logs_created_at", "usage_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("usage_logs")
    op.drop_table("api_keys")
    op.drop_table("applications")
    op.drop_table("users")
