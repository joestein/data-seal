"""Document field placement API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.api.deps import get_envelope_dep
from dataseal.database import get_db
from dataseal.models.document import Document
from dataseal.models.envelope import Envelope
from dataseal.models.field import DocumentField
from dataseal.models.recipient import Recipient
from dataseal.schemas.field import FieldCreate, FieldResponse, FieldUpdate

router = APIRouter(
    prefix="/envelopes/{envelope_id}/documents/{doc_id}/fields", tags=["fields"]
)


async def _get_document(
    envelope_id: uuid.UUID, doc_id: uuid.UUID, db: AsyncSession
) -> Document:
    result = await db.execute(
        select(Document).where(
            Document.id == doc_id, Document.envelope_id == envelope_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("", response_model=list[FieldResponse], status_code=status.HTTP_201_CREATED)
async def add_fields(
    envelope_id: uuid.UUID,
    doc_id: uuid.UUID,
    data: FieldCreate | list[FieldCreate],
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add fields after envelope has been sent",
        )

    await _get_document(envelope_id, doc_id, db)

    items = data if isinstance(data, list) else [data]
    fields = []

    for item in items:
        # Validate recipient belongs to this envelope
        r_result = await db.execute(
            select(Recipient).where(
                Recipient.id == item.recipient_id,
                Recipient.envelope_id == envelope_id,
            )
        )
        if not r_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recipient {item.recipient_id} not found in this envelope",
            )

        field = DocumentField(
            document_id=doc_id,
            recipient_id=item.recipient_id,
            type=item.type,
            page_number=item.page_number,
            x_position=item.x_position,
            y_position=item.y_position,
            width=item.width,
            height=item.height,
            is_required=item.is_required,
            placeholder=item.placeholder,
            validation_rule=item.validation_rule,
            dropdown_options=item.dropdown_options,
        )
        db.add(field)
        fields.append(field)

    await db.flush()
    return fields


@router.get("", response_model=list[FieldResponse])
async def list_fields(
    envelope_id: uuid.UUID,
    doc_id: uuid.UUID,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    await _get_document(envelope_id, doc_id, db)

    result = await db.execute(
        select(DocumentField)
        .where(DocumentField.document_id == doc_id)
        .order_by(DocumentField.page_number, DocumentField.y_position)
    )
    return result.scalars().all()


@router.put("/{field_id}", response_model=FieldResponse)
async def update_field(
    envelope_id: uuid.UUID,
    doc_id: uuid.UUID,
    field_id: uuid.UUID,
    data: FieldUpdate,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update fields after envelope has been sent",
        )

    result = await db.execute(
        select(DocumentField).where(
            DocumentField.id == field_id, DocumentField.document_id == doc_id
        )
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    for attr in ("page_number", "x_position", "y_position", "width", "height", "is_required", "placeholder", "validation_rule", "dropdown_options"):
        val = getattr(data, attr, None)
        if val is not None:
            setattr(field, attr, val)

    await db.flush()
    return field


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(
    envelope_id: uuid.UUID,
    doc_id: uuid.UUID,
    field_id: uuid.UUID,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove fields after envelope has been sent",
        )

    result = await db.execute(
        select(DocumentField).where(
            DocumentField.id == field_id, DocumentField.document_id == doc_id
        )
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    await db.delete(field)
    await db.flush()
    return None
