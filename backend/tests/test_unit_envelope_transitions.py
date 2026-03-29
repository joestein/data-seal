"""Unit tests for Envelope status transition logic."""

from dataseal.models.envelope import Envelope


class _FakeEnvelope:
    """Lightweight stub for testing can_transition_to without SQLAlchemy session."""

    ALLOWED_TRANSITIONS = Envelope.ALLOWED_TRANSITIONS
    VALID_STATUSES = Envelope.VALID_STATUSES

    def __init__(self, status: str):
        self.status = status

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())


class TestEnvelopeStatusTransitions:
    def _make_envelope(self, status: str) -> _FakeEnvelope:
        return _FakeEnvelope(status)

    # Valid transitions
    def test_created_can_transition_to_sent(self):
        e = self._make_envelope("created")
        assert e.can_transition_to("sent") is True

    def test_created_can_transition_to_voided(self):
        e = self._make_envelope("created")
        assert e.can_transition_to("voided") is True

    def test_sent_can_transition_to_delivered(self):
        e = self._make_envelope("sent")
        assert e.can_transition_to("delivered") is True

    def test_sent_can_transition_to_voided(self):
        e = self._make_envelope("sent")
        assert e.can_transition_to("voided") is True

    def test_sent_can_transition_to_declined(self):
        e = self._make_envelope("sent")
        assert e.can_transition_to("declined") is True

    def test_delivered_can_transition_to_signed(self):
        e = self._make_envelope("delivered")
        assert e.can_transition_to("signed") is True

    def test_delivered_can_transition_to_voided(self):
        e = self._make_envelope("delivered")
        assert e.can_transition_to("voided") is True

    def test_delivered_can_transition_to_declined(self):
        e = self._make_envelope("delivered")
        assert e.can_transition_to("declined") is True

    def test_signed_can_transition_to_completed(self):
        e = self._make_envelope("signed")
        assert e.can_transition_to("completed") is True

    def test_signed_can_transition_to_voided(self):
        e = self._make_envelope("signed")
        assert e.can_transition_to("voided") is True

    # Invalid transitions
    def test_completed_cannot_transition_anywhere(self):
        e = self._make_envelope("completed")
        for status in Envelope.VALID_STATUSES:
            assert e.can_transition_to(status) is False

    def test_voided_cannot_transition_anywhere(self):
        e = self._make_envelope("voided")
        for status in Envelope.VALID_STATUSES:
            assert e.can_transition_to(status) is False

    def test_declined_cannot_transition_anywhere(self):
        e = self._make_envelope("declined")
        for status in Envelope.VALID_STATUSES:
            assert e.can_transition_to(status) is False

    def test_created_cannot_transition_to_completed(self):
        e = self._make_envelope("created")
        assert e.can_transition_to("completed") is False

    def test_created_cannot_transition_to_delivered(self):
        e = self._make_envelope("created")
        assert e.can_transition_to("delivered") is False

    def test_created_cannot_transition_to_signed(self):
        e = self._make_envelope("created")
        assert e.can_transition_to("signed") is False

    def test_created_cannot_transition_to_declined(self):
        e = self._make_envelope("created")
        assert e.can_transition_to("declined") is False

    def test_sent_cannot_transition_to_completed(self):
        e = self._make_envelope("sent")
        assert e.can_transition_to("completed") is False

    def test_sent_cannot_transition_to_signed(self):
        e = self._make_envelope("sent")
        assert e.can_transition_to("signed") is False

    def test_can_transition_to_unknown_status_returns_false(self):
        e = self._make_envelope("created")
        assert e.can_transition_to("unknown_status") is False

    def test_can_transition_to_empty_string_returns_false(self):
        e = self._make_envelope("sent")
        assert e.can_transition_to("") is False

    def test_valid_statuses_contains_all_expected(self):
        expected = {"created", "sent", "delivered", "signed", "completed", "voided", "declined"}
        assert expected == Envelope.VALID_STATUSES
