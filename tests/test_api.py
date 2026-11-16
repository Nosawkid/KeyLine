from datetime import UTC, datetime, timedelta

import pytest


async def register(client, email="owner@example.com"):
    response = client.post("/auth/register", json={"email": email, "password": "a-strong-password"})
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_registration_login_and_application_ownership(client):
    token = await register(client)
    headers = {"Authorization": f"Bearer {token}"}
    app = client.post("/applications", json={"name": "Acme"}, headers=headers)
    assert app.status_code == 201
    other_token = await register(client, "other@example.com")
    response = client.get(f"/applications/{app.json()['id']}", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 404
    assert client.post("/auth/login", json={"email": "owner@example.com", "password": "bad"}).status_code == 401


@pytest.mark.asyncio
async def test_dashboard_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Security, made" in response.text


@pytest.mark.asyncio
async def test_key_authentication_revocation_and_usage(client):
    token = await register(client)
    headers = {"Authorization": f"Bearer {token}"}
    app_id = client.post("/applications", json={"name": "Acme"}, headers=headers).json()["id"]
    created = client.post(f"/applications/{app_id}/keys", json={"name": "server"}, headers=headers)
    assert created.status_code == 201
    body = created.json()
    raw_key = body["api_key"]
    key_headers = {"Authorization": f"Bearer {raw_key}"}
    assert client.get("/protected/resource", headers=key_headers).status_code == 200
    assert client.get("/protected/resource", headers=key_headers).status_code == 200
    assert client.get("/protected/resource", headers=key_headers).status_code == 429
    assert client.delete(f"/keys/{body['id']}", headers=headers).status_code == 204
    assert client.get("/protected/resource", headers=key_headers).status_code == 403
    usage = client.get(f"/keys/{body['id']}/usage", headers=headers)
    assert usage.status_code == 200
    assert usage.json()["total"] == 3


@pytest.mark.asyncio
async def test_expired_key_is_rejected(client):
    token = await register(client)
    headers = {"Authorization": f"Bearer {token}"}
    app_id = client.post("/applications", json={"name": "Acme"}, headers=headers).json()["id"]
    expires = (datetime.now(UTC) + timedelta(seconds=1)).isoformat()
    created = client.post(f"/applications/{app_id}/keys", json={"name": "soon", "expires_at": expires}, headers=headers)
    assert created.status_code == 201
    import time
    time.sleep(1.05)
    assert client.get("/protected/resource", headers={"Authorization": f"Bearer {created.json()['api_key']}"}).status_code == 403
