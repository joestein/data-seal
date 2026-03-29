"""Document schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    envelope_id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    page_count: int
    display_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PageResponse(BaseModel):
    page_number: int
    image_url: str
