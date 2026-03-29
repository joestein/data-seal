"""OAuth 2.0 API endpoints."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.api.deps import create_access_token, create_refresh_token, get_current_user
from dataseal.config import settings
from dataseal.database import get_db
from dataseal.models.oauth import OAuthApp
from dataseal.models.user import User
from dataseal.schemas.oauth import (
    OAuthAppCreate,
    OAuthAppCreatedResponse,
    OAuthAppResponse,
    OAuthTokenRequest,
    OAuthTokenResponse,
)
from dataseal.security.oauth_codes import consume_auth_code, store_auth_code

router = APIRouter(prefix="/oauth", tags=["oauth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/apps", response_model=OAuthAppCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_oauth_app(
    data: OAuthAppCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client_id = secrets.token_urlsafe(32)
    client_secret = secrets.token_urlsafe(48)

    app = OAuthApp(
        user_id=current_user.id,
        name=data.name,
        client_id=client_id,
        client_secret_hash=pwd_context.hash(client_secret),
        redirect_uris=data.redirect_uris,
        scopes=data.scopes,
    )
    db.add(app)
    await db.flush()

    return OAuthAppCreatedResponse(
        id=app.id,
        user_id=app.user_id,
        name=app.name,
        client_id=client_id,
        redirect_uris=data.redirect_uris,
        scopes=data.scopes,
        is_active=True,
        created_at=app.created_at,
        updated_at=app.updated_at,
        client_secret=client_secret,
    )


@router.get("/apps", response_model=list[OAuthAppResponse])
async def list_oauth_apps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OAuthApp).where(OAuthApp.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/apps/{app_id}", response_model=OAuthAppResponse)
async def get_oauth_app(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OAuthApp).where(
            OAuthApp.id == app_id, OAuthApp.user_id == current_user.id
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth app not found")
    return app


@router.delete("/apps/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_oauth_app(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OAuthApp).where(
            OAuthApp.id == app_id, OAuthApp.user_id == current_user.id
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth app not found")

    await db.delete(app)
    await db.flush()
    return None


@router.get("/authorize")
async def authorize(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str | None = Query(None),
    state: str | None = Query(None),
    code_challenge: str | None = Query(None),
    code_challenge_method: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """OAuth authorization endpoint - generates an authorization code.

    Supports PKCE (RFC 7636) via code_challenge and code_challenge_method parameters.
    The state parameter is required for CSRF protection.
    """
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only 'code' response_type is supported",
        )

    # Require state parameter for CSRF protection
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'state' parameter is required for CSRF protection",
        )

    # Validate PKCE parameters if provided
    if code_challenge_method and code_challenge_method not in ("S256", "plain"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="code_challenge_method must be 'S256' or 'plain'",
        )
    if code_challenge and not code_challenge_method:
        # Default to S256 per RFC 7636
        code_challenge_method = "S256"

    result = await db.execute(
        select(OAuthApp).where(
            OAuthApp.client_id == client_id, OAuthApp.is_active.is_(True)
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client_id"
        )

    if redirect_uri not in app.redirect_uris:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid redirect_uri"
        )

    # Generate authorization code and store in Valkey with 10-minute TTL
    code = secrets.token_urlsafe(32)
    store_auth_code(
        code=code,
        user_id=str(current_user.id),
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )

    return {
        "code": code,
        "state": state,
        "redirect_uri": f"{redirect_uri}?code={code}&state={state}",
    }


@router.post("/token", response_model=OAuthTokenResponse)
async def token_exchange(
    data: OAuthTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """OAuth token endpoint - exchange auth code or JWT for access token."""
    if data.grant_type == "authorization_code":
        return await _handle_auth_code_grant(data, db)
    elif data.grant_type == "urn:ietf:params:oauth:grant-type:jwt-bearer":
        return await _handle_jwt_bearer_grant(data, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant_type: {data.grant_type}",
        )


def _verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    """Verify a PKCE code_verifier against the stored code_challenge."""
    if method == "plain":
        return secrets.compare_digest(code_verifier, code_challenge)
    elif method == "S256":
        import base64
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return secrets.compare_digest(computed, code_challenge)
    return False


async def _handle_auth_code_grant(
    data: OAuthTokenRequest, db: AsyncSession
) -> OAuthTokenResponse:
    if not data.code or not data.client_id or not data.client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameters: code, client_id, client_secret",
        )

    # Consume auth code from Valkey (single-use, auto-expires after 10 minutes)
    code_data = consume_auth_code(data.code)
    if not code_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired authorization code"
        )

    if code_data["client_id"] != data.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Client ID mismatch"
        )

    if data.redirect_uri and code_data["redirect_uri"] != data.redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Redirect URI mismatch"
        )

    # Verify PKCE if code_challenge was provided during authorization
    if code_data.get("code_challenge"):
        if not data.code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code_verifier is required (PKCE was used during authorization)",
            )
        method = code_data.get("code_challenge_method", "S256")
        if not _verify_pkce(data.code_verifier, code_data["code_challenge"], method):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code_verifier (PKCE verification failed)",
            )

    # Validate client secret
    result = await db.execute(
        select(OAuthApp).where(OAuthApp.client_id == data.client_id)
    )
    app = result.scalar_one_or_none()
    if not app or not pwd_context.verify(data.client_secret, app.client_secret_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials"
        )

    user_id = code_data["user_id"]
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    return OAuthTokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expiry_minutes * 60,
        refresh_token=refresh_token,
        scope=code_data.get("scope"),
    )


async def _handle_jwt_bearer_grant(
    data: OAuthTokenRequest, db: AsyncSession
) -> OAuthTokenResponse:
    if not data.assertion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing assertion parameter",
        )

    # Decode the JWT assertion (simplified - in production would verify RSA signature)
    try:
        payload = jwt.decode(
            data.assertion,
            settings.secret_key,
            algorithms=["HS256"],
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT assertion",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT assertion"
        )

    # Verify user exists
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )

    access_token = create_access_token(str(user.id))

    return OAuthTokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expiry_minutes * 60,
        scope=payload.get("scope"),
    )


@router.post("/revoke", status_code=status.HTTP_200_OK)
async def revoke_token(
    token: str,
):
    """Revoke an OAuth token by adding its JTI to the blocklist."""
    from dataseal.api.deps import decode_token
    from dataseal.security.token_blocklist import add_token_to_blocklist

    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            expires_at = datetime.fromtimestamp(exp, tz=UTC)
            add_token_to_blocklist(jti, expires_at)
    except Exception:
        # RFC 7009: The server responds with HTTP 200 even if the token is invalid
        pass
    return {"message": "Token revoked"}
