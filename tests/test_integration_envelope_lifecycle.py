"""Integration tests: Full envelope lifecycle and signing flow."""

import io
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio

from dataseal.models.document import Document
from dataseal.models.envelope import Envelope
from dataseal.models.field import DocumentField
from dataseal.models.recipient import Recipient

# Minimal valid PDF (magic bytes)
MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<</Type /Catalog>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<</Size 1>>\nstartxref\n9\n%%EOF"


@pytest.fixture
def user_and_headers(client):
    """Register user and return auth headers."""
    client.post("/api/v1/auth/register", json={
        "email": "lifecycle@example.com",
        "password": "LifecyclePass123!",
        "full_name": "Lifecycle User",
    })
    login = client.post("/api/v1/auth/login", json={
        "email": "lifecycle@example.com",
        "password": "LifecyclePass123!",
    })
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestEnvelopeValidation:
    """Test send envelope validation before we can do full flow tests."""

    def test_cannot_send_envelope_without_documents(self, client, user_and_headers):
        env = client.post("/api/v1/envelopes", json={"title": "Empty"}, headers=user_and_headers).json()
        resp = client.post(f"/api/v1/envelopes/{env['id']}/send", headers=user_and_headers)
        assert resp.status_code == 400
        errors = resp.json()["detail"]["errors"]
        assert any("document" in e.lower() for e in errors)

    def test_cannot_send_envelope_without_signers(self, client, user_and_headers):
        env = client.post("/api/v1/envelopes", json={"title": "No Signers"}, headers=user_and_headers).json()

        # Upload doc
        with patch("dataseal.api.documents.storage.save"), \
             patch("dataseal.tasks.documents.render_document_pages.delay"):
            client.post(
                f"/api/v1/envelopes/{env['id']}/documents",
                files={"file": ("doc.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
                headers=user_and_headers,
            )

        resp = client.post(f"/api/v1/envelopes/{env['id']}/send", headers=user_and_headers)
        assert resp.status_code == 400
        errors = resp.json()["detail"]["errors"]
        assert any("signer" in e.lower() for e in errors)

    def test_cannot_send_envelope_when_signer_has_no_fields(self, client, user_and_headers):
        env = client.post("/api/v1/envelopes", json={"title": "No Fields"}, headers=user_and_headers).json()

        # Upload doc
        with patch("dataseal.api.documents.storage.save"), \
             patch("dataseal.tasks.documents.render_document_pages.delay"):
            doc = client.post(
                f"/api/v1/envelopes/{env['id']}/documents",
                files={"file": ("doc.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
                headers=user_and_headers,
            ).json()

        # Add signer but no fields
        client.post(
            f"/api/v1/envelopes/{env['id']}/recipients",
            json={"name": "Alice", "email": "alice@example.com"},
            headers=user_and_headers,
        )

        resp = client.post(f"/api/v1/envelopes/{env['id']}/send", headers=user_and_headers)
        assert resp.status_code == 400
        errors = resp.json()["detail"]["errors"]
        assert any("field" in e.lower() for e in errors)


class TestFullEnvelopeLifecycle:
    """Test the complete envelope lifecycle with mocked storage."""

    def _setup_envelope(self, client, headers):
        """Helper: create envelope with doc, recipient, and field ready to send."""
        # 1. Create envelope
        env = client.post("/api/v1/envelopes", json={"title": "Contract"}, headers=headers).json()
        env_id = env["id"]

        # 2. Upload document with mocked storage
        with patch("dataseal.api.documents.storage.save"), \
             patch("dataseal.tasks.documents.render_document_pages.delay"):
            doc = client.post(
                f"/api/v1/envelopes/{env_id}/documents",
                files={"file": ("contract.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
                headers=headers,
            ).json()
        doc_id = doc["id"]

        # 3. Add signer
        recipient_resp = client.post(
            f"/api/v1/envelopes/{env_id}/recipients",
            json={"name": "Alice Signer", "email": "alice@example.com"},
            headers=headers,
        )
        assert recipient_resp.status_code == 201
        recipient_id = recipient_resp.json()[0]["id"]

        # 4. Add field for signer
        field_resp = client.post(
            f"/api/v1/envelopes/{env_id}/documents/{doc_id}/fields",
            json={
                "recipient_id": recipient_id,
                "type": "signature",
                "page_number": 1,
                "x_position": 10.0,
                "y_position": 10.0,
                "width": 20.0,
                "height": 5.0,
            },
            headers=headers,
        )
        assert field_resp.status_code == 201

        return env_id, doc_id, recipient_id

    def test_send_envelope_success(self, client, user_and_headers):
        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            env_id, doc_id, recipient_id = self._setup_envelope(client, user_and_headers)
            resp = client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sent"

    def test_envelope_status_is_sent_after_send(self, client, user_and_headers):
        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            env_id, _, _ = self._setup_envelope(client, user_and_headers)
            client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)

        env = client.get(f"/api/v1/envelopes/{env_id}", headers=user_and_headers).json()
        assert env["status"] == "sent"

    def test_cannot_update_sent_envelope(self, client, user_and_headers):
        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            env_id, _, _ = self._setup_envelope(client, user_and_headers)
            client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)

        resp = client.put(
            f"/api/v1/envelopes/{env_id}",
            json={"title": "Try to Update"},
            headers=user_and_headers,
        )
        assert resp.status_code == 400

    def test_cannot_delete_sent_envelope(self, client, user_and_headers):
        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            env_id, _, _ = self._setup_envelope(client, user_and_headers)
            client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)

        resp = client.delete(f"/api/v1/envelopes/{env_id}", headers=user_and_headers)
        assert resp.status_code == 400

    def test_can_void_sent_envelope(self, client, user_and_headers):
        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"), \
             patch("dataseal.tasks.emails.send_void_notification.delay"):
            env_id, _, _ = self._setup_envelope(client, user_and_headers)
            client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)
            resp = client.post(
                f"/api/v1/envelopes/{env_id}/void",
                json={"reason": "No longer needed"},
                headers=user_and_headers,
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "voided"

    def test_cannot_send_already_sent_envelope(self, client, user_and_headers):
        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            env_id, _, _ = self._setup_envelope(client, user_and_headers)
            client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)
            # Try to send again
            resp = client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)

        assert resp.status_code == 400

    def test_resend_sent_envelope_success(self, client, user_and_headers):
        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            env_id, _, _ = self._setup_envelope(client, user_and_headers)
            client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)

        with patch("dataseal.tasks.emails.send_signing_emails.delay"):
            resp = client.post(f"/api/v1/envelopes/{env_id}/resend", headers=user_and_headers)

        assert resp.status_code == 200

    def test_audit_trail_records_send_event(self, client, user_and_headers):
        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            env_id, _, _ = self._setup_envelope(client, user_and_headers)
            client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)

        audit = client.get(f"/api/v1/envelopes/{env_id}/audit-trail", headers=user_and_headers).json()
        event_types = [e["event_type"] for e in audit]
        assert "envelope.sent" in event_types

    async def test_signing_session_accessible_with_token(self, client, user_and_headers, db_session):
        """Test the signing session endpoint using a signing token from DB."""
        from sqlalchemy import select as sa_select

        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            env_id, _, recipient_id = self._setup_envelope(client, user_and_headers)
            client.post(f"/api/v1/envelopes/{env_id}/send", headers=user_and_headers)

        # Get the signing token from DB
        result = await db_session.execute(
            sa_select(Recipient).where(Recipient.id == uuid.UUID(recipient_id))
        )
        r = result.scalar_one_or_none()
        signing_token = r.signing_token if r else None
        assert signing_token is not None

        # Access the signing session
        resp = client.get(f"/api/v1/signing/{signing_token}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["envelope"]["id"] == env_id
        assert data["recipient"]["email"] == "alice@example.com"


class TestSigningWorkflow:
    """Test the signing experience endpoints using a directly injected signing token."""

    @pytest_asyncio.fixture
    async def ready_envelope(self, client, user_and_headers, db_session):
        """Create a fully configured envelope in 'sent' state, return IDs and token."""
        from sqlalchemy import select as sa_select

        env_id_str = None
        doc_id_str = None
        recipient_id_str = None
        field_id_str = None

        # Create envelope
        env = client.post("/api/v1/envelopes", json={"title": "Signing Test"}, headers=user_and_headers).json()
        env_id_str = env["id"]

        # Upload doc
        with patch("dataseal.api.documents.storage.save"), \
             patch("dataseal.tasks.documents.render_document_pages.delay"):
            doc = client.post(
                f"/api/v1/envelopes/{env_id_str}/documents",
                files={"file": ("contract.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
                headers=user_and_headers,
            ).json()
        doc_id_str = doc["id"]

        # Add recipient
        rec = client.post(
            f"/api/v1/envelopes/{env_id_str}/recipients",
            json={"name": "Bob Signer", "email": "bob@sign.com"},
            headers=user_and_headers,
        ).json()[0]
        recipient_id_str = rec["id"]

        # Add field
        field = client.post(
            f"/api/v1/envelopes/{env_id_str}/documents/{doc_id_str}/fields",
            json={
                "recipient_id": recipient_id_str,
                "type": "text",
                "page_number": 1,
                "x_position": 10.0,
                "y_position": 10.0,
                "width": 20.0,
                "height": 5.0,
            },
            headers=user_and_headers,
        ).json()[0]
        field_id_str = field["id"]

        # Send envelope
        with patch("dataseal.tasks.emails.send_signing_emails.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            client.post(f"/api/v1/envelopes/{env_id_str}/send", headers=user_and_headers)

        # Get signing token from DB
        result = await db_session.execute(
            sa_select(Recipient).where(Recipient.id == uuid.UUID(recipient_id_str))
        )
        recipient = result.scalar_one()
        signing_token = recipient.signing_token

        return {
            "env_id": env_id_str,
            "doc_id": doc_id_str,
            "recipient_id": recipient_id_str,
            "field_id": field_id_str,
            "signing_token": signing_token,
        }

    async def test_get_signing_session(self, client, ready_envelope):
        token = ready_envelope["signing_token"]
        resp = client.get(f"/api/v1/signing/{token}")
        assert resp.status_code == 200
        data = resp.json()
        assert "envelope" in data
        assert "recipient" in data
        assert "documents" in data

    async def test_signing_with_invalid_token_returns_404(self, client):
        resp = client.get("/api/v1/signing/totally-invalid-token-xyz")
        assert resp.status_code == 404

    async def test_submit_field_value(self, client, ready_envelope):
        token = ready_envelope["signing_token"]
        field_id = ready_envelope["field_id"]

        resp = client.put(
            f"/api/v1/signing/{token}/fields/{field_id}",
            json={"value": "John Doe"},
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == "John Doe"

    async def test_submit_field_empty_value_returns_422(self, client, ready_envelope):
        token = ready_envelope["signing_token"]
        field_id = ready_envelope["field_id"]

        resp = client.put(
            f"/api/v1/signing/{token}/fields/{field_id}",
            json={"value": ""},
        )
        assert resp.status_code == 422

    async def test_complete_signing_without_filling_required_fields_returns_400(
        self, client, ready_envelope
    ):
        token = ready_envelope["signing_token"]
        resp = client.post(f"/api/v1/signing/{token}/complete")
        assert resp.status_code == 400
        assert "errors" in resp.json()["detail"]

    async def test_complete_signing_after_filling_fields(self, client, ready_envelope):
        token = ready_envelope["signing_token"]
        field_id = ready_envelope["field_id"]

        # Fill the required field
        client.put(
            f"/api/v1/signing/{token}/fields/{field_id}",
            json={"value": "Signed by Bob"},
        )

        with patch("dataseal.tasks.finalize.finalize_envelope.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            resp = client.post(f"/api/v1/signing/{token}/complete")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "signed"

    async def test_cannot_sign_again_after_completion(self, client, ready_envelope):
        token = ready_envelope["signing_token"]
        field_id = ready_envelope["field_id"]

        # Fill field and complete
        client.put(f"/api/v1/signing/{token}/fields/{field_id}", json={"value": "Bob"})
        with patch("dataseal.tasks.finalize.finalize_envelope.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            client.post(f"/api/v1/signing/{token}/complete")

        # Try to use token again - should be invalidated
        resp = client.get(f"/api/v1/signing/{token}")
        assert resp.status_code == 404  # token cleared

    async def test_decline_signing(self, client, ready_envelope):
        token = ready_envelope["signing_token"]

        with patch("dataseal.tasks.emails.send_decline_notification.delay"), \
             patch("dataseal.tasks.webhooks.dispatch_webhook_event.delay"):
            resp = client.post(
                f"/api/v1/signing/{token}/decline",
                params={"reason": "Not ready to sign"},
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "declined"
