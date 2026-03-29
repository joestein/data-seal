"""Signing service - handles the recipient signing experience."""

import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dataseal.models.envelope import Envelope
from dataseal.models.field import DocumentField
from dataseal.models.recipient import Recipient
from dataseal.services.audit import create_audit_event


async def get_recipient_by_token(
    db: AsyncSession, token: str
) -> Recipient | None:
    """Look up a recipient by their signing token."""
    result = await db.execute(
        select(Recipient)
        .options(selectinload(Recipient.envelope).selectinload(Envelope.documents))
        .where(Recipient.signing_token == token)
    )
    return result.scalar_one_or_none()


def validate_token(recipient: Recipient) -> str | None:
    """Validate a signing token. Returns error message or None if valid."""
    if recipient.status in ("signed", "declined"):
        return "This signing session has already been completed"

    if recipient.token_expires_at:
        expires = recipient.token_expires_at
        # Handle both timezone-aware and timezone-naive datetimes
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            return "This signing link has expired. Please contact the sender for a new link."

    return None


async def mark_delivered(
    db: AsyncSession,
    recipient: Recipient,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Mark a recipient as having viewed the document."""
    if recipient.status == "sent":
        recipient.status = "delivered"
        recipient.ip_address = ip_address
        recipient.user_agent = user_agent

        await create_audit_event(
            db,
            envelope_id=recipient.envelope_id,
            recipient_id=recipient.id,
            event_type="recipient.document_viewed",
            description=f"{recipient.name} viewed the document",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Update envelope status if first delivery
        envelope = recipient.envelope
        if envelope.status == "sent":
            envelope.status = "delivered"

        await db.flush()


async def update_field_value(
    db: AsyncSession,
    field: DocumentField,
    value: str,
    recipient: Recipient,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> DocumentField:
    """Update a field value during signing."""
    # Validate the value based on field type
    if field.type == "checkbox":
        if value not in ("true", "false"):
            raise ValueError("Checkbox value must be 'true' or 'false'")
    elif field.type == "dropdown":
        if field.dropdown_options and value not in field.dropdown_options:
            raise ValueError(f"Value must be one of: {field.dropdown_options}")
    elif field.type == "date_signed":
        # Auto-set to current date
        value = datetime.now(UTC).strftime("%Y-%m-%d")
    elif field.validation_rule:
        if not re.match(field.validation_rule, value):
            raise ValueError("Value does not match validation rule")

    field.value = value
    field.completed_at = datetime.now(UTC)

    await create_audit_event(
        db,
        envelope_id=recipient.envelope_id,
        recipient_id=recipient.id,
        event_type="recipient.field_completed",
        description=f"{recipient.name} completed a {field.type} field",
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"field_id": str(field.id), "field_type": field.type},
    )

    await db.flush()
    return field


async def complete_signing(
    db: AsyncSession,
    recipient: Recipient,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> list[str]:
    """Complete signing for a recipient. Returns list of errors if any."""
    errors = []

    # Validate all required fields are completed
    for field in recipient.fields:
        if field.is_required and field.value is None:
            errors.append(f"Required field on page {field.page_number} is not completed")

    if errors:
        return errors

    recipient.status = "signed"
    recipient.signed_at = datetime.now(UTC)
    recipient.ip_address = ip_address
    recipient.user_agent = user_agent

    await create_audit_event(
        db,
        envelope_id=recipient.envelope_id,
        recipient_id=recipient.id,
        event_type="recipient.signed",
        description=f"{recipient.name} completed signing",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await db.flush()
    return []


async def decline_signing(
    db: AsyncSession,
    recipient: Recipient,
    reason: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Decline signing for a recipient."""
    recipient.status = "declined"
    recipient.declined_at = datetime.now(UTC)
    recipient.declined_reason = reason
    recipient.signing_token = None  # Invalidate token

    await create_audit_event(
        db,
        envelope_id=recipient.envelope_id,
        recipient_id=recipient.id,
        event_type="recipient.declined",
        description=f"{recipient.name} declined to sign: {reason or 'No reason given'}",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Update envelope status
    envelope = recipient.envelope
    if envelope.can_transition_to("declined"):
        envelope.status = "declined"

    await db.flush()
