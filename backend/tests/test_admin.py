import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import create_access_token, decode_token
from app.db.models.responder import UserRole

client = TestClient(app)

def get_admin_token() -> str:
    """Helper to authenticate as admin and obtain access token."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin_user",
        "password": "dev-token-request"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]

def get_people_token() -> str:
    """Helper to authenticate as people and obtain access token."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "people_user",
        "password": "dev-token-request"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]

# 1. Supabase Auth Identity Token RBAC Verification
def test_admin_and_people_identity_tokens():
    admin_token = get_admin_token()
    assert admin_token is not None and len(admin_token) > 20
    admin_payload = decode_token(admin_token)
    assert admin_payload["app_metadata"]["role"] == "ADMIN"

    people_token = get_people_token()
    assert people_token is not None and len(people_token) > 20
    people_payload = decode_token(people_token)
    assert people_payload["app_metadata"]["role"] == "PEOPLE"

# 3. PEOPLE Denied Admin APIs (HTTP 403)
def test_people_denied_admin_apis():
    token = get_people_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Dashboard
    resp = client.get("/api/v1/admin/dashboard", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # Cases
    resp = client.get("/api/v1/admin/cases", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # Audit
    resp = client.get("/api/v1/admin/audit", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

# 4. ADMIN Allowed Admin APIs (HTTP 200)
def test_admin_allowed_admin_apis():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/admin/dashboard", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/v1/admin/cases", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/v1/admin/audit", headers=headers)
    assert resp.status_code == 200

# 5. Dashboard Aggregation Structure & Real DB Data
def test_admin_dashboard_aggregation():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/admin/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "active_cases" in data
    assert data["active_cases"] >= 1
    assert "urgent_review" in data
    assert "high_risk" in data
    assert "pending_reviews" in data
    assert "risk_distribution" in data
    assert all(k in data["risk_distribution"] for k in ["LOW", "MODERATE", "HIGH", "CRITICAL"])
    assert "requires_attention_cases" in data
    assert "recent_cases" in data

# 6. Case Listing with Filters and Search
def test_admin_cases_listing_and_filtering():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/admin/cases?page=1&page_size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    # Search by reference
    ref = data["items"][0]["external_case_reference"]
    search_resp = client.get(f"/api/v1/admin/cases?search={ref[:8]}", headers=headers)
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert len(search_data["items"]) >= 1
    assert any(c["external_case_reference"] == ref for c in search_data["items"])

# 7. Case Detail Retrieval
def test_admin_case_detail():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Get a valid case ID
    list_resp = client.get("/api/v1/admin/cases", headers=headers)
    case_id = list_resp.json()["items"][0]["id"]

    detail_resp = client.get(f"/api/v1/admin/cases/{case_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()

    assert detail["id"] == case_id
    assert "external_case_reference" in detail
    assert "conversation_summary" in detail
    assert "svi_result" in detail
    assert "recommendations" in detail

# 8. Audit Log Retrieval (No raw victim conversation)
def test_admin_audit_retrieval():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/admin/audit?page=1&page_size=20", headers=headers)
    assert resp.status_code == 200
    audits = resp.json()
    assert isinstance(audits, list)
    assert len(audits) >= 1

    for audit in audits:
        assert "timestamp" in audit
        assert "actor" in audit
        assert "event" in audit
        assert "entity" in audit
        # Verify no raw victim conversation is exposed in audit details
        details_str = str(audit["details"]).lower()
        assert "raw_text" not in details_str

# 9. Recommendation Review Workflow (Accept, Modify, Reject)
def test_admin_recommendation_review_workflow():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Find a case with recommendations
    list_resp = client.get("/api/v1/admin/cases", headers=headers)
    cases = list_resp.json()["items"]
    target_rec = None
    target_case_id = None

    for c in cases:
        d = client.get(f"/api/v1/admin/cases/{c['id']}", headers=headers).json()
        if d["recommendations"]:
            target_rec = d["recommendations"][0]
            target_case_id = c["id"]
            break

    assert target_rec is not None, "Need at least one recommendation for testing"
    rec_id = target_rec["id"]

    # Modify recommendation
    mod_resp = client.post(
        f"/api/v1/admin/recommendations/{rec_id}/review",
        headers=headers,
        json={
            "decision": "MODIFY",
            "modified_action": "Adjusted action by Admin in testing",
            "modified_priority": "CRITICAL",
            "responder_note": "Case complexity requires accelerated review."
        }
    )
    assert mod_resp.status_code == 200
    mod_data = mod_resp.json()
    assert mod_data["success"] is True
    assert mod_data["decision"] == "MODIFY"
    assert mod_data["responder_action"] == "Adjusted action by Admin in testing"

    # Accept recommendation
    acc_resp = client.post(
        f"/api/v1/admin/recommendations/{rec_id}/review",
        headers=headers,
        json={
            "decision": "ACCEPT",
            "responder_note": "Accepted after human review."
        }
    )
    assert acc_resp.status_code == 200
    acc_data = acc_resp.json()
    assert acc_data["decision"] == "ACCEPT"

# 10. Case Status Lifecycle Change
def test_admin_case_status_change():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = client.get("/api/v1/admin/cases", headers=headers)
    case_id = list_resp.json()["items"][0]["id"]

    # Close case
    close_resp = client.post(
        f"/api/v1/admin/cases/{case_id}/status",
        headers=headers,
        json={"status": "CLOSED"}
    )
    assert close_resp.status_code in (200, 400) # Valid transition or already in terminal

    # Reopen to IN_REVIEW
    reopen_resp = client.post(
        f"/api/v1/admin/cases/{case_id}/status",
        headers=headers,
        json={"status": "IN_REVIEW"}
    )
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["new_status"] == "IN_REVIEW"

# 11. Invalid & Expired JWT Tokens
def test_admin_jwt_security_guards():
    # Invalid token
    resp = client.get("/api/v1/admin/dashboard", headers={"Authorization": "Bearer invalid.token.value"})
    assert resp.status_code == 401

    # Missing token
    resp = client.get("/api/v1/admin/dashboard")
    assert resp.status_code == 401

    # Expired token
    expired_token = create_access_token(
        subject="admin_user",
        role="ADMIN",
        expires_delta=timedelta(seconds=-10)
    )
    resp = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401

# 12. Nonexistent Case ID (404)
def test_admin_nonexistent_case():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/admin/cases/00000000-0000-0000-0000-000000000000", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "CASE_NOT_FOUND"
