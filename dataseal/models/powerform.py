"""PowerForm model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataseal.models.base import Base, TimestampMixin, UUIDMixin


class PowerForm(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "powerforms"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user = relationship("User", back_populates="powerforms")
    template = relationship("Template", back_populates="powerforms")

    __table_args__ = (
        Index("idx_powerforms_slug", "slug"),
        Index("idx_powerforms_user_id", "user_id"),
    )
