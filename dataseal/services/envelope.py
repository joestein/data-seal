"""Envelope business logic service."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.config import settings
from dataseal.models.envelope import Envelope
from dataseal.models.recipient import Recipient
from dataseal.services.audit import create_audit_event


async def validate_envelope_for_sending(
    db: AsyncSession, envelope: Envelope
) -> list[str]:
    """Validate an envelope is ready to be sent. Returns list of error messages."""
    errors = []

    if envelope.status != "created":
        errors.append(f"Envelope must be in 'created' status, currently '{envelope.status}'")

    if not envelope.documents:
        errors.append("Envelope must have at least one document")

    signers = [r for r in envelope.recipients if r.role == "signer"]
    if not signers:
        errors.append("Envelope must have at least one signer")

    # Check that all signers have at least one field assigned
    for signer in signers:
        has_fields = False
        for doc in envelope.documents:
            for field in doc.fields:
                if field.recipient_id == signer.id:
                    has_fields = True
                    break
            if has_fields:
                break
        if not has_fields:
            errors.append(f"Signer '{signer.name}' has no fields assigned")

    return errors


async def send_envelope(
    db: AsyncSession,
    envelope: Envelope,
    user_id: uuid.UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Envelope:
    """Send an envelope - update status, generate tokens, create audit events."""
    envelope.status = "sent"

    await create_audit_event(
        db,
        envelope_id=envelope.id,
        user_id=user_id,
        event_type="envelope.sent",
        description=f"Envelope '{envelope.title}' sent for signing",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Generate signing tokens for the first routing group
    await generate_tokens_for_current_group(db, envelope)

    await db.flush()
    return envelope


async def generate_tokens_for_current_group(
    db: AsyncSession, envelope: Envelope
) -> list[Recipient]:
    """Generate signing tokens for recipients in the current routing order group."""
    signers = [r for r in envelope.recipients if r.role in ("signer", "in_person_signer")]
    if not signers:
        return []

    # Find the minimum routing_order among unsent signers
    unsent = [r for r in signers if r.status == "created"]
    if not unsent:
        return []

    min_order = min(r.routing_order for r in unsent)
    current_group = [r for r in unsent if r.routing_order == min_order]

    expiry = datetime.now(UTC) + timedelta(hours=settings.signing_token_expiry_hours)

    for recipient in current_group:
        recipient.signing_token = secrets.token_urlsafe(64)
        recipient.token_expires_at = expiry
        recipient.status = "sent"

    # Also mark CC recipients as sent
    for recipient in envelope.recipients:
        if recipient.role == "cc" and recipient.status == "created":
            recipient.status = "sent"

    await db.flush()
    return current_group


async def check_envelope_completion(
    db: AsyncSession, envelope: Envelope
) -> bool:
    """Check if all signers have signed and update envelope status accordingly."""
    signers = [r for r in envelope.recipients if r.role in ("signer", "in_person_signer")]

    all_signed = all(r.status == "signed" for r in signers)
    any_signed = any(r.status == "signed" for r in signers)

    if all_signed:
        envelope.status = "completed"
        envelope.completed_at = datetime.now(UTC)
        await db.flush()
        return True

    # Check if we need to advance to the next routing group
    if any_signed:
        # Update envelope status to 'signed' if not already
        if envelope.status not in ("signed", "completed"):
            envelope.status = "signed"
            await db.flush()

        # Check if current group is all done
        current_signers = [r for r in signers if r.status in ("sent", "delivered")]
        if not current_signers:
            # Current group is done, advance to next
            next_group = await generate_tokens_for_current_group(db, envelope)
            if next_group:
                return False  # More groups to go

    return False
