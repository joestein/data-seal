"""Unit tests for signing service business logic."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from dataseal.services.signing import validate_token


class TestValidateToken:
    def _make_recipient(self, status="sent", token_expires_at=None):
        r = MagicMock()
        r.status = status
        r.token_expires_at = token_expires_at
        return r

    def test_valid_active_token_returns_none(self):
        future = datetime.now(UTC) + timedelta(hours=1)
        recipient = self._make_recipient(status="sent", token_expires_at=future)
        result = validate_token(recipient)
        assert result is None

    def test_valid_delivered_token_returns_none(self):
        future = datetime.now(UTC) + timedelta(hours=1)
        recipient = self._make_recipient(status="delivered", token_expires_at=future)
        result = validate_token(recipient)
        assert result is None

    def test_already_signed_returns_error_string(self):
        recipient = self._make_recipient(status="signed")
        result = validate_token(recipient)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_declined_returns_error_string(self):
        recipient = self._make_recipient(status="declined")
        result = validate_token(recipient)
        assert result is not None

    def test_expired_token_returns_error_string(self):
        past = datetime.now(UTC) - timedelta(seconds=1)
        recipient = self._make_recipient(status="sent", token_expires_at=past)
        result = validate_token(recipient)
        assert result is not None
        assert "expired" in result.lower()

    def test_no_expiry_date_is_valid(self):
        recipient = self._make_recipient(status="sent", token_expires_at=None)
        result = validate_token(recipient)
        assert result is None
