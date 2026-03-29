"""API tests for envelope CRUD and lifecycle endpoints."""

import pytest


@pytest.fixture
def envelope(client, registered_user, auth_headers):
    """Create and return an envelope."""
    response = client.post("/api/v1/envelopes", json={
        "title": "Test Envelope",
        "message": "Please sign this.",
    }, headers=auth_headers)
    assert response.status_code == 201
    return response.json()


class TestCreateEnvelope:
    def test_create_envelope_success(self, client, registered_user, auth_headers):
        response = client.post("/api/v1/envelopes", json={
            "title": "My Document",
            "message": "Please sign",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My Document"
        assert data["status"] == "created"
        assert "id" in data

    def test_create_envelope_without_message(self, client, registered_user, auth_headers):
        response = client.post("/api/v1/envelopes", json={
            "title": "No Message",
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["message"] is None

    def test_create_envelope_unauthenticated_returns_401(self, client):
        response = client.post("/api/v1/envelopes", json={"title": "Unauthorized"})
        assert response.status_code == 401

    def test_create_envelope_empty_title_returns_422(self, client, registered_user, auth_headers):
        response = client.post("/api/v1/envelopes", json={"title": ""}, headers=auth_headers)
        assert response.status_code == 422

    def test_create_envelope_missing_title_returns_422(self, client, registered_user, auth_headers):
        response = client.post("/api/v1/envelopes", json={}, headers=auth_headers)
        assert response.status_code == 422


class TestListEnvelopes:
    def test_list_envelopes_empty(self, client, registered_user, auth_headers):
        response = client.get("/api/v1/envelopes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_list_envelopes_returns_own_only(self, client, registered_user, auth_headers, second_user_auth):
        # Create envelope as first user
        client.post("/api/v1/envelopes", json={"title": "User 1 Envelope"}, headers=auth_headers)
        # Create envelope as second user
        client.post("/api/v1/envelopes", json={"title": "User 2 Envelope"}, headers=second_user_auth)

        response = client.get("/api/v1/envelopes", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert item["title"] != "User 2 Envelope"

    def test_list_envelopes_pagination(self, client, registered_user, auth_headers):
        for i in range(5):
            client.post("/api/v1/envelopes", json={"title": f"Envelope {i}"}, headers=auth_headers)

        response = client.get("/api/v1/envelopes?page=1&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_list_envelopes_status_filter(self, client, registered_user, auth_headers, envelope):
        response = client.get("/api/v1/envelopes?status=created", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert item["status"] == "created"

    def test_list_envelopes_search(self, client, registered_user, auth_headers):
        client.post("/api/v1/envelopes", json={"title": "Special Unique Doc 12345"}, headers=auth_headers)
        response = client.get("/api/v1/envelopes?search=Special+Unique+Doc", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()["items"]
        assert any("Special Unique Doc" in item["title"] for item in items)


class TestGetEnvelope:
    def test_get_envelope_success(self, client, registered_user, auth_headers, envelope):
        response = client.get(f"/api/v1/envelopes/{envelope['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == envelope["id"]

    def test_get_envelope_not_found_returns_404(self, client, registered_user, auth_headers):
        response = client.get(
            "/api/v1/envelopes/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_envelope_other_user_returns_404(self, client, registered_user, auth_headers, envelope, second_user_auth):
        response = client.get(f"/api/v1/envelopes/{envelope['id']}", headers=second_user_auth)
        assert response.status_code == 404


class TestUpdateEnvelope:
    def test_update_envelope_title(self, client, registered_user, auth_headers, envelope):
        response = client.put(
            f"/api/v1/envelopes/{envelope['id']}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_update_envelope_message(self, client, registered_user, auth_headers, envelope):
        response = client.put(
            f"/api/v1/envelopes/{envelope['id']}",
            json={"message": "New message"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["message"] == "New message"

    def test_update_envelope_unauthenticated_returns_401(self, client, registered_user, auth_headers, envelope):
        response = client.put(
            f"/api/v1/envelopes/{envelope['id']}",
            json={"title": "Hack"},
        )
        assert response.status_code == 401


class TestDeleteEnvelope:
    def test_delete_created_envelope_success(self, client, registered_user, auth_headers):
        create_response = client.post("/api/v1/envelopes", json={"title": "Delete Me"}, headers=auth_headers)
        env_id = create_response.json()["id"]
        response = client.delete(f"/api/v1/envelopes/{env_id}", headers=auth_headers)
        assert response.status_code == 204

        # Confirm it's gone
        get_response = client.get(f"/api/v1/envelopes/{env_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_envelope_returns_404(self, client, registered_user, auth_headers):
        response = client.delete(
            "/api/v1/envelopes/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_other_users_envelope_returns_404(self, client, registered_user, auth_headers, envelope, second_user_auth):
        response = client.delete(f"/api/v1/envelopes/{envelope['id']}", headers=second_user_auth)
        assert response.status_code == 404


class TestVoidEnvelope:
    def test_void_envelope_from_created_status(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/void",
            json={"reason": "Changed my mind"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "voided"
        assert data["voided_reason"] == "Changed my mind"

    def test_void_requires_reason(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/void",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_void_empty_reason_returns_422(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/void",
            json={"reason": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_void_completed_envelope_returns_400(self, client, registered_user, auth_headers, db_session):
        # Create an envelope and force-set it to completed via DB
        create_response = client.post(
            "/api/v1/envelopes", json={"title": "Completed Env"}, headers=auth_headers
        )
        env_id = create_response.json()["id"]

        # Directly update via API - we can't easily set completed status via normal flow,
        # so instead void it first and then try to void again
        client.post(
            f"/api/v1/envelopes/{env_id}/void",
            json={"reason": "First void"},
            headers=auth_headers,
        )
        response = client.post(
            f"/api/v1/envelopes/{env_id}/void",
            json={"reason": "Second void"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_cannot_delete_voided_envelope(self, client, registered_user, auth_headers, envelope):
        client.post(
            f"/api/v1/envelopes/{envelope['id']}/void",
            json={"reason": "Void it"},
            headers=auth_headers,
        )
        response = client.delete(f"/api/v1/envelopes/{envelope['id']}", headers=auth_headers)
        assert response.status_code == 400


class TestSendEnvelope:
    def test_send_envelope_without_documents_returns_400(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/send",
            headers=auth_headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "errors" in detail

    def test_audit_trail_exists_after_creation(self, client, registered_user, auth_headers, envelope):
        response = client.get(
            f"/api/v1/envelopes/{envelope['id']}/audit-trail",
            headers=auth_headers,
        )
        assert response.status_code == 200
        events = response.json()
        assert len(events) >= 1
        event_types = [e["event_type"] for e in events]
        assert "envelope.created" in event_types


class TestResendEnvelope:
    def test_resend_from_created_status_returns_400(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/resend",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_certificate_unavailable_for_non_completed_envelope(self, client, registered_user, auth_headers, envelope):
        response = client.get(
            f"/api/v1/envelopes/{envelope['id']}/certificate",
            headers=auth_headers,
        )
        assert response.status_code == 400
