"""Envelope API endpoints."""

from datetime import UTC
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.api.deps import get_client_ip, get_current_user, get_envelope_dep, require_scope
from dataseal.config import settings
from dataseal.database import get_db
from dataseal.models.audit import AuditEvent
from dataseal.models.envelope import Envelope
from dataseal.models.user import User
from dataseal.schemas.envelope import (
    EnvelopeCreate,
    EnvelopeListResponse,
    EnvelopeResponse,
    EnvelopeUpdate,
    SendResponse,
    VoidRequest,
)
from dataseal.services.audit import create_audit_event
from dataseal.services.envelope import send_envelope, validate_envelope_for_sending

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


@router.post(
    "",
    response_model=EnvelopeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("write", "envelopes:write"))],
)
async def create_envelope(
    data: EnvelopeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    envelope = Envelope(
        user_id=current_user.id,
        title=data.title,
        message=data.message,
        expires_at=data.expires_at,
    )
    db.add(envelope)
    await db.flush()

    await create_audit_event(
        db,
        envelope_id=envelope.id,
        user_id=current_user.id,
        event_type="envelope.created",
        description=f"Envelope '{envelope.title}' created",
        ip_address=get_client_ip(request) if request else None,
    )

    return envelope


@router.get("", response_model=EnvelopeListResponse)
async def list_envelopes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = select(Envelope).where(Envelope.user_id == current_user.id)
    count_query = select(func.count()).select_from(Envelope).where(Envelope.user_id == current_user.id)

    if status_filter:
        query = query.where(Envelope.status == status_filter)
        count_query = count_query.where(Envelope.status == status_filter)

    if search:
        query = query.where(Envelope.title.ilike(f"%{search}%"))
        count_query = count_query.where(Envelope.title.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Envelope.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    envelopes = result.scalars().all()

    return EnvelopeListResponse(
        items=envelopes,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{envelope_id}", response_model=EnvelopeResponse)
async def get_envelope(envelope: Envelope = Depends(get_envelope_dep)):
    return envelope


@router.put("/{envelope_id}", response_model=EnvelopeResponse)
async def update_envelope(
    data: EnvelopeUpdate,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update envelope after it has been sent",
        )

    if data.title is not None:
        envelope.title = data.title
    if data.message is not None:
        envelope.message = data.message
    if data.expires_at is not None:
        envelope.expires_at = data.expires_at

    await db.flush()
    return envelope


@router.delete(
    "/{envelope_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("write", "envelopes:delete"))],
)
async def delete_envelope(
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete envelope after it has been sent",
        )
    await db.delete(envelope)
    await db.flush()


@router.post(
    "/{envelope_id}/send",
    response_model=SendResponse,
    dependencies=[Depends(require_scope("write", "envelopes:send"))],
)
async def send_envelope_endpoint(
    envelope: Envelope = Depends(get_envelope_dep),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    errors = await validate_envelope_for_sending(db, envelope)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors},
        )

    ip = get_client_ip(request) if request else None
    ua = request.headers.get("User-Agent") if request else None

    await send_envelope(db, envelope, current_user.id, ip, ua)

    # Enqueue email sending
    from dataseal.tasks.emails import send_signing_emails
    from dataseal.tasks.webhooks import dispatch_webhook_event

    send_signing_emails.delay(str(envelope.id))
    dispatch_webhook_event.delay(str(envelope.id), "envelope.sent")

    return SendResponse(
        id=envelope.id,
        status=envelope.status,
        message="Envelope sent successfully",
    )


@router.post(
    "/{envelope_id}/void",
    response_model=EnvelopeResponse,
    dependencies=[Depends(require_scope("write", "envelopes:void"))],
)
async def void_envelope(
    data: VoidRequest,
    envelope: Envelope = Depends(get_envelope_dep),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    if not envelope.can_transition_to("voided"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot void envelope in '{envelope.status}' status",
        )

    envelope.status = "voided"
    envelope.voided_reason = data.reason

    await create_audit_event(
        db,
        envelope_id=envelope.id,
        user_id=current_user.id,
        event_type="envelope.voided",
        description=f"Envelope voided: {data.reason}",
        ip_address=get_client_ip(request) if request else None,
    )

    # Invalidate all signing tokens
    for recipient in envelope.recipients:
        recipient.signing_token = None

    await db.flush()

    from dataseal.tasks.emails import send_void_notification
    from dataseal.tasks.webhooks import dispatch_webhook_event

    send_void_notification.delay(str(envelope.id))
    dispatch_webhook_event.delay(str(envelope.id), "envelope.voided")

    return envelope


@router.post("/{envelope_id}/resend", response_model=SendResponse)
async def resend_envelope(
    envelope: Envelope = Depends(get_envelope_dep),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    if envelope.status not in ("sent", "delivered"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only resend envelopes that are sent or delivered",
        )

    # Regenerate tokens for recipients who haven't signed
    import secrets
    from datetime import datetime, timedelta

    expiry = datetime.now(UTC) + timedelta(hours=settings.signing_token_expiry_hours)

    for recipient in envelope.recipients:
        if recipient.status in ("sent", "delivered", "created") and recipient.role != "cc":
            recipient.signing_token = secrets.token_urlsafe(64)
            recipient.token_expires_at = expiry

    await db.flush()

    from dataseal.tasks.emails import send_signing_emails

    send_signing_emails.delay(str(envelope.id))

    return SendResponse(
        id=envelope.id,
        status=envelope.status,
        message="Signing emails resent",
    )


@router.get("/{envelope_id}/audit-trail")
async def get_audit_trail(
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditEvent).where(AuditEvent.envelope_id == envelope.id).order_by(AuditEvent.created_at)
    )
    events = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "description": e.description,
            "ip_address": e.ip_address,
            "user_agent": e.user_agent,
            "metadata": e.metadata_,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/{envelope_id}/certificate")
async def download_certificate(
    envelope: Envelope = Depends(get_envelope_dep),
):
    if envelope.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate is only available for completed envelopes",
        )

    cert_path = Path(settings.storage_local_path) / "documents" / str(envelope.id) / "completed" / "certificate.pdf"
    if not cert_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    return FileResponse(
        str(cert_path),
        media_type="application/pdf",
        filename=f"certificate_{envelope.id}.pdf",
    )


@router.get("/{envelope_id}/combined")
async def download_combined(
    envelope: Envelope = Depends(get_envelope_dep),
):
    if envelope.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Combined document is only available for completed envelopes",
        )

    final_path = Path(settings.storage_local_path) / "documents" / str(envelope.id) / "completed" / "final.pdf"
    if not final_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return FileResponse(
        str(final_path),
        media_type="application/pdf",
        filename=f"{envelope.title}_completed.pdf",
    )
