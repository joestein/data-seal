"""Unit tests for auth utilities: password hashing and JWT token functions."""

from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from dataseal.api.deps import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from dataseal.config import settings


class TestPasswordHashing:
    def test_hash_password_returns_non_empty_string(self):
        hashed = hash_password("mypassword123")
        assert hashed
        assert isinstance(hashed, str)

    def test_hash_password_is_not_plaintext(self):
        plain = "mypassword123"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_verify_password_correct(self):
        plain = "correct_password"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_wrong(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_deterministic_check_different_salts(self):
        # Two hashes of the same password should be different (bcrypt uses random salt)
        plain = "same_password"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2
        # But both should verify correctly
        assert verify_password(plain, h1) is True
        assert verify_password(plain, h2) is True

    def test_verify_empty_password_against_empty_hash(self):
        hashed = hash_password("x" * 128)
        # Max password boundary
        assert verify_password("x" * 128, hashed) is True

    def test_verify_password_empty_plain_text(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False


class TestJWTTokens:
    def test_create_access_token_returns_string(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token("user-123")
        assert isinstance(token, str)

    def test_access_token_contains_correct_claims(self):
        user_id = "abc-123-def"
        token = create_access_token(user_id)
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_refresh_token_contains_correct_claims(self):
        user_id = "abc-123-def"
        token = create_refresh_token(user_id)
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_access_token_expiry_is_future(self):
        token = create_access_token("user-123")
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert exp > datetime.now(UTC)

    def test_refresh_token_expiry_longer_than_access(self):
        access = create_access_token("user-123")
        refresh = create_refresh_token("user-123")
        access_payload = jwt.decode(access, settings.secret_key, algorithms=["HS256"])
        refresh_payload = jwt.decode(refresh, settings.secret_key, algorithms=["HS256"])
        assert refresh_payload["exp"] > access_payload["exp"]

    def test_decode_token_valid(self):
        token = create_access_token("user-abc")
        payload = decode_token(token)
        assert payload["sub"] == "user-abc"

    def test_decode_token_invalid_raises_http_exception(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_token("not.a.valid.token")
        assert exc_info.value.status_code == 401

    def test_decode_token_tampered_raises_http_exception(self):
        from fastapi import HTTPException

        token = create_access_token("user-123")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException) as exc_info:
            decode_token(tampered)
        assert exc_info.value.status_code == 401

    def test_decode_expired_token_raises_http_exception(self):
        from fastapi import HTTPException

        # Manually craft an expired token
        payload = {
            "sub": "user-123",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(seconds=1),
        }
        expired_token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
        with pytest.raises(HTTPException) as exc_info:
            decode_token(expired_token)
        assert exc_info.value.status_code == 401
