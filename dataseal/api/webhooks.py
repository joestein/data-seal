"""Webhook management API endpoints."""

import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.api.deps import get_current_user, require_scope
from dataseal.database import get_db
from dataseal.models.user import User
from dataseal.models.webhook import WebhookDelivery, WebhookEndpoint
from dataseal.security.encryption import encrypt_value
from dataseal.security.url_validation import SSRFError, validate_webhook_url
from dataseal.schemas.webhook import (
    WebhookCreate,
    WebhookDeliveryResponse,
    WebhookResponse,
    WebhookUpdate,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

VALID_EVENTS = {
    "envelope.created",
    "envelope.sent",
    "envelope.delivered",
    "envelope.signed",
    "envelope.completed",
    "envelope.voided",
    "envelope.declined",
    "recipient.sent",
    "recipient.delivered",
    "recipient.signed",
    "recipient.declined",
    "*",
}


@router.post(
    "",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("write", "webhooks:write"))],
)
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate URL against SSRF
    try:
        validate_webhook_url(data.url)
    except SSRFError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook URL: {e}",
        )

    # Validate events
    for event in data.events:
        if event not in VALID_EVENTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event}",
            )

    raw_secret = secrets.token_urlsafe(32)
    webhook = WebhookEndpoint(
        user_id=current_user.id,
        url=data.url,
        secret=encrypt_value(raw_secret),
        events=data.events,
        is_active=data.is_active,
    )
    db.add(webhook)
    await db.flush()
    return webhook


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint)
        .where(WebhookEndpoint.user_id == current_user.id)
        .order_by(WebhookEndpoint.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    return webhook


@router.put(
    "/{webhook_id}",
    response_model=WebhookResponse,
    dependencies=[Depends(require_scope("write", "webhooks:write"))],
)
async def update_webhook(
    webhook_id: uuid.UUID,
    data: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    if data.url is not None:
        try:
            validate_webhook_url(data.url)
        except SSRFError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook URL: {e}",
            )
        webhook.url = data.url
    if data.events is not None:
        for event in data.events:
            if event not in VALID_EVENTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event type: {event}",
                )
        webhook.events = data.events
    if data.is_active is not None:
        webhook.is_active = data.is_active

    await db.flush()
    return webhook


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("write", "webhooks:delete"))],
)
async def delete_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    await db.delete(webhook)
    await db.flush()
    return None


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def list_deliveries(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    # Verify ownership
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    delivery_result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_endpoint_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return delivery_result.scalars().all()


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    # Create a test delivery
    test_payload = {
        "event": "test",
        "timestamp": datetime.now(UTC).isoformat(),
        "envelope_id": "00000000-0000-0000-0000-000000000000",
        "data": {
            "message": "This is a test webhook delivery from DataSeal",
        },
    }

    delivery = WebhookDelivery(
        webhook_endpoint_id=webhook.id,
        envelope_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        event_type="test",
        payload=test_payload,
    )
    db.add(delivery)
    await db.flush()

    from dataseal.tasks.webhooks import deliver_webhook
    deliver_webhook.delay(str(delivery.id))

    return {"message": "Test webhook delivery enqueued", "delivery_id": str(delivery.id)}
