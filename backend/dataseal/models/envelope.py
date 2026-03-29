"""Envelope model."""

import uuid
from datetime import datetime
from typing import ClassVar

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataseal.models.base import Base, TimestampMixin, UUIDMixin


class Envelope(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "envelopes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )
    powerform_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("powerforms.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    voided_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Relationships
    user = relationship("User", back_populates="envelopes")
    documents = relationship("Document", back_populates="envelope", cascade="all, delete-orphan", lazy="selectin")
    recipients = relationship("Recipient", back_populates="envelope", cascade="all, delete-orphan", lazy="selectin")
    audit_events = relationship("AuditEvent", back_populates="envelope", cascade="all, delete-orphan", lazy="noload")

    __table_args__ = (
        Index("idx_envelopes_user_id", "user_id"),
        Index("idx_envelopes_status", "status"),
        Index("idx_envelopes_created_at", "created_at"),
    )

    VALID_STATUSES: ClassVar[set[str]] = {"created", "sent", "delivered", "signed", "completed", "voided", "declined"}

    ALLOWED_TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        "created": {"sent", "voided"},
        "sent": {"delivered", "voided", "declined"},
        "delivered": {"signed", "voided", "declined"},
        "signed": {"completed", "voided", "declined"},
        "completed": set(),
        "voided": set(),
        "declined": set(),
    }

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())
