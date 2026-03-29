"""User and API key models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataseal.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    envelopes = relationship("Envelope", back_populates="user", lazy="selectin")
    api_keys = relationship("ApiKey", back_populates="user", lazy="selectin")
    templates = relationship("Template", back_populates="user", lazy="selectin")
    webhook_endpoints = relationship("WebhookEndpoint", back_populates="user", lazy="selectin")
    powerforms = relationship("PowerForm", back_populates="user", lazy="selectin")
    oauth_apps = relationship("OAuthApp", back_populates="user", lazy="selectin")

    __table_args__ = (Index("idx_users_email", "email"),)


class ApiKey(Base, UUIDMixin):
    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    scopes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: ["*"])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index("idx_api_keys_key_prefix", "key_prefix"),
        Index("idx_api_keys_user_id", "user_id"),
    )
