"""Valkey-backed OAuth authorization code storage with TTL.

Replaces the in-memory dict with Valkey to provide:
- Persistence across restarts
- Automatic expiration via TTL (10 minutes)
- No unbounded memory growth
"""

import json
from datetime import UTC, datetime, timedelta

import valkey

from dataseal.config import settings

_valkey_client: valkey.Valkey | None = None

_AUTH_CODE_PREFIX = "oauth:auth_code:"
_AUTH_CODE_TTL_SECONDS = 600  # 10 minutes


def _get_valkey() -> valkey.Valkey:
    global _valkey_client
    if _valkey_client is None:
        _valkey_client = valkey.from_url(settings.valkey_url, decode_responses=True)
    return _valkey_client


def store_auth_code(
    code: str,
    user_id: str,
    client_id: str,
    redirect_uri: str,
    scope: str | None = None,
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
) -> None:
    """Store an authorization code in Valkey with a 10-minute TTL.

    Args:
        code: The authorization code string.
        user_id: The authenticated user's ID.
        client_id: The OAuth client ID.
        redirect_uri: The redirect URI bound to this code.
        scope: Requested scopes.
        code_challenge: PKCE code challenge (optional).
        code_challenge_method: PKCE method, either "S256" or "plain" (optional).
    """
    r = _get_valkey()
    data = {
        "user_id": user_id,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "created_at": datetime.now(UTC).isoformat(),
    }
    key = f"{_AUTH_CODE_PREFIX}{code}"
    r.setex(key, _AUTH_CODE_TTL_SECONDS, json.dumps(data))


def consume_auth_code(code: str) -> dict | None:
    """Retrieve and delete an authorization code (single-use).

    Args:
        code: The authorization code to consume.

    Returns:
        The code data dict if valid and not expired, None otherwise.
    """
    r = _get_valkey()
    key = f"{_AUTH_CODE_PREFIX}{code}"

    # Use a pipeline to atomically GET and DELETE
    pipe = r.pipeline()
    pipe.get(key)
    pipe.delete(key)
    results = pipe.execute()

    raw = results[0]
    if not raw:
        return None

    return json.loads(raw)
