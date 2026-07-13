import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["msg"] == "User created"
    assert data["username"] == "newuser"


@pytest.mark.asyncio
async def test_register_duplicate_username(client, registered_user):
    response = await client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "other@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "mavjud" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client, registered_user):
    response = await client.post(
        "/auth/register",
        json={
            "username": "otheruser",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "mavjud" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client, registered_user):
    response = await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "password123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, registered_user):
    response = await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert "noto'g'ri" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(client, registered_user):
    await client.patch(
        "/auth/update-profile",
        json={"is_active": False},
        headers=(await _login_headers(client)),
    )

    response = await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "password123"},
    )

    assert response.status_code == 403
    assert "faol emas" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token(client, auth_tokens):
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": auth_tokens["refresh_token"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid.token"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client, auth_headers):
    response = await client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client, auth_headers):
    response = await client.patch(
        "/auth/update-profile",
        json={"username": "updateduser"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updateduser"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_change_password_success(client, auth_headers):
    response = await client.patch(
        "/auth/change-password",
        json={
            "old_password": "password123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["msg"] == "Parol uzgartirildi"

    login_response = await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "newpassword456"},
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old_password(client, auth_headers):
    response = await client.patch(
        "/auth/change-password",
        json={
            "old_password": "wrong",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456",
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "Eski parol" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_mismatch(client, auth_headers):
    response = await client.patch(
        "/auth/change-password",
        json={
            "old_password": "password123",
            "new_password": "newpassword456",
            "confirm_password": "different",
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "mos emas" in response.json()["detail"]


@pytest.mark.asyncio
async def test_logout(client, auth_headers, auth_tokens):
    response = await client.post(
        "/auth/logout",
        json={"refresh": auth_tokens["refresh_token"]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["msg"] == "Logout"

    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": auth_tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 401


async def _login_headers(client):
    response = await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
