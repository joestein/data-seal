"""Recipient schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RecipientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    role: str = Field(default="signer", pattern=r"^(signer|cc|in_person_signer)$")
    routing_order: int = Field(default=1, ge=1)


class RecipientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    role: str | None = Field(default=None, pattern=r"^(signer|cc|in_person_signer)$")
    routing_order: int | None = Field(default=None, ge=1)


class RecipientResponse(BaseModel):
    id: uuid.UUID
    envelope_id: uuid.UUID
    name: str
    email: str
    role: str
    routing_order: int
    status: str
    signed_at: datetime | None
    declined_at: datetime | None
    declined_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
