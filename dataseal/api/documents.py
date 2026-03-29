"""Document upload and management API endpoints."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.api.deps import get_current_user, get_envelope_dep
from dataseal.config import settings
from dataseal.database import get_db
from dataseal.models.document import Document
from dataseal.models.envelope import Envelope
from dataseal.models.user import User
from dataseal.schemas.document import DocumentResponse, PageResponse
from dataseal.storage import storage

router = APIRouter(prefix="/envelopes/{envelope_id}/documents", tags=["documents"])

# PDF magic bytes
PDF_MAGIC = b"%PDF"
MAX_SIZE = settings.max_document_size_mb * 1024 * 1024


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    envelope_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get envelope
    result = await db.execute(select(Envelope).where(Envelope.id == envelope_id))
    envelope = result.scalar_one_or_none()
    if not envelope or envelope.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envelope not found")

    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add documents after envelope has been sent",
        )

    # Check document count limit
    doc_count = len(envelope.documents) if envelope.documents else 0
    if doc_count >= settings.max_documents_per_envelope:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.max_documents_per_envelope} documents per envelope",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {settings.max_document_size_mb}MB limit",
        )

    # Validate PDF magic bytes
    if not content[:4].startswith(PDF_MAGIC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Validate MIME type
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    from uuid_extensions import uuid7
    doc_id = uuid7()

    storage_path = f"documents/{envelope_id}/{doc_id}/original.pdf"
    await storage.save(storage_path, content)

    document = Document(
        id=doc_id,
        envelope_id=envelope_id,
        filename=file.filename or "document.pdf",
        storage_path=storage_path,
        content_type="application/pdf",
        size_bytes=len(content),
        page_count=0,  # Will be updated by rendering task
        display_order=doc_count,
    )
    db.add(document)
    await db.flush()

    # Enqueue page rendering
    from dataseal.tasks.documents import render_document_pages
    render_document_pages.delay(str(doc_id))

    return document


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document)
        .where(Document.envelope_id == envelope.id)
        .order_by(Document.display_order)
    )
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.envelope_id == envelope.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: uuid.UUID,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.envelope_id == envelope.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_path = Path(settings.storage_local_path) / document.storage_path
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(
        str(file_path),
        media_type=document.content_type,
        filename=document.filename,
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    if envelope.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove documents after envelope has been sent",
        )

    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.envelope_id == envelope.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await storage.delete(document.storage_path)
    await db.delete(document)
    await db.flush()
    return None


@router.get("/{doc_id}/pages", response_model=list[PageResponse])
async def list_pages(
    doc_id: uuid.UUID,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.envelope_id == envelope.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    pages = []
    for i in range(1, document.page_count + 1):
        pages.append(PageResponse(
            page_number=i,
            image_url=f"/api/v1/envelopes/{envelope.id}/documents/{doc_id}/pages/{i}",
        ))
    return pages


@router.get("/{doc_id}/pages/{page_number}")
async def get_page_image(
    doc_id: uuid.UUID,
    page_number: int,
    envelope: Envelope = Depends(get_envelope_dep),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.envelope_id == envelope.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if page_number < 1 or page_number > document.page_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")

    page_path = (
        Path(settings.storage_local_path)
        / f"documents/{envelope.id}/{doc_id}/pages/page_{page_number}.png"
    )
    if not page_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page image not found")

    return FileResponse(str(page_path), media_type="image/png")
