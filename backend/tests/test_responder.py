import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_admin_token():
    resp = client.post("/api/v1/auth/login", json={"username": "admin_user", "password": "AdminPassword@123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_responder_cases_list_pagination():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/responder/cases?page=1&page_size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 4
    assert len(data["items"]) >= 4

def test_responder_cases_search_safe_reference():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/responder/cases?search=0812", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert "0812" in data["items"][0]["external_case_reference"]

def test_responder_cases_filter_by_status():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/responder/cases?case_status=NEW", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["status"] == "NEW"

def test_responder_case_detail_structure():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = client.get("/api/v1/responder/cases?search=0812", headers=headers)
    case_id = list_resp.json()["items"][0]["id"]

    detail_resp = client.get(f"/api/v1/responder/cases/{case_id}", headers=headers)
    assert detail_resp.status_code == 200
    c = detail_resp.json()

    assert c["external_case_reference"] == "NHAA-2026-SYN-0812"
    assert c["safety_flags"]["immediate_safety_attention"] is True
    assert c["safety_flags"]["urgent_human_review"] is True
    assert c["svi_result"]["score"] == 88.5
    assert c["svi_result"]["risk_category"] == "CRITICAL"
    assert len(c["recommendations"]) >= 2
    assert c["ai_assessment"] is not None
    assert c["conversation_summary"] is not None

def test_admin_case_assignment_success():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    me_resp = client.get("/api/v1/auth/me", headers=headers)
    admin_id = me_resp.json()["id"]

    list_resp = client.get("/api/v1/responder/cases?search=0820", headers=headers)
    case_id = list_resp.json()["items"][0]["id"]

    assign_resp = client.post(
        f"/api/v1/responder/cases/{case_id}/assign",
        json={"responder_id": admin_id},
        headers=headers
    )
    assert assign_resp.status_code == 200
    data = assign_resp.json()
    assert data["success"] is True
    assert data["assigned_responder_id"] == admin_id

def test_recommendation_review_workflow():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = client.get("/api/v1/responder/cases?search=0812", headers=headers)
    case_id = list_resp.json()["items"][0]["id"]

    detail_resp = client.get(f"/api/v1/responder/cases/{case_id}", headers=headers)
    rec_id = detail_resp.json()["recommendations"][0]["id"]

    review_resp = client.post(
        f"/api/v1/responder/cases/{case_id}/recommendations/{rec_id}/review",
        json={
            "decision": "ACCEPT",
            "responder_note": "Verified with triage protocols. Escalation dispatched to local PCR."
        },
        headers=headers
    )
    assert review_resp.status_code == 200
    rev_data = review_resp.json()
    assert rev_data["success"] is True
    assert rev_data["decision"] == "ACCEPT"
    assert rev_data["status"] == "ACCEPT"
    assert rev_data["reviewed_by"] == "System Administrator"

def test_case_audit_trail_retrieval():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = client.get("/api/v1/responder/cases?search=0812", headers=headers)
    case_id = list_resp.json()["items"][0]["id"]

    audit_resp = client.get(f"/api/v1/responder/cases/{case_id}/audit", headers=headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert len(events) >= 1
    for ev in events:
        assert "event_type" in ev
        assert "actor_id" in ev
        assert "created_at" in ev
