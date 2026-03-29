"""PowerForm API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.api.deps import get_current_user
from dataseal.database import get_db
from dataseal.models.powerform import PowerForm
from dataseal.models.template import Template
from dataseal.models.user import User
from dataseal.schemas.powerform import (
    PowerFormCreate,
    PowerFormResponse,
    PowerFormSubmit,
    PowerFormUpdate,
)

router = APIRouter(tags=["powerforms"])


# --- Authenticated CRUD ---


@router.post("/powerforms", response_model=PowerFormResponse, status_code=status.HTTP_201_CREATED)
async def create_powerform(
    data: PowerFormCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate template exists and belongs to user
    result = await db.execute(
        select(Template).where(Template.id == data.template_id, Template.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Check slug uniqueness
    existing = await db.execute(select(PowerForm).where(PowerForm.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already in use")

    pf = PowerForm(
        user_id=current_user.id,
        template_id=data.template_id,
        name=data.name,
        slug=data.slug,
        is_active=data.is_active,
        max_uses=data.max_uses,
    )
    db.add(pf)
    await db.flush()
    return pf


@router.get("/powerforms", response_model=list[PowerFormResponse])
async def list_powerforms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PowerForm).where(PowerForm.user_id == current_user.id).order_by(PowerForm.created_at.desc())
    )
    return result.scalars().all()


@router.get("/powerforms/{pf_id}", response_model=PowerFormResponse)
async def get_powerform(
    pf_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PowerForm).where(PowerForm.id == pf_id, PowerForm.user_id == current_user.id))
    pf = result.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PowerForm not found")
    return pf


@router.put("/powerforms/{pf_id}", response_model=PowerFormResponse)
async def update_powerform(
    pf_id: uuid.UUID,
    data: PowerFormUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PowerForm).where(PowerForm.id == pf_id, PowerForm.user_id == current_user.id))
    pf = result.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PowerForm not found")

    if data.name is not None:
        pf.name = data.name
    if data.is_active is not None:
        pf.is_active = data.is_active
    if data.max_uses is not None:
        pf.max_uses = data.max_uses

    await db.flush()
    return pf


@router.delete("/powerforms/{pf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_powerform(
    pf_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PowerForm).where(PowerForm.id == pf_id, PowerForm.user_id == current_user.id))
    pf = result.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PowerForm not found")

    await db.delete(pf)
    await db.flush()


# --- Public endpoints ---


@router.get("/p/{slug}")
async def access_powerform(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint to access a PowerForm."""
    result = await db.execute(select(PowerForm).where(PowerForm.slug == slug, PowerForm.is_active.is_(True)))
    pf = result.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PowerForm not found")

    if pf.max_uses is not None and pf.use_count >= pf.max_uses:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This PowerForm has reached its maximum number of uses",
        )

    # Load template recipients to show the form
    template = await db.execute(select(Template).where(Template.id == pf.template_id))
    template = template.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated template not found")

    from dataseal.models.template import TemplateRecipient

    recipients = await db.execute(select(TemplateRecipient).where(TemplateRecipient.template_id == template.id))
    roles = recipients.scalars().all()

    return {
        "powerform": {
            "name": pf.name,
            "slug": pf.slug,
        },
        "roles": [{"role_name": r.role_name, "role": r.role} for r in roles if r.role != "cc"],
    }


@router.post("/p/{slug}")
async def submit_powerform(
    slug: str,
    data: PowerFormSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Submit a PowerForm - creates an envelope and sends it."""
    result = await db.execute(select(PowerForm).where(PowerForm.slug == slug, PowerForm.is_active.is_(True)))
    pf = result.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PowerForm not found")

    if pf.max_uses is not None and pf.use_count >= pf.max_uses:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This PowerForm has reached its maximum number of uses",
        )

    # Create envelope from template using the template endpoint logic

    # Get the powerform owner as the user
    from dataseal.models.user import User
    from dataseal.schemas.template import CreateEnvelopeFromTemplate

    user_result = await db.execute(select(User).where(User.id == pf.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    CreateEnvelopeFromTemplate(
        recipients=data.recipients,
        title=f"{pf.name} - Submission",
        message=None,
    )

    # Create the envelope
    from uuid_extensions import uuid7

    from dataseal.models.document import Document
    from dataseal.models.envelope import Envelope
    from dataseal.models.field import DocumentField
    from dataseal.models.recipient import Recipient
    from dataseal.models.template import TemplateDocument, TemplateField, TemplateRecipient

    template_result = await db.execute(select(Template).where(Template.id == pf.template_id))
    template = template_result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    envelope = Envelope(
        user_id=pf.user_id,
        template_id=pf.template_id,
        powerform_id=pf.id,
        title=f"{pf.name} - Submission",
    )
    db.add(envelope)
    await db.flush()

    # Map recipients
    template_recipients = await db.execute(
        select(TemplateRecipient).where(TemplateRecipient.template_id == template.id)
    )
    template_recipients = template_recipients.scalars().all()

    recipient_map = {}

    for tr in template_recipients:
        if tr.role_name not in data.recipients:
            continue
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

    # Copy docs and fields
    template_docs = await db.execute(select(TemplateDocument).where(TemplateDocument.template_id == template.id))
    template_docs = template_docs.scalars().all()

    from dataseal.storage import storage

    for td in template_docs:
        doc_id = uuid7()
        new_path = f"documents/{envelope.id}/{doc_id}/original.pdf"
        try:
            original_data = await storage.load(td.storage_path)
            await storage.save(new_path, original_data)
        except FileNotFoundError:
            continue

        document = Document(
            id=doc_id,
            envelope_id=envelope.id,
            filename=td.filename,
            storage_path=new_path,
            content_type=td.content_type,
            size_bytes=td.size_bytes,
            page_count=td.page_count,
            display_order=td.display_order,
        )
        db.add(document)
        await db.flush()

        # Copy fields
        tf_result = await db.execute(select(TemplateField).where(TemplateField.template_document_id == td.id))
        for tf in tf_result.scalars().all():
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

        from dataseal.tasks.documents import render_document_pages

        render_document_pages.delay(str(doc_id))

    await db.flush()

    # Send the envelope
    from dataseal.services.envelope import send_envelope

    await send_envelope(db, envelope, pf.user_id)

    # Increment use count
    pf.use_count += 1

    await db.flush()

    # Get the first signer's token for redirect
    signers = await db.execute(
        select(Recipient)
        .where(Recipient.envelope_id == envelope.id)
        .where(Recipient.role == "signer")
        .where(Recipient.signing_token.isnot(None))
        .order_by(Recipient.routing_order)
    )
    first_signer = signers.scalars().first()

    from dataseal.tasks.emails import send_signing_emails

    send_signing_emails.delay(str(envelope.id))

    return {
        "envelope_id": str(envelope.id),
        "signing_url": f"/sign/{first_signer.signing_token}" if first_signer else None,
        "message": "Envelope created and sent",
    }
