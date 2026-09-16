import pytest
from starlette.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def get_tokens(client):
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminPassword@123"}
    )
    admin_token = admin_login.json()["access_token"]

    people_login = client.post(
        "/api/v1/auth/login",
        json={"username": "people_user", "password": "PeoplePassword@123"}
    )
    people_token = people_login.json()["access_token"]

    return {
        "admin": admin_token,
        "people": people_token
    }

def test_people_role_denied_admin_portal_endpoints(client):
    """Verify that a user with role PEOPLE receives HTTP 403 when attempting to access administrative/responder endpoints."""
    tokens = get_tokens(client)
    people_headers = {"Authorization": f"Bearer {tokens['people']}"}

    # 1. PEOPLE attempting to list cases -> 403 FORBIDDEN
    res_cases = client.get("/api/v1/responder/cases", headers=people_headers)
    assert res_cases.status_code == 403
    assert res_cases.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # 2. PEOPLE attempting to get a case detail -> 403 FORBIDDEN
    res_detail = client.get("/api/v1/responder/cases/some-case-id", headers=people_headers)
    assert res_detail.status_code == 403
    assert res_detail.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # 3. PEOPLE attempting to assign case -> 403 FORBIDDEN
    res_assign = client.post(
        "/api/v1/responder/cases/some-case-id/assign",
        json={"responder_id": "any-id"},
        headers=people_headers
    )
    assert res_assign.status_code == 403
    assert res_assign.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # 4. PEOPLE attempting to update status -> 403 FORBIDDEN
    res_status = client.post(
        "/api/v1/responder/cases/some-case-id/status",
        json={"status": "CLOSED"},
        headers=people_headers
    )
    assert res_status.status_code == 403
    assert res_status.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # 5. PEOPLE attempting to review recommendation -> 403 FORBIDDEN
    res_review = client.post(
        "/api/v1/responder/cases/some-case-id/recommendations/some-rec-id/review",
        json={"decision": "ACCEPT"},
        headers=people_headers
    )
    assert res_review.status_code == 403
    assert res_review.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # 6. PEOPLE attempting to view audit trail -> 403 FORBIDDEN
    res_audit = client.get("/api/v1/responder/cases/some-case-id/audit", headers=people_headers)
    assert res_audit.status_code == 403
    assert res_audit.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

def test_admin_role_access_authorized(client):
    """Verify that a user with role ADMIN is authorized to access administrative endpoints."""
    tokens = get_tokens(client)
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}

    res_cases = client.get("/api/v1/responder/cases", headers=admin_headers)
    assert res_cases.status_code == 200
    assert "items" in res_cases.json()

def test_invalid_and_expired_jwt_handling(client):
    """Verify invalid or malformed tokens fail safely without stack trace leakage."""
    res = client.get(
        "/api/v1/responder/cases",
        headers={"Authorization": "Bearer not-a-valid-token-string"}
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] in ["INVALID_TOKEN", "AUTHENTICATION_FAILED"]

    res_no_auth = client.get("/api/v1/responder/cases")
    assert res_no_auth.status_code == 401

def test_recommendation_review_idempotency(client):
    """Verify repeated recommendation reviews with same decision do not duplicate audit records."""
    tokens = get_tokens(client)
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}

    case_c_res = client.get(
        "/api/v1/responder/cases?search=NHAA-2026-SYN-0815",
        headers=admin_headers
    )
    assert case_c_res.status_code == 200
    items = case_c_res.json()["items"]
    assert len(items) > 0
    case_id = items[0]["id"]

    detail = client.get(
        f"/api/v1/responder/cases/{case_id}",
        headers=admin_headers
    ).json()
    assert len(detail["recommendations"]) > 0
    rec_id = detail["recommendations"][0]["id"]

    audit_before = client.get(
        f"/api/v1/responder/cases/{case_id}/audit",
        headers=admin_headers
    ).json()
    count_before = len(audit_before)

    # Review 1
    rev1 = client.post(
        f"/api/v1/responder/cases/{case_id}/recommendations/{rec_id}/review",
        json={
            "decision": "ACCEPT",
            "responder_note": "Verified DLSA referral eligibility."
        },
        headers=admin_headers
    )
    assert rev1.status_code == 200

    audit_after_rev1 = client.get(
        f"/api/v1/responder/cases/{case_id}/audit",
        headers=admin_headers
    ).json()
    count_after_rev1 = len(audit_after_rev1)
    assert count_after_rev1 == count_before + 1

    # Review 2 (IDEMPOTENCY TEST)
    rev2 = client.post(
        f"/api/v1/responder/cases/{case_id}/recommendations/{rec_id}/review",
        json={
            "decision": "ACCEPT",
            "responder_note": "Verified DLSA referral eligibility."
        },
        headers=admin_headers
    )
    assert rev2.status_code == 200

    audit_after_rev2 = client.get(
        f"/api/v1/responder/cases/{case_id}/audit",
        headers=admin_headers
    ).json()
    count_after_rev2 = len(audit_after_rev2)
    assert count_after_rev2 == count_after_rev1

def test_invalid_status_transition_rejection(client):
    """Verify invalid status transitions (e.g., NEW directly to ACTION_RECORDED) are rejected."""
    tokens = get_tokens(client)
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}

    case_b_res = client.get(
        "/api/v1/responder/cases?search=NHAA-2026-SYN-0820",
        headers=admin_headers
    )
    assert case_b_res.status_code == 200
    case_id = case_b_res.json()["items"][0]["id"]

    # Assign to admin
    admin_id = client.get("/api/v1/auth/me", headers=admin_headers).json()["id"]
    client.post(
        f"/api/v1/responder/cases/{case_id}/assign",
        json={"responder_id": admin_id},
        headers=admin_headers
    )

    # Attempt illegal jump: IN_REVIEW directly to ACTION_RECORDED
    illegal_trans = client.post(
        f"/api/v1/responder/cases/{case_id}/status",
        json={"status": "ACTION_RECORDED"},
        headers=admin_headers
    )
    assert illegal_trans.status_code == 400
    assert illegal_trans.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

def test_sql_injection_safe_search(client):
    """Verify malformed search strings with SQL injection payloads fail safely."""
    tokens = get_tokens(client)
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}

    sqli_payload = "' OR 1=1; DROP TABLE cases; --"
    res = client.get(
        f"/api/v1/responder/cases?search={sqli_payload}",
        headers=admin_headers
    )
    assert res.status_code == 200
    assert res.json()["total"] == 0
