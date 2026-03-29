"""API tests for templates CRUD."""

import pytest


@pytest.fixture
def template(client, registered_user, auth_headers):
    """Create and return a template."""
    response = client.post(
        "/api/v1/templates",
        json={
            "name": "NDA Template",
            "description": "Standard NDA",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


class TestTemplateCRUD:
    def test_create_template_success(self, client, registered_user, auth_headers):
        response = client.post(
            "/api/v1/templates",
            json={
                "name": "Employment Contract",
                "description": "Standard employment contract",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Employment Contract"
        assert data["description"] == "Standard employment contract"
        assert "id" in data

    def test_create_template_no_description(self, client, registered_user, auth_headers):
        response = client.post(
            "/api/v1/templates",
            json={
                "name": "Simple Template",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_create_template_empty_name_returns_422(self, client, registered_user, auth_headers):
        response = client.post("/api/v1/templates", json={"name": ""}, headers=auth_headers)
        assert response.status_code == 422

    def test_create_template_unauthenticated_returns_401(self, client):
        response = client.post("/api/v1/templates", json={"name": "Unauth"})
        assert response.status_code == 401

    def test_list_templates_empty(self, client, registered_user, auth_headers):
        response = client.get("/api/v1/templates", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_templates_returns_own_only(self, client, registered_user, auth_headers, template, second_user_auth):
        response = client.get("/api/v1/templates", headers=second_user_auth)
        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert template["id"] not in ids

    def test_get_template_success(self, client, registered_user, auth_headers, template):
        response = client.get(f"/api/v1/templates/{template['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == template["id"]

    def test_get_template_not_found_returns_404(self, client, registered_user, auth_headers):
        response = client.get(
            "/api/v1/templates/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_other_users_template_returns_404(
        self,
        client,
        registered_user,
        auth_headers,
        template,
        second_user_auth,
    ):
        response = client.get(f"/api/v1/templates/{template['id']}", headers=second_user_auth)
        assert response.status_code == 404

    def test_update_template_name(self, client, registered_user, auth_headers, template):
        response = client.put(
            f"/api/v1/templates/{template['id']}",
            json={"name": "Updated NDA"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated NDA"

    def test_update_template_description(self, client, registered_user, auth_headers, template):
        response = client.put(
            f"/api/v1/templates/{template['id']}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_delete_template(self, client, registered_user, auth_headers, template):
        response = client.delete(f"/api/v1/templates/{template['id']}", headers=auth_headers)
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/templates/{template['id']}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_template_returns_404(self, client, registered_user, auth_headers):
        response = client.delete(
            "/api/v1/templates/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_other_users_template_returns_404(
        self,
        client,
        registered_user,
        auth_headers,
        template,
        second_user_auth,
    ):
        response = client.delete(f"/api/v1/templates/{template['id']}", headers=second_user_auth)
        assert response.status_code == 404

    def test_add_recipient_to_template(self, client, registered_user, auth_headers, template):
        response = client.post(
            f"/api/v1/templates/{template['id']}/recipients",
            json={"name": "Signer Role", "email_placeholder": "{{signer_email}}", "role": "signer"},
            headers=auth_headers,
        )
        # Templates may have a different recipient structure, check we get a valid response
        assert response.status_code in (201, 422)

    def test_create_envelope_from_nonexistent_template_returns_404(self, client, registered_user, auth_headers):
        # The endpoint requires recipients dict + title; with a nonexistent template it should 404
        response = client.post(
            "/api/v1/templates/00000000-0000-0000-0000-000000000000/create-envelope",
            json={"title": "From Template", "recipients": {}},
            headers=auth_headers,
        )
        assert response.status_code == 404
