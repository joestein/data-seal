"""API tests for recipients and fields management."""

import io

import pytest


@pytest.fixture
def envelope(client, registered_user, auth_headers):
    """Create a test envelope."""
    response = client.post(
        "/api/v1/envelopes",
        json={
            "title": "Recipient Test Envelope",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def recipient(client, registered_user, auth_headers, envelope):
    """Add a recipient to the envelope."""
    response = client.post(
        f"/api/v1/envelopes/{envelope['id']}/recipients",
        json={"name": "Alice Signer", "email": "alice@example.com", "role": "signer"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()[0]


@pytest.fixture
def document(client, registered_user, auth_headers, envelope):
    """Upload a fake document to the envelope."""
    fake_pdf = b"%PDF-1.4 fake content for test purposes only"
    response = client.post(
        f"/api/v1/envelopes/{envelope['id']}/documents",
        files={"file": ("test.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        headers=auth_headers,
    )
    # The upload may fail due to PDF validation, but we still need a document for field tests
    # We'll handle this gracefully
    return response


class TestRecipientsAPI:
    def test_add_single_recipient(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            json={"name": "Bob Smith", "email": "bob@example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Bob Smith"
        assert data[0]["email"] == "bob@example.com"
        assert data[0]["role"] == "signer"
        assert data[0]["routing_order"] == 1

    def test_add_recipient_as_cc(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            json={"name": "CC User", "email": "cc@example.com", "role": "cc"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()[0]["role"] == "cc"

    def test_add_multiple_recipients_via_list(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            json=[
                {"name": "Signer 1", "email": "s1@example.com"},
                {"name": "Signer 2", "email": "s2@example.com"},
            ],
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert len(response.json()) == 2

    def test_add_recipient_with_routing_order(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            json={"name": "Second", "email": "second@example.com", "routing_order": 2},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()[0]["routing_order"] == 2

    def test_add_recipient_invalid_role_returns_422(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            json={"name": "Bad Role", "email": "role@example.com", "role": "admin"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_add_recipient_invalid_email_returns_422(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            json={"name": "Bad Email", "email": "not-an-email"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_list_recipients(self, client, registered_user, auth_headers, envelope, recipient):
        response = client.get(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            headers=auth_headers,
        )
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 1
        ids = [r["id"] for r in items]
        assert recipient["id"] in ids

    def test_update_recipient_name(self, client, registered_user, auth_headers, envelope, recipient):
        response = client.put(
            f"/api/v1/envelopes/{envelope['id']}/recipients/{recipient['id']}",
            json={"name": "Alice Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Alice Updated"

    def test_update_recipient_email(self, client, registered_user, auth_headers, envelope, recipient):
        response = client.put(
            f"/api/v1/envelopes/{envelope['id']}/recipients/{recipient['id']}",
            json={"email": "alice_new@example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["email"] == "alice_new@example.com"

    def test_update_nonexistent_recipient_returns_404(self, client, registered_user, auth_headers, envelope):
        response = client.put(
            f"/api/v1/envelopes/{envelope['id']}/recipients/00000000-0000-0000-0000-000000000000",
            json={"name": "Ghost"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_recipient(self, client, registered_user, auth_headers, envelope):
        add_response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            json={"name": "Delete Me", "email": "deleteme@example.com"},
            headers=auth_headers,
        )
        recipient_id = add_response.json()[0]["id"]
        response = client.delete(
            f"/api/v1/envelopes/{envelope['id']}/recipients/{recipient_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_delete_nonexistent_recipient_returns_404(self, client, registered_user, auth_headers, envelope):
        response = client.delete(
            f"/api/v1/envelopes/{envelope['id']}/recipients/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_recipient_unauthenticated_returns_401(self, client, envelope):
        response = client.get(f"/api/v1/envelopes/{envelope['id']}/recipients")
        assert response.status_code == 401

    def test_recipient_on_other_users_envelope_returns_404(
        self,
        client,
        registered_user,
        auth_headers,
        envelope,
        second_user_auth,
    ):
        response = client.get(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            headers=second_user_auth,
        )
        assert response.status_code == 404

    def test_add_recipient_zero_routing_order_returns_422(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/recipients",
            json={"name": "Bad Order", "email": "order@example.com", "routing_order": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestFieldsAPI:
    """Tests for fields require documents, which require real PDF upload/validation.
    We test the field schema validation directly and test fields on mock documents
    where possible.
    """

    def test_field_type_validation_via_schema(self):
        """Verify field type validation at schema level."""
        import uuid

        from pydantic import ValidationError

        from dataseal.schemas.field import FieldCreate

        with pytest.raises(ValidationError):
            FieldCreate(
                recipient_id=uuid.uuid4(),
                type="invalid",
                page_number=1,
                x_position=10.0,
                y_position=10.0,
                width=10.0,
                height=5.0,
            )

    def test_field_coordinate_out_of_range_validation(self):
        import uuid

        from pydantic import ValidationError

        from dataseal.schemas.field import FieldCreate

        with pytest.raises(ValidationError):
            FieldCreate(
                recipient_id=uuid.uuid4(),
                type="text",
                page_number=1,
                x_position=200.0,  # out of range
                y_position=10.0,
                width=10.0,
                height=5.0,
            )

    def test_list_fields_on_nonexistent_document_returns_404(self, client, registered_user, auth_headers, envelope):
        response = client.get(
            f"/api/v1/envelopes/{envelope['id']}/documents/00000000-0000-0000-0000-000000000000/fields",
            headers=auth_headers,
        )
        assert response.status_code == 404
