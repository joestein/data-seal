"""Template management API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extensions import uuid7

from dataseal.api.deps import get_current_user
from dataseal.database import get_db
from dataseal.models.document import Document
from dataseal.models.envelope import Envelope
from dataseal.models.field import DocumentField
from dataseal.models.recipient import Recipient
from dataseal.models.template import Template, TemplateDocument, TemplateField, TemplateRecipient
from dataseal.models.user import User
from dataseal.schemas.template import (
    CreateEnvelopeFromTemplate,
    TemplateCreate,
    TemplateDocumentResponse,
    TemplateFieldCreate,
    TemplateFieldResponse,
    TemplateRecipientCreate,
    TemplateRecipientResponse,
    TemplateResponse,
    TemplateUpdate,
)
from dataseal.storage import storage

router = APIRouter(prefix="/templates", tags=["templates"])


async def _get_template(template_id: uuid.UUID, user: User, db: AsyncSession) -> Template:
    result = await db.execute(select(Template).where(Template.id == template_id, Template.user_id == user.id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = Template(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
    )
    db.add(template)
    await db.flush()
    return template


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Template).where(Template.user_id == current_user.id).order_by(Template.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_template(template_id, current_user, db)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await _get_template(template_id, current_user, db)

    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description
    if data.is_active is not None:
        template.is_active = data.is_active

    await db.flush()
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await _get_template(template_id, current_user, db)
    await db.delete(template)
    await db.flush()


@router.post(
    "/{template_id}/documents",
    response_model=TemplateDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_template_document(
    template_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await _get_template(template_id, current_user, db)

    content = await file.read()

    # Validate PDF
    if not content[:4].startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    doc_id = uuid7()
    storage_path = f"templates/{template_id}/{doc_id}/original.pdf"
    await storage.save(storage_path, content)

    doc_count = len(template.documents) if template.documents else 0

    template_doc = TemplateDocument(
        id=doc_id,
        template_id=template_id,
        filename=file.filename or "document.pdf",
        storage_path=storage_path,
        content_type="application/pdf",
        size_bytes=len(content),
        page_count=0,
        display_order=doc_count,
    )
    db.add(template_doc)
    await db.flush()

    # Render pages
    from dataseal.tasks.documents import render_document_pages

    render_document_pages.delay(str(doc_id))

    return template_doc


@router.post(
    "/{template_id}/recipients",
    response_model=TemplateRecipientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_template_recipient(
    template_id: uuid.UUID,
    data: TemplateRecipientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_template(template_id, current_user, db)

    recipient = TemplateRecipient(
        template_id=template_id,
        role_name=data.role_name,
        role=data.role,
        routing_order=data.routing_order,
    )
    db.add(recipient)
    await db.flush()
    return recipient


@router.post(
    "/{template_id}/documents/{doc_id}/fields",
    response_model=TemplateFieldResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_template_field(
    template_id: uuid.UUID,
    doc_id: uuid.UUID,
    data: TemplateFieldCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_template(template_id, current_user, db)

    # Validate template document exists
    doc_result = await db.execute(
        select(TemplateDocument).where(
            TemplateDocument.id == doc_id,
            TemplateDocument.template_id == template_id,
        )
    )
    if not doc_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template document not found")

    # Validate template recipient exists
    r_result = await db.execute(
        select(TemplateRecipient).where(
            TemplateRecipient.id == data.template_recipient_id,
            TemplateRecipient.template_id == template_id,
        )
    )
    if not r_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template recipient not found",
        )

    field = TemplateField(
        template_document_id=doc_id,
        template_recipient_id=data.template_recipient_id,
        type=data.type,
        page_number=data.page_number,
        x_position=data.x_position,
        y_position=data.y_position,
        width=data.width,
        height=data.height,
        is_required=data.is_required,
        placeholder=data.placeholder,
        validation_rule=data.validation_rule,
        dropdown_options=data.dropdown_options,
    )
    db.add(field)
    await db.flush()
    return field


@router.post(
    "/{template_id}/create-envelope",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_envelope_from_template(
    template_id: uuid.UUID,
    data: CreateEnvelopeFromTemplate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await _get_template(template_id, current_user, db)

    if not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template is not active",
        )

    # Create envelope
    envelope = Envelope(
        user_id=current_user.id,
        template_id=template_id,
        title=data.title,
        message=data.message,
    )
    db.add(envelope)
    await db.flush()

    # Map template recipients to real recipients
    recipient_map: dict[uuid.UUID, uuid.UUID] = {}  # template_recipient_id -> recipient_id
    template_recipients = template.recipients or []

    for tr in template_recipients:
        if tr.role_name not in data.recipients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing recipient data for role '{tr.role_name}'",
            )

        r_data = data.recipients[tr.role_name]
        recipient = Recipient(
            envelope_id=envelope.id,
            name=r_data.get("name", ""),
            email=r_data.get("email", ""),
            role=tr.role,
            routing_order=tr.routing_order,
        )
        db.add(recipient)
        await db.flush()
        recipient_map[tr.id] = recipient.id

    # Copy template documents and fields
    doc_map: dict[uuid.UUID, uuid.UUID] = {}

    for td in template.documents or []:
        doc_id = uuid7()

        # Copy the file
        new_storage_path = f"documents/{envelope.id}/{doc_id}/original.pdf"
        try:
            original_data = await storage.load(td.storage_path)
            await storage.save(new_storage_path, original_data)
        except FileNotFoundError:
            continue

        document = Document(
            id=doc_id,
            envelope_id=envelope.id,
            filename=td.filename,
            storage_path=new_storage_path,
            content_type=td.content_type,
            size_bytes=td.size_bytes,
            page_count=td.page_count,
            display_order=td.display_order,
        )
        db.add(document)
        await db.flush()
        doc_map[td.id] = doc_id

        # Copy fields
        for tf in td.fields or []:
            if tf.template_recipient_id not in recipient_map:
                continue

            field = DocumentField(
                document_id=doc_id,
                recipient_id=recipient_map[tf.template_recipient_id],
                type=tf.type,
                page_number=tf.page_number,
                x_position=tf.x_position,
                y_position=tf.y_position,
                width=tf.width,
                height=tf.height,
                is_required=tf.is_required,
                placeholder=tf.placeholder,
                validation_rule=tf.validation_rule,
                dropdown_options=tf.dropdown_options,
            )
            db.add(field)

        # Render pages for the new document
        from dataseal.tasks.documents import render_document_pages

        render_document_pages.delay(str(doc_id))

    await db.flush()

    from dataseal.services.audit import create_audit_event

    await create_audit_event(
        db,
        envelope_id=envelope.id,
        user_id=current_user.id,
        event_type="envelope.created",
        description=f"Envelope created from template '{template.name}'",
    )

    return {
        "envelope_id": str(envelope.id),
        "status": "created",
        "message": "Envelope created from template",
    }
