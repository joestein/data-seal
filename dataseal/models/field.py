"""Document field model."""

import uuid
from datetime import datetime
from typing import ClassVar

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataseal.models.base import Base, TimestampMixin, UUIDMixin


class DocumentField(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_fields"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    x_position: Mapped[float] = mapped_column(Float, nullable=False)
    y_position: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    placeholder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    validation_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dropdown_options: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="fields")
    recipient = relationship("Recipient", back_populates="fields")

    __table_args__ = (
        Index("idx_document_fields_document_id", "document_id"),
        Index("idx_document_fields_recipient_id", "recipient_id"),
    )

    VALID_TYPES: ClassVar[set[str]] = {"signature", "initials", "date_signed", "text", "checkbox", "dropdown"}
