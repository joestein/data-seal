"""Document processing tasks (PDF page rendering)."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from dataseal.config import settings
from dataseal.models.document import Document
from dataseal.tasks.celery_app import celery_app


def _get_sync_session() -> Session:
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return Session(engine)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def render_document_pages(self, document_id: str) -> None:
    """Render PDF pages as PNG images for the signing UI."""
    session = _get_sync_session()
    try:
        document = session.get(Document, document_id)
        if not document:
            return

        storage_base = Path(settings.storage_local_path)
        pdf_path = storage_base / document.storage_path

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Import pdf2image here to avoid import errors when poppler isn't installed
        from pdf2image import convert_from_path

        images = convert_from_path(str(pdf_path), dpi=150, fmt="png")

        pages_dir = pdf_path.parent / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        for i, image in enumerate(images, start=1):
            page_path = pages_dir / f"page_{i}.png"
            image.save(str(page_path), "PNG")

        # Update page count
        document.page_count = len(images)
        session.commit()

    except Exception as exc:
        session.rollback()
        raise self.retry(exc=exc) from exc
    finally:
        session.close()
