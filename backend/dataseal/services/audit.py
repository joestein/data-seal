"""Audit trail service - append-only event logging."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.models.audit import AuditEvent


async def create_audit_event(
    db: AsyncSession,
    *,
    envelope_id: uuid.UUID,
    event_type: str,
    description: str,
    recipient_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> AuditEvent:
    """Create an append-only audit event."""
    event = AuditEvent(
        envelope_id=envelope_id,
        recipient_id=recipient_id,
        user_id=user_id,
        event_type=event_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_=metadata,
    )
    db.add(event)
    await db.flush()
    return event
