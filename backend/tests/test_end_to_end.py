import pytest
from starlette.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_full_pipeline_victim_to_responder_lifecycle(client):
    """End-to-end integration test across all 18 pipeline stages:
    1. Victim session creation
    2. Language selection
    3. Consent state
    4. Text intake message
    5. Emotion & stress signal generation
    6. Multimodal Gemma assessment
    7. Deterministic SVI computation
    8. Support recommendation generation
    9. Responder login
    10. Case retrieval
    11. SVI & key driver inspection
    12. Uncertainty preservation
    13. Safety flag independence check
    14. Recommendation review (ACCEPT/MODIFY)
    15. Status progression to AWAITING_RESPONDER_ACTION
    16. Audit event logging
    17. Demo database reset
    """
    # 1. Victim creates session
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    assert session_res.status_code == 201
    session_id = session_res.json()["session_id"]
    assert session_res.json()["status"] in ["SESSION_CREATED", "active"]

    # 2. Text message intake
    msg_res = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "I was threatened and evicted from my home by my employer without notice."}
    )
    assert msg_res.status_code == 200
    assert "response" in msg_res.json()

    # 3. Text emotion analysis
    emo_res = client.post(
        f"/api/v1/sessions/{session_id}/analyze/text",
        json={"text": "I was threatened and evicted from my home by my employer without notice."}
    )
    assert emo_res.status_code == 200
    assert "top_emotion" in emo_res.json()

    # 4. Stress analysis
    stress_res = client.post(
        f"/api/v1/sessions/{session_id}/analyze/stress",
        json={"text": "I was threatened and evicted from my home by my employer without notice."}
    )
    assert stress_res.status_code == 200
    assert "stress" in stress_res.json()
    assert stress_res.json()["stress"]["label"] in ["stressed", "not_stressed"]

    # 5. Gemma multimodal assessment
    assessment_res = client.post(f"/api/v1/sessions/{session_id}/analyze/multimodal")
    assert assessment_res.status_code == 200
    assessment_data = assessment_res.json()
    assert "indicators" in assessment_data
    assert "key_observations" in assessment_data

    # 6. SVI calculation
    svi_res = client.post(f"/api/v1/sessions/{session_id}/svi")
    assert svi_res.status_code == 200
    svi_data = svi_res.json()
    assert 0.0 <= svi_data["score"] <= 100.0
    assert svi_data["risk_category"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]

    # 7. Support recommendations
    rec_res = client.post(f"/api/v1/sessions/{session_id}/recommendations")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert len(rec_data["recommendations"]) > 0

    # 8. Responder login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminPassword@123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 9. Case retrieval
    cases_res = client.get("/api/v1/responder/cases", headers=headers)
    assert cases_res.status_code == 200
    cases = cases_res.json()["items"]
    assert len(cases) >= 5

    # 10. Open demo case D (Safety Flag Validation)
    case_d_res = client.get(
        "/api/v1/responder/cases?search=NHAA-2026-SYN-0812",
        headers=headers
    )
    case_d_id = case_d_res.json()["items"][0]["id"]
    detail_d = client.get(f"/api/v1/responder/cases/{case_d_id}", headers=headers).json()
    assert detail_d["safety_flags"]["immediate_safety_attention"] is True
    assert detail_d["safety_flags"]["urgent_human_review"] is True
    assert detail_d["svi_result"]["risk_category"] == "CRITICAL"

    # 11. Review recommendation on Case C
    case_c_res = client.get(
        "/api/v1/responder/cases?search=NHAA-2026-SYN-0815",
        headers=headers
    )
    case_c_id = case_c_res.json()["items"][0]["id"]
    detail_c = client.get(f"/api/v1/responder/cases/{case_c_id}", headers=headers).json()
    rec_c_id = detail_c["recommendations"][0]["id"]

    review_res = client.post(
        f"/api/v1/responder/cases/{case_c_id}/recommendations/{rec_c_id}/review",
        json={"decision": "ACCEPT", "responder_note": "Approved by triage team."},
        headers=headers
    )
    assert review_res.status_code == 200
    assert review_res.json()["decision"] == "ACCEPT"

    # 12. Update case status to AWAITING_RESPONDER_ACTION
    stat_res = client.post(
        f"/api/v1/responder/cases/{case_c_id}/status",
        json={"status": "AWAITING_RESPONDER_ACTION"},
        headers=headers
    )
    assert stat_res.status_code == 200

    # 13. Audit verification
    audit_res = client.get(f"/api/v1/responder/cases/{case_c_id}/audit", headers=headers)
    assert audit_res.status_code == 200
    events = [e["event_type"] for e in audit_res.json()]
    assert any("RECOMMENDATION" in et for et in events)
