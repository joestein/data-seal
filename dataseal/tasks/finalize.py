"""Envelope finalization task - embed signatures and generate certificate."""

import base64
import hashlib
import io
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from dataseal.config import settings
from dataseal.models.audit import AuditEvent
from dataseal.models.document import Document
from dataseal.models.envelope import Envelope
from dataseal.models.field import DocumentField
from dataseal.models.recipient import Recipient
from dataseal.tasks.celery_app import celery_app


def _get_sync_session() -> Session:
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return Session(engine)


def _generate_certificate_pdf(
    envelope: Envelope,
    recipients: list[Recipient],
    audit_events: list[AuditEvent],
    document_hashes: dict[str, str],
) -> bytes:
    """Generate a certificate of completion PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        "CertTitle", parent=styles["Title"], fontSize=18, spaceAfter=20
    )
    elements.append(Paragraph("Certificate of Completion", title_style))
    elements.append(Spacer(1, 12))

    # Envelope info
    info_style = ParagraphStyle("Info", parent=styles["Normal"], fontSize=10, spaceAfter=6)
    cert_id = str(uuid.uuid4())
    elements.append(Paragraph(f"<b>Certificate ID:</b> {cert_id}", info_style))
    elements.append(Paragraph(f"<b>Envelope ID:</b> {envelope.id}", info_style))
    elements.append(Paragraph(f"<b>Title:</b> {envelope.title}", info_style))
    completed_str = envelope.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if envelope.completed_at else "N/A"
    elements.append(Paragraph(f"<b>Completed:</b> {completed_str}", info_style))
    elements.append(Spacer(1, 16))

    # Recipients
    elements.append(Paragraph("<b>Signing Participants</b>", styles["Heading3"]))
    for r in recipients:
        signed_str = r.signed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if r.signed_at else "N/A"
        elements.append(Paragraph(
            f"{r.name} ({r.email}) - {r.role} - Status: {r.status} - "
            f"Signed: {signed_str} - IP: {r.ip_address or 'N/A'}",
            info_style,
        ))
    elements.append(Spacer(1, 16))

    # Document hashes
    elements.append(Paragraph("<b>Document Integrity</b>", styles["Heading3"]))
    for doc_name, doc_hash in document_hashes.items():
        elements.append(Paragraph(
            f"{doc_name}: SHA-256 = {doc_hash}", info_style
        ))
    elements.append(Spacer(1, 16))

    # Audit trail
    elements.append(Paragraph("<b>Audit Trail</b>", styles["Heading3"]))
    for event in audit_events:
        ts = event.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if event.created_at else ""
        elements.append(Paragraph(
            f"[{ts}] {event.event_type}: {event.description}",
            info_style,
        ))

    doc.build(elements)
    return buffer.getvalue()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def finalize_envelope(self, envelope_id: str) -> None:
    """Finalize an envelope after all recipients have signed."""
    session = _get_sync_session()
    try:
        envelope = session.get(Envelope, envelope_id)
        if not envelope:
            return

        storage_base = Path(settings.storage_local_path)

        # Load all documents, fields, recipients, audit events
        documents = (
            session.execute(select(Document).where(Document.envelope_id == envelope_id))
            .scalars().all()
        )
        recipients = (
            session.execute(select(Recipient).where(Recipient.envelope_id == envelope_id))
            .scalars().all()
        )
        audit_events = (
            session.execute(
                select(AuditEvent)
                .where(AuditEvent.envelope_id == envelope_id)
                .order_by(AuditEvent.created_at)
            )
            .scalars().all()
        )

        from PIL import Image
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas

        document_hashes = {}
        final_writer = PdfWriter()

        for document in documents:
            pdf_path = storage_base / document.storage_path
            if not pdf_path.exists():
                continue

            # Hash the original document
            with open(pdf_path, "rb") as f:
                original_data = f.read()
            document_hashes[document.filename] = hashlib.sha256(original_data).hexdigest()

            reader = PdfReader(io.BytesIO(original_data))

            # Get fields for this document
            fields = (
                session.execute(
                    select(DocumentField)
                    .where(DocumentField.document_id == document.id)
                    .where(DocumentField.value.isnot(None))
                )
                .scalars().all()
            )

            # Process each page
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)

                # Get fields for this page
                page_fields = [f for f in fields if f.page_number == page_num + 1]

                if page_fields:
                    # Create an overlay with field values
                    overlay_buffer = io.BytesIO()
                    c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))

                    for field in page_fields:
                        # Convert percentage to absolute coordinates
                        x = (field.x_position / 100.0) * page_width
                        # PDF y-coordinates are from bottom
                        y = page_height - ((field.y_position / 100.0) * page_height)
                        w = (field.width / 100.0) * page_width
                        h = (field.height / 100.0) * page_height

                        if field.type in ("signature", "initials"):
                            # Decode base64 image and draw it
                            try:
                                img_data = base64.b64decode(field.value)
                                img = Image.open(io.BytesIO(img_data))
                                # Save as temp PNG for reportlab
                                img_buffer = io.BytesIO()
                                img.save(img_buffer, format="PNG")
                                img_buffer.seek(0)

                                from reportlab.lib.utils import ImageReader
                                img_reader = ImageReader(img_buffer)
                                c.drawImage(img_reader, x, y - h, width=w, height=h, mask="auto")
                            except Exception:
                                # Fallback: draw the value as text
                                c.setFont("Helvetica", 10)
                                c.drawString(x, y - 12, field.value[:50])
                        elif field.type == "checkbox":
                            if field.value == "true":
                                c.setFont("ZapfDingbats", 14)
                                c.drawString(x, y - 14, "\u2714")
                        elif field.type in ("text", "date_signed", "dropdown"):
                            c.setFont("Helvetica", 10)
                            c.drawString(x, y - 12, field.value[:200])

                    c.save()
                    overlay_buffer.seek(0)

                    # Merge overlay onto page
                    overlay_reader = PdfReader(overlay_buffer)
                    if len(overlay_reader.pages) > 0:
                        page.merge_page(overlay_reader.pages[0])

                final_writer.add_page(page)

        # Generate certificate of completion
        cert_pdf_bytes = _generate_certificate_pdf(
            envelope, recipients, audit_events, document_hashes
        )
        cert_reader = PdfReader(io.BytesIO(cert_pdf_bytes))
        for page in cert_reader.pages:
            final_writer.add_page(page)

        # Save final document
        completed_dir = storage_base / "documents" / str(envelope_id) / "completed"
        completed_dir.mkdir(parents=True, exist_ok=True)

        final_path = completed_dir / "final.pdf"
        final_buffer = io.BytesIO()
        final_writer.write(final_buffer)
        final_data = final_buffer.getvalue()

        with open(final_path, "wb") as f:
            f.write(final_data)

        # Save certificate separately
        cert_path = completed_dir / "certificate.pdf"
        with open(cert_path, "wb") as f:
            f.write(cert_pdf_bytes)

        # Compute and store final hash
        final_hash = hashlib.sha256(final_data).hexdigest()
        envelope.completed_hash = final_hash
        envelope.status = "completed"
        envelope.completed_at = datetime.now(UTC)

        # Add audit event
        audit = AuditEvent(
            envelope_id=uuid.UUID(envelope_id),
            event_type="envelope.completed",
            description=f"Envelope finalized. SHA-256: {final_hash}",
        )
        session.add(audit)
        session.commit()

        # Trigger completion emails and webhooks
        from dataseal.tasks.emails import send_completion_emails
        from dataseal.tasks.webhooks import dispatch_webhook_event

        send_completion_emails.delay(envelope_id)
        dispatch_webhook_event.delay(envelope_id, "envelope.completed")

    except Exception as exc:
        session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()
