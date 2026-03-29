"""Unit tests for HMAC-SHA256 webhook signature generation."""

import hashlib
import hmac

from dataseal.tasks.webhooks import _compute_signature


class TestWebhookSignature:
    def test_signature_returns_hex_string(self):
        sig = _compute_signature("my-secret", '{"event": "test"}')
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA-256 hex digest length

    def test_signature_is_deterministic(self):
        secret = "consistent-secret"
        payload = '{"event": "envelope.sent"}'
        sig1 = _compute_signature(secret, payload)
        sig2 = _compute_signature(secret, payload)
        assert sig1 == sig2

    def test_signature_changes_with_different_secret(self):
        payload = '{"event": "test"}'
        sig1 = _compute_signature("secret-a", payload)
        sig2 = _compute_signature("secret-b", payload)
        assert sig1 != sig2

    def test_signature_changes_with_different_payload(self):
        secret = "same-secret"
        sig1 = _compute_signature(secret, '{"event": "a"}')
        sig2 = _compute_signature(secret, '{"event": "b"}')
        assert sig1 != sig2

    def test_signature_matches_manual_hmac_computation(self):
        secret = "test-secret"
        payload = '{"event": "envelope.completed", "id": "123"}'
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        result = _compute_signature(secret, payload)
        assert result == expected

    def test_signature_with_empty_payload(self):
        # Should not raise; empty payload still produces a valid signature
        sig = _compute_signature("secret", "")
        assert len(sig) == 64

    def test_signature_with_unicode_payload(self):
        sig = _compute_signature("secret", '{"name": "José García"}')
        assert len(sig) == 64

    def test_signature_with_empty_secret(self):
        sig = _compute_signature("", '{"event": "test"}')
        assert len(sig) == 64

    def test_verify_signature_using_hmac_compare_digest(self):
        """Verify signature can be validated in constant time."""
        secret = "webhook-secret"
        payload = '{"event": "envelope.sent"}'
        computed = _compute_signature(secret, payload)
        # Simulate receiver verification
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert hmac.compare_digest(computed, expected)
