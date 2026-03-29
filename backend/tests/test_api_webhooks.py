"""API tests for webhook management endpoints."""

import pytest


@pytest.fixture
def webhook(client, registered_user, auth_headers):
    """Create and return a webhook endpoint."""
    response = client.post(
        "/api/v1/webhooks",
        json={
            "url": "https://example.com/webhook",
            "events": ["envelope.sent", "envelope.completed"],
            "is_active": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


class TestWebhookCRUD:
    def test_create_webhook_success(self, client, registered_user, auth_headers):
        response = client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/hook",
                "events": ["envelope.sent"],
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://example.com/hook"
        assert "envelope.sent" in data["events"]
        # Note: secret is not exposed in the response schema (security by design)
        assert "secret" not in data
        assert data["is_active"] is True

    def test_create_webhook_with_wildcard_event(self, client, registered_user, auth_headers):
        response = client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/all",
                "events": ["*"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_create_webhook_invalid_event_returns_400(self, client, registered_user, auth_headers):
        response = client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/hook",
                "events": ["invalid.event"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_create_webhook_unauthenticated_returns_401(self, client):
        response = client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/hook",
                "events": ["*"],
            },
        )
        assert response.status_code == 401

    def test_list_webhooks(self, client, registered_user, auth_headers, webhook):
        response = client.get("/api/v1/webhooks", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        ids = [w["id"] for w in items]
        assert webhook["id"] in ids

    def test_list_webhooks_only_own(self, client, registered_user, auth_headers, webhook, second_user_auth):
        response = client.get("/api/v1/webhooks", headers=second_user_auth)
        assert response.status_code == 200
        ids = [w["id"] for w in response.json()]
        assert webhook["id"] not in ids

    def test_get_webhook_success(self, client, registered_user, auth_headers, webhook):
        response = client.get(f"/api/v1/webhooks/{webhook['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == webhook["id"]

    def test_get_webhook_not_found_returns_404(self, client, registered_user, auth_headers):
        response = client.get(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_other_users_webhook_returns_404(
        self,
        client,
        registered_user,
        auth_headers,
        webhook,
        second_user_auth,
    ):
        response = client.get(f"/api/v1/webhooks/{webhook['id']}", headers=second_user_auth)
        assert response.status_code == 404

    def test_update_webhook_url(self, client, registered_user, auth_headers, webhook):
        response = client.put(
            f"/api/v1/webhooks/{webhook['id']}",
            json={"url": "https://updated.example.com/hook"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["url"] == "https://updated.example.com/hook"

    def test_update_webhook_events(self, client, registered_user, auth_headers, webhook):
        response = client.put(
            f"/api/v1/webhooks/{webhook['id']}",
            json={"events": ["envelope.completed"]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["events"] == ["envelope.completed"]

    def test_update_webhook_invalid_event_returns_400(self, client, registered_user, auth_headers, webhook):
        response = client.put(
            f"/api/v1/webhooks/{webhook['id']}",
            json={"events": ["not.valid"]},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_update_webhook_deactivate(self, client, registered_user, auth_headers, webhook):
        response = client.put(
            f"/api/v1/webhooks/{webhook['id']}",
            json={"is_active": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_delete_webhook(self, client, registered_user, auth_headers, webhook):
        response = client.delete(f"/api/v1/webhooks/{webhook['id']}", headers=auth_headers)
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/webhooks/{webhook['id']}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_webhook_returns_404(self, client, registered_user, auth_headers):
        response = client.delete(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_other_users_webhook_returns_404(
        self,
        client,
        registered_user,
        auth_headers,
        webhook,
        second_user_auth,
    ):
        response = client.delete(f"/api/v1/webhooks/{webhook['id']}", headers=second_user_auth)
        assert response.status_code == 404

    def test_list_deliveries_empty(self, client, registered_user, auth_headers, webhook):
        response = client.get(
            f"/api/v1/webhooks/{webhook['id']}/deliveries",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_test_webhook_enqueues_delivery(self, client, registered_user, auth_headers, webhook):
        response = client.post(f"/api/v1/webhooks/{webhook['id']}/test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "delivery_id" in data

    def test_test_nonexistent_webhook_returns_404(self, client, registered_user, auth_headers):
        response = client.post(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000000/test",
            headers=auth_headers,
        )
        assert response.status_code == 404
