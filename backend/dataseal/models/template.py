"""Template models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataseal.models.base import Base, TimestampMixin, UUIDMixin


class Template(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "templates"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="templates")
    documents = relationship(
        "TemplateDocument",
        back_populates="template",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    recipients = relationship(
        "TemplateRecipient",
        back_populates="template",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    powerforms = relationship("PowerForm", back_populates="template", lazy="noload")

    __table_args__ = (Index("idx_templates_user_id", "user_id"),)


class TemplateDocument(Base, UUIDMixin):
    __tablename__ = "template_documents"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    template = relationship("Template", back_populates="documents")
    fields = relationship(
        "TemplateField",
        back_populates="template_document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (Index("idx_template_documents_template_id", "template_id"),)


class TemplateRecipient(Base, UUIDMixin):
    __tablename__ = "template_recipients"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="signer")
    routing_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    template = relationship("Template", back_populates="recipients")

    __table_args__ = (Index("idx_template_recipients_template_id", "template_id"),)


class TemplateField(Base, UUIDMixin):
    __tablename__ = "template_fields"

    template_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("template_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("template_recipients.id", ondelete="CASCADE"), nullable=False
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    template_document = relationship("TemplateDocument", back_populates="fields")

    __table_args__ = (Index("idx_template_fields_template_document_id", "template_document_id"),)
