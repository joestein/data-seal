"""OAuth schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class OAuthAppCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    redirect_uris: list[str]
    scopes: list[str]


class OAuthAppResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    client_id: str
    redirect_uris: list[str]
    scopes: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OAuthAppCreatedResponse(OAuthAppResponse):
    """Returned only at creation time - includes the client secret."""
    client_secret: str


class OAuthTokenRequest(BaseModel):
    grant_type: str
    code: str | None = None
    redirect_uri: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    assertion: str | None = None  # For JWT Bearer grant
    code_verifier: str | None = None  # PKCE (RFC 7636)


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None
    scope: str | None = None


class OAuthAuthorizeRequest(BaseModel):
    response_type: str = "code"
    client_id: str
    redirect_uri: str
    scope: str | None = None
    state: str | None = None
