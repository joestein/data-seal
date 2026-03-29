"""Envelope schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EnvelopeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    message: str | None = None
    expires_at: datetime | None = None


class EnvelopeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    message: str | None = None
    expires_at: datetime | None = None


class EnvelopeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    template_id: uuid.UUID | None
    powerform_id: uuid.UUID | None
    title: str
    message: str | None
    status: str
    voided_reason: str | None
    expires_at: datetime | None
    completed_at: datetime | None
    completed_hash: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnvelopeListResponse(BaseModel):
    items: list[EnvelopeResponse]
    total: int
    page: int
    page_size: int


class VoidRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class SendResponse(BaseModel):
    id: uuid.UUID
    status: str
    message: str
