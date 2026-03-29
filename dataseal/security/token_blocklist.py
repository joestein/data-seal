"""Valkey-based JWT token blocklist for token revocation.

When a user logs out or a token is revoked, the token's JTI (JWT ID) is
added to the blocklist with a TTL matching the token's remaining lifetime.
On every authenticated request, the blocklist is checked before accepting
the token.
"""

from datetime import UTC, datetime

import valkey

from dataseal.config import settings

_valkey_client: valkey.Valkey | None = None

# Key prefix for blocklist entries in Valkey
_BLOCKLIST_PREFIX = "token:blocklist:"


def _get_valkey() -> valkey.Valkey:
    """Get or create a Valkey client for the token blocklist."""
    global _valkey_client  # noqa: PLW0603
    if _valkey_client is None:
        _valkey_client = valkey.from_url(settings.valkey_url, decode_responses=True)
    return _valkey_client


def add_token_to_blocklist(jti: str, expires_at: datetime) -> None:
    """Add a token's JTI to the blocklist.

    Args:
        jti: The JWT ID (unique identifier for the token).
        expires_at: When the token expires. The blocklist entry will
                    be automatically removed after this time.
    """
    r = _get_valkey()
    now = datetime.now(UTC)

    # Calculate remaining TTL in seconds
    remaining = int((expires_at - now).total_seconds())
    if remaining <= 0:
        # Token is already expired, no need to blocklist
        return

    key = f"{_BLOCKLIST_PREFIX}{jti}"
    r.setex(key, remaining, "revoked")


def is_token_blocklisted(jti: str) -> bool:
    """Check if a token's JTI is in the blocklist.

    Args:
        jti: The JWT ID to check.

    Returns:
        True if the token has been revoked, False otherwise.
    """
    r = _get_valkey()
    key = f"{_BLOCKLIST_PREFIX}{jti}"
    return r.exists(key) > 0
