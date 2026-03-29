"""Webhook schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WebhookCreate(BaseModel):
    url: str = Field(max_length=2000)
    events: list[str]
    is_active: bool = True


class WebhookUpdate(BaseModel):
    url: str | None = Field(default=None, max_length=2000)
    events: list[str] | None = None
    is_active: bool | None = None


class WebhookResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryResponse(BaseModel):
    id: uuid.UUID
    webhook_endpoint_id: uuid.UUID
    envelope_id: uuid.UUID
    event_type: str
    payload: dict
    response_status: int | None
    response_body: str | None
    attempt_count: int
    max_attempts: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
