"""Audit event model - append-only.

This model is protected at both the application level (SQLAlchemy event listeners)
and the database level (PostgreSQL triggers in migration 002) to prevent
UPDATE and DELETE operations on audit records.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, event, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataseal.models.base import Base, UUIDMixin


class AuditEvent(Base, UUIDMixin):
    __tablename__ = "audit_events"

    envelope_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("envelopes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipients.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    envelope = relationship("Envelope", back_populates="audit_events")

    __table_args__ = (
        Index("idx_audit_events_envelope_id", "envelope_id"),
        Index("idx_audit_events_created_at", "created_at"),
    )


# Application-level protection: prevent UPDATE and DELETE on AuditEvent instances
@event.listens_for(AuditEvent, "before_update")
def _prevent_audit_update(mapper, connection, target):
    raise RuntimeError(
        "AuditEvent records are append-only and cannot be modified. "
        "This is enforced at both the application and database levels."
    )


@event.listens_for(AuditEvent, "before_delete")
def _prevent_audit_delete(mapper, connection, target):
    raise RuntimeError(
        "AuditEvent records are append-only and cannot be deleted. "
        "This is enforced at both the application and database levels."
    )
