"""Signing experience API endpoints (recipient-facing, token-authenticated)."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.api.deps import get_client_ip
from dataseal.config import settings
from dataseal.database import get_db
from dataseal.models.document import Document
from dataseal.models.field import DocumentField
from dataseal.models.recipient import Recipient
from dataseal.schemas.document import PageResponse
from dataseal.schemas.field import FieldResponse, FieldValueUpdate
from dataseal.services.envelope import check_envelope_completion
from dataseal.services.signing import (
    complete_signing,
    decline_signing,
    get_recipient_by_token,
    mark_delivered,
    update_field_value,
    validate_token,
)

router = APIRouter(prefix="/signing", tags=["signing"])


async def _get_authenticated_recipient(
    token: str, db: AsyncSession, request: Request | None = None
) -> Recipient:
    """Validate signing token and return the recipient."""
    recipient = await get_recipient_by_token(db, token)
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid signing link",
        )

    error = validate_token(recipient)
    if error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )

    return recipient


@router.get("/{token}")
async def get_signing_session(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get signing session data for a recipient."""
    recipient = await _get_authenticated_recipient(token, db, request)

    ip = get_client_ip(request)
    ua = request.headers.get("User-Agent")

    # Mark as delivered on first view
    await mark_delivered(db, recipient, ip, ua)

    envelope = recipient.envelope
    documents_data = []

    for doc in envelope.documents:
        # Get fields for this recipient on this document
        result = await db.execute(
            select(DocumentField).where(
                DocumentField.document_id == doc.id,
                DocumentField.recipient_id == recipient.id,
            )
        )
        fields = result.scalars().all()

        pages = []
        for i in range(1, doc.page_count + 1):
            pages.append({
                "page_number": i,
                "image_url": f"/api/v1/signing/{token}/documents/{doc.id}/pages/{i}",
            })

        documents_data.append({
            "id": str(doc.id),
            "filename": doc.filename,
            "page_count": doc.page_count,
            "pages": pages,
            "fields": [
                {
                    "id": str(f.id),
                    "type": f.type,
                    "page_number": f.page_number,
                    "x_position": f.x_position,
                    "y_position": f.y_position,
                    "width": f.width,
                    "height": f.height,
                    "is_required": f.is_required,
                    "placeholder": f.placeholder,
                    "dropdown_options": f.dropdown_options,
                    "value": f.value,
                    "completed_at": f.completed_at.isoformat() if f.completed_at else None,
                }
                for f in fields
            ],
        })

    return {
        "envelope": {
            "id": str(envelope.id),
            "title": envelope.title,
            "message": envelope.message,
            "status": envelope.status,
        },
        "recipient": {
            "id": str(recipient.id),
            "name": recipient.name,
            "email": recipient.email,
            "status": recipient.status,
        },
        "documents": documents_data,
    }


@router.get("/{token}/documents/{doc_id}/pages", response_model=list[PageResponse])
async def get_signing_pages(
    token: str,
    doc_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    recipient = await _get_authenticated_recipient(token, db, request)

    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.envelope_id == recipient.envelope_id,
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return [
        PageResponse(
            page_number=i,
            image_url=f"/api/v1/signing/{token}/documents/{doc_id}/pages/{i}",
        )
        for i in range(1, document.page_count + 1)
    ]


@router.get("/{token}/documents/{doc_id}/pages/{page_number}")
async def get_signing_page_image(
    token: str,
    doc_id: uuid.UUID,
    page_number: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    recipient = await _get_authenticated_recipient(token, db, request)

    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.envelope_id == recipient.envelope_id,
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if page_number < 1 or page_number > document.page_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")

    page_path = (
        Path(settings.storage_local_path)
        / f"documents/{recipient.envelope_id}/{doc_id}/pages/page_{page_number}.png"
    )
    if not page_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page image not found")

    return FileResponse(str(page_path), media_type="image/png")


@router.put("/{token}/fields/{field_id}", response_model=FieldResponse)
async def submit_field_value(
    token: str,
    field_id: uuid.UUID,
    data: FieldValueUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    recipient = await _get_authenticated_recipient(token, db, request)

    result = await db.execute(
        select(DocumentField).where(
            DocumentField.id == field_id,
            DocumentField.recipient_id == recipient.id,
        )
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found or not assigned to you",
        )

    ip = get_client_ip(request)
    ua = request.headers.get("User-Agent")

    try:
        field = await update_field_value(db, field, data.value, recipient, ip, ua)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return field


@router.post("/{token}/complete")
async def complete_signing_endpoint(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    recipient = await _get_authenticated_recipient(token, db, request)

    ip = get_client_ip(request)
    ua = request.headers.get("User-Agent")

    # Reload recipient with fields
    result = await db.execute(
        select(Recipient).where(Recipient.id == recipient.id)
    )
    recipient = result.scalar_one()

    # Load fields for this recipient
    fields_result = await db.execute(
        select(DocumentField).where(DocumentField.recipient_id == recipient.id)
    )
    # Attach fields to recipient for validation
    recipient.fields = fields_result.scalars().all()

    errors = await complete_signing(db, recipient, ip, ua)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors},
        )

    # Check if envelope is complete
    from sqlalchemy.orm import selectinload

    envelope_result = await db.execute(
        select(Recipient.envelope_id).where(Recipient.id == recipient.id)
    )
    envelope_id = envelope_result.scalar_one()

    from dataseal.models.envelope import Envelope

    env_result = await db.execute(
        select(Envelope)
        .options(selectinload(Envelope.recipients))
        .where(Envelope.id == envelope_id)
    )
    envelope = env_result.scalar_one()

    is_complete = await check_envelope_completion(db, envelope)

    if is_complete:
        from dataseal.tasks.finalize import finalize_envelope
        finalize_envelope.delay(str(envelope.id))

    # Invalidate the signing token
    recipient.signing_token = None

    await db.flush()

    return {
        "status": "signed",
        "message": "Thank you for signing!",
        "envelope_complete": is_complete,
    }


@router.post("/{token}/decline")
async def decline_signing_endpoint(
    token: str,
    request: Request,
    reason: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    recipient = await _get_authenticated_recipient(token, db, request)

    ip = get_client_ip(request)
    ua = request.headers.get("User-Agent")

    await decline_signing(db, recipient, reason, ip, ua)

    from dataseal.tasks.emails import send_decline_notification
    from dataseal.tasks.webhooks import dispatch_webhook_event

    send_decline_notification.delay(str(recipient.envelope_id), str(recipient.id))
    dispatch_webhook_event.delay(str(recipient.envelope_id), "envelope.declined")

    return {
        "status": "declined",
        "message": "You have declined to sign this document.",
    }
