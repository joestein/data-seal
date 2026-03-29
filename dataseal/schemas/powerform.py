"""PowerForm schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PowerFormCreate(BaseModel):
    template_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9\-]+$")
    is_active: bool = True
    max_uses: int | None = Field(default=None, ge=1)


class PowerFormUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None
    max_uses: int | None = None


class PowerFormResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    template_id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    max_uses: int | None
    use_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PowerFormSubmit(BaseModel):
    """Data submitted by the public user filling in a PowerForm."""

    recipients: dict[str, dict[str, str]]  # role_name -> {name, email}
