"""FastAPI dependency injection for authentication and authorization."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataseal.config import settings
from dataseal.database import get_db
from dataseal.models.envelope import Envelope
from dataseal.models.user import ApiKey, User

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_rounds)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    from datetime import timedelta

    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expiry_minutes)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(user_id: str) -> str:
    from datetime import timedelta

    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expiry_days)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from err

    # Check if the token has been revoked via the blocklist
    jti = payload.get("jti")
    if jti:
        try:
            from dataseal.security.token_blocklist import is_token_blocklisted

            if is_token_blocklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )
        except ImportError:
            pass
        except HTTPException:
            raise
        except Exception:
            # If Valkey is unavailable, log but do not block the request
            # to avoid a denial-of-service when Valkey is down
            logger.warning("Failed to check token blocklist (Valkey may be unavailable)")

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate via JWT bearer token or API key."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check if it's an API key (starts with ds_key_)
    if token.startswith("ds_key_"):
        return await _authenticate_api_key(token, db)

    # Otherwise try JWT
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


class AuthenticatedUser:
    """Wrapper that carries the authenticated user and their API key scopes (if any)."""

    def __init__(self, user: User, api_key_scopes: list[str] | None = None):
        self.user = user
        self.api_key_scopes = api_key_scopes


# Module-level storage for the current request's API key scopes (set during auth)
_current_api_key_scopes: dict[int, list[str] | None] = {}


async def _authenticate_api_key(key: str, db: AsyncSession) -> User:
    """Authenticate via API key and store scopes for later enforcement."""
    prefix = key[:8]
    result = await db.execute(select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True)))
    api_keys = result.scalars().all()

    for api_key in api_keys:
        if pwd_context.verify(key, api_key.key_hash):
            # Check expiry
            if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key expired",
                )

            # Update last_used_at
            api_key.last_used_at = datetime.now(UTC)

            # Load user
            user_result = await db.execute(select(User).where(User.id == api_key.user_id))
            user = user_result.scalar_one_or_none()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )

            # Store scopes on the user object for later enforcement
            user._api_key_scopes = api_key.scopes  # type: ignore[attr-defined]
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )


def require_scope(*required_scopes: str):
    """FastAPI dependency factory that checks API key scopes.

    If the request is authenticated via JWT (not API key), all scopes
    are implicitly granted. If authenticated via API key, the key's
    scopes must include at least one of the required scopes or "*".

    Usage:
        @router.post("/sensitive", dependencies=[Depends(require_scope("write", "admin"))])
        async def sensitive_endpoint(...): ...
    """

    async def _check_scope(
        current_user: User = Depends(get_current_user),
    ) -> User:
        scopes = getattr(current_user, "_api_key_scopes", None)
        # If no scopes attribute, this is JWT auth -- allow everything
        if scopes is None:
            return current_user

        # Wildcard scope grants everything
        if "*" in scopes:
            return current_user

        # Check if any required scope is in the key's scopes
        for scope in required_scopes:
            if scope in scopes:
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key lacks required scope. Required one of: {list(required_scopes)}",
        )

    return _check_scope


async def get_envelope_dep(
    envelope_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope:
    """Get an envelope, ensuring it belongs to the current user."""
    result = await db.execute(select(Envelope).where(Envelope.id == envelope_id))
    envelope = result.scalar_one_or_none()

    if not envelope or envelope.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envelope not found")

    return envelope


def get_client_ip(request: Request) -> str | None:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
