"""Template schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class TemplateRecipientCreate(BaseModel):
    role_name: str = Field(min_length=1, max_length=100)
    role: str = Field(default="signer", pattern=r"^(signer|cc|in_person_signer)$")
    routing_order: int = Field(default=1, ge=1)


class TemplateFieldCreate(BaseModel):
    template_recipient_id: uuid.UUID
    type: str = Field(pattern=r"^(signature|initials|date_signed|text|checkbox|dropdown)$")
    page_number: int = Field(ge=1)
    x_position: float = Field(ge=0, le=100)
    y_position: float = Field(ge=0, le=100)
    width: float = Field(gt=0, le=100)
    height: float = Field(gt=0, le=100)
    is_required: bool = True
    placeholder: str | None = Field(default=None, max_length=255)
    validation_rule: str | None = Field(default=None, max_length=255)
    dropdown_options: list[str] | None = None


class TemplateRecipientResponse(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    role_name: str
    role: str
    routing_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateFieldResponse(BaseModel):
    id: uuid.UUID
    template_document_id: uuid.UUID
    template_recipient_id: uuid.UUID
    type: str
    page_number: int
    x_position: float
    y_position: float
    width: float
    height: float
    is_required: bool
    placeholder: str | None
    validation_rule: str | None
    dropdown_options: list[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateDocumentResponse(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    page_count: int
    display_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateEnvelopeFromTemplate(BaseModel):
    recipients: dict[str, dict[str, str]]  # role_name -> {name, email}
    title: str = Field(min_length=1, max_length=500)
    message: str | None = None
