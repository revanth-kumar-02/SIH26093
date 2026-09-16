import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import hash_password, verify_password, create_access_token, decode_token
from app.db.models.responder import UserRole

client = TestClient(app)

def test_password_hashing_security():
    password = "SecurePassword@2026"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2b$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_auth_login_admin_success():
    """Verify ADMIN login succeeds and returns role ADMIN."""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin_user",
        "password": "AdminPassword@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "ADMIN"
    assert data["display_name"] == "System Administrator"

def test_auth_login_people_success():
    """Verify PEOPLE login succeeds and returns role PEOPLE."""
    response = client.post("/api/v1/auth/login", json={
        "username": "people_user",
        "password": "PeoplePassword@123"
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
        "password": "AdminPassword@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "ADMIN"

def test_auth_login_invalid_password():
    response = client.post("/api/v1/auth/login", json={
        "username": "admin_user",
        "password": "IncorrectPassword"
    })
    assert response.status_code == 401
    err = response.json()
    assert "error" in err
    assert err["error"]["code"] == "INVALID_CREDENTIALS"

def test_auth_login_nonexistent_user():
    response = client.post("/api/v1/auth/login", json={
        "username": "unknown_user_999",
        "password": "SomePassword@123"
    })
    assert response.status_code == 401
    err = response.json()
    assert err["error"]["code"] == "INVALID_CREDENTIALS"

def test_old_roles_rejected():
    """Verify old roles RESPONDER and SUPERVISOR accounts do not exist and are rejected."""
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
        "password": "AdminPassword@123"
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

def test_auth_refresh_token_flow():
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_user",
        "password": "AdminPassword@123"
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
