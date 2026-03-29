"""API tests for authentication endpoints."""


class TestRegister:
    def test_register_success(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "Password123!",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "password_hash" not in data

    def test_register_with_company(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "corp@example.com",
                "password": "Password123!",
                "full_name": "Corp User",
                "company": "Acme Inc",
            },
        )
        assert response.status_code == 201
        assert response.json()["company"] == "Acme Inc"

    def test_register_duplicate_email_returns_409(self, client):
        payload = {
            "email": "dup@example.com",
            "password": "Password123!",
            "full_name": "Dup User",
        }
        client.post("/api/v1/auth/register", json=payload)
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    def test_register_invalid_email_returns_422(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "Password123!",
                "full_name": "Bad Email",
            },
        )
        assert response.status_code == 422

    def test_register_short_password_returns_422(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "password": "abc",
                "full_name": "Short Pass",
            },
        )
        assert response.status_code == 422

    def test_register_empty_full_name_returns_422(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "empty@example.com",
                "password": "Password123!",
                "full_name": "",
            },
        )
        assert response.status_code == 422

    def test_register_missing_fields_returns_422(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "missing@example.com",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client, registered_user):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_wrong_password_returns_401(self, client, registered_user):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "WrongPassword!",
            },
        )
        assert response.status_code == 401

    def test_login_unknown_email_returns_401(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "ghost@example.com",
                "password": "Password123!",
            },
        )
        assert response.status_code == 401

    def test_login_invalid_email_format_returns_422(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-valid",
                "password": "Password123!",
            },
        )
        assert response.status_code == 422


class TestRefreshToken:
    def test_refresh_token_returns_new_tokens(self, client, registered_user):
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPass123!",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_access_token_returns_401(self, client, registered_user, auth_token):
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": auth_token})
        assert response.status_code == 401

    def test_refresh_with_invalid_token_returns_401(self, client):
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.token.here"})
        assert response.status_code == 401


class TestGetProfile:
    def test_get_profile_authenticated(self, client, registered_user, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["full_name"] == "Test User"

    def test_get_profile_unauthenticated_returns_401(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_profile_with_invalid_token_returns_401(self, client):
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt"})
        assert response.status_code == 401


class TestUpdateProfile:
    def test_update_profile_full_name(self, client, registered_user, auth_headers):
        response = client.put("/api/v1/auth/me", json={"full_name": "Updated Name"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    def test_update_profile_company(self, client, registered_user, auth_headers):
        response = client.put("/api/v1/auth/me", json={"company": "New Company"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["company"] == "New Company"

    def test_update_profile_unauthenticated_returns_401(self, client):
        response = client.put("/api/v1/auth/me", json={"full_name": "Hack"})
        assert response.status_code == 401


class TestApiKeys:
    def test_create_api_key(self, client, registered_user, auth_headers):
        response = client.post("/api/v1/auth/api-keys", json={"name": "My Key"}, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Key"
        assert "key" in data
        assert data["key"].startswith("ds_key_")
        assert data["is_active"] is True

    def test_list_api_keys(self, client, registered_user, auth_headers):
        client.post("/api/v1/auth/api-keys", json={"name": "Key 1"}, headers=auth_headers)
        client.post("/api/v1/auth/api-keys", json={"name": "Key 2"}, headers=auth_headers)
        response = client.get("/api/v1/auth/api-keys", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_revoke_api_key(self, client, registered_user, auth_headers):
        create_response = client.post("/api/v1/auth/api-keys", json={"name": "Revoke Me"}, headers=auth_headers)
        key_id = create_response.json()["id"]
        response = client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=auth_headers)
        assert response.status_code == 204

    def test_revoke_nonexistent_key_returns_404(self, client, registered_user, auth_headers):
        response = client.delete(
            "/api/v1/auth/api-keys/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_cannot_revoke_other_users_key(self, client, registered_user, auth_headers, second_user_auth):
        # Create key as first user
        create_response = client.post("/api/v1/auth/api-keys", json={"name": "First User Key"}, headers=auth_headers)
        key_id = create_response.json()["id"]
        # Try to revoke as second user
        response = client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=second_user_auth)
        assert response.status_code == 404

    def test_api_key_auth_works(self, client, registered_user, auth_headers):
        create_response = client.post("/api/v1/auth/api-keys", json={"name": "API Auth Key"}, headers=auth_headers)
        raw_key = create_response.json()["key"]
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {raw_key}"})
        assert response.status_code == 200

    def test_logout(self, client, registered_user, auth_headers):
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 204
