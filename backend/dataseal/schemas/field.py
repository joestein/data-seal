"""Document field schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FieldCreate(BaseModel):
    recipient_id: uuid.UUID
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


class FieldUpdate(BaseModel):
    page_number: int | None = Field(default=None, ge=1)
    x_position: float | None = Field(default=None, ge=0, le=100)
    y_position: float | None = Field(default=None, ge=0, le=100)
    width: float | None = Field(default=None, gt=0, le=100)
    height: float | None = Field(default=None, gt=0, le=100)
    is_required: bool | None = None
    placeholder: str | None = Field(default=None, max_length=255)
    validation_rule: str | None = Field(default=None, max_length=255)
    dropdown_options: list[str] | None = None


class FieldResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    recipient_id: uuid.UUID
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
    value: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FieldValueUpdate(BaseModel):
    value: str = Field(min_length=1)
