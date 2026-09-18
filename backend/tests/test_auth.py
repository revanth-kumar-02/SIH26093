import pytest
import uuid
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import create_access_token, create_refresh_token, decode_token
from app.db.models.responder import UserRole

client = TestClient(app)

def test_supabase_jwt_structure_and_decode():
    """Verify Supabase formatted JWT token creation and decoding."""
    test_uuid = str(uuid.uuid4())
    token = create_access_token(
        subject=test_uuid,
        role="ADMIN",
        extra_claims={"email": "supabase_admin@nhaa.gov.in", "display_name": "Supabase Admin"}
    )
    payload = decode_token(token)
    assert payload["sub"] == test_uuid
    assert payload["app_metadata"]["role"] == "ADMIN"
    assert payload["user_metadata"]["role"] == "ADMIN"
    assert payload["email"] == "supabase_admin@nhaa.gov.in"

def test_auth_login_admin_success():
    """Verify ADMIN development token issuance succeeds and returns role ADMIN."""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin_user",
        "password": "dev-token-request"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "ADMIN"
    assert data["display_name"] == "System Administrator"

def test_auth_login_people_success():
    """Verify PEOPLE development token issuance succeeds and returns role PEOPLE."""
    response = client.post("/api/v1/auth/login", json={
        "username": "people_user",
        "password": "dev-token-request"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "PEOPLE"
    assert data["display_name"] == "Citizen / Complainant"

def test_auth_login_with_email_success():
    response = client.post("/api/v1/auth/login", json={
        "username": "admin@nhaa.gov.in",
        "password": "dev-token-request"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "ADMIN"

def test_auth_login_nonexistent_user():
    response = client.post("/api/v1/auth/login", json={
        "username": "unknown_user_999",
        "password": "SomePassword@123"
    })
    assert response.status_code == 401
    err = response.json()
    assert "error" in err
    assert err["error"]["code"] == "INVALID_CREDENTIALS"

def test_old_roles_rejected():
    """Verify old roles RESPONDER and SUPERVISOR accounts do not exist."""
    resp1 = client.post("/api/v1/auth/login", json={
        "username": "responder_user",
        "password": "ResponderPassword@123"
    })
    assert resp1.status_code == 401

    resp2 = client.post("/api/v1/auth/login", json={
        "username": "supervisor_user",
        "password": "SupervisorPassword@123"
    })
    assert resp2.status_code == 401

def test_auth_me_authenticated():
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_user",
        "password": "dev-token-request"
    })
    token = login_resp.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    profile = response.json()
    assert profile["username"] == "admin_user"
    assert profile["email"] == "admin@nhaa.gov.in"
    assert profile["role"] == "ADMIN"
    assert profile["is_active"] is True

def test_auth_me_missing_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_auth_me_invalid_token():
    response = client.get("/api/v1/auth/me", headers={
        "Authorization": "Bearer not-a-valid-token-string"
    })
    assert response.status_code == 401

def test_auth_me_expired_token():
    expired_token = create_access_token(
        subject="test-id",
        role="ADMIN",
        expires_delta=timedelta(seconds=-10)
    )
    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {expired_token}"
    })
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"

def test_supabase_jit_profile_provisioning():
    """Verify that a valid Supabase JWT for a new user auto-provisions a PostgreSQL profile."""
    new_sub_uuid = str(uuid.uuid4())
    supabase_jwt = create_access_token(
        subject=new_sub_uuid,
        role="PEOPLE",
        extra_claims={
            "email": f"new_victim_{new_sub_uuid[:6]}@example.com",
            "display_name": "New Complainant"
        }
    )

    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {supabase_jwt}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == new_sub_uuid
    assert data["role"] == "PEOPLE"
    assert data["display_name"] == "New Complainant"

def test_supabase_auth_sync_endpoint():
    """Verify /api/v1/auth/sync endpoint provisions/syncs profile from Supabase token."""
    sync_uuid = str(uuid.uuid4())
    token = create_access_token(
        subject=sync_uuid,
        role="PEOPLE",
        extra_claims={
            "email": f"sync_user_{sync_uuid[:6]}@example.com",
        }
    )
    response = client.post("/api/v1/auth/sync", json={
        "access_token": token,
        "display_name": "Synced User Name"
    })
    assert response.status_code == 200
    res = response.json()
    assert res["id"] == sync_uuid
    assert res["display_name"] == "Synced User Name"
    assert res["role"] == "PEOPLE"

def test_auth_refresh_token_flow():
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_user",
        "password": "dev-token-request"
    })
    tokens = login_resp.json()
    refresh_token = tokens["refresh_token"]

    import time
    time.sleep(1.1)

    refresh_resp = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["access_token"] != tokens["access_token"]

