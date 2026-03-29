"""Recipient model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataseal.models.base import Base, TimestampMixin, UUIDMixin


class Recipient(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "recipients"

    envelope_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("envelopes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="signer")
    routing_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    signing_token: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True
    )
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    declined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    declined_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    envelope = relationship("Envelope", back_populates="recipients")
    fields = relationship("DocumentField", back_populates="recipient", lazy="selectin")

    __table_args__ = (
        Index("idx_recipients_envelope_id", "envelope_id"),
        Index(
            "idx_recipients_signing_token",
            "signing_token",
            postgresql_where="signing_token IS NOT NULL",
        ),
        Index("idx_recipients_email", "email"),
    )

    VALID_ROLES = {"signer", "cc", "in_person_signer"}
    VALID_STATUSES = {"created", "sent", "delivered", "signed", "declined"}
