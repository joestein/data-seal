"""Recipient management API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.api.deps import get_envelope_dep
from dataseal.database import get_db
from dataseal.models.envelope import Envelope
from dataseal.models.recipient import Recipient
from dataseal.schemas.recipient import RecipientCreate, RecipientResponse, RecipientUpdate

router = APIRouter(prefix="/envelopes/{envelope_id}/recipients", tags=["recipients"])


@router.post("", response_model=list[RecipientResponse], status_code=status.HTTP_201_CREATED)
async def add_recipients(
    data: RecipientCreate | list[RecipientCreate],
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add recipients after envelope has been sent",
        )

    # Accept single or list
    items = data if isinstance(data, list) else [data]
    recipients = []

    for item in items:
        recipient = Recipient(
            envelope_id=envelope.id,
            name=item.name,
            email=item.email,
            role=item.role,
            routing_order=item.routing_order,
        )
        db.add(recipient)
        recipients.append(recipient)

    await db.flush()
    return recipients


@router.get("", response_model=list[RecipientResponse])
async def list_recipients(
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recipient)
        .where(Recipient.envelope_id == envelope.id)
        .order_by(Recipient.routing_order, Recipient.created_at)
    )
    return result.scalars().all()


@router.put("/{recipient_id}", response_model=RecipientResponse)
async def update_recipient(
    recipient_id: uuid.UUID,
    data: RecipientUpdate,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update recipients after envelope has been sent",
        )

    result = await db.execute(
        select(Recipient).where(
            Recipient.id == recipient_id, Recipient.envelope_id == envelope.id
        )
    )
    recipient = result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    if data.name is not None:
        recipient.name = data.name
    if data.email is not None:
        recipient.email = data.email
    if data.role is not None:
        recipient.role = data.role
    if data.routing_order is not None:
        recipient.routing_order = data.routing_order

    await db.flush()
    return recipient


@router.delete("/{recipient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipient(
    recipient_id: uuid.UUID,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove recipients after envelope has been sent",
        )

    result = await db.execute(
        select(Recipient).where(
            Recipient.id == recipient_id, Recipient.envelope_id == envelope.id
        )
    )
    recipient = result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    await db.delete(recipient)
    await db.flush()
    return None
