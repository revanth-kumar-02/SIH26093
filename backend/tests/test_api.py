def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_session(client):
    response = client.post("/api/v1/sessions", json={"language": "en"})
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["language"] == "en"
    assert data["status"] in ["active", "SESSION_CREATED"]

def test_send_message_success(client):
    # First create session
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    # Send message
    msg_res = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "I want to tell you what happened."}
    )
    assert msg_res.status_code == 200
    data = msg_res.json()
    assert "message_id" in data
    assert "response" in data
    assert len(data["response"]) > 0
    assert data["status"] == "received"

def test_send_message_invalid_session(client):
    msg_res = client.post(
        "/api/v1/sessions/non-existent-session-id/messages",
        json={"message": "Hello"}
    )
    assert msg_res.status_code == 404

def test_assessment_placeholder(client):
    session_res = client.post("/api/v1/sessions", json={"language": "hi"})
    session_id = session_res.json()["session_id"]

    res = client.post(f"/api/v1/sessions/{session_id}/assessment")
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == session_id
    assert data["status"] == "pending_review"
    assert data["assessment"]["risk_level"] == "not_available"
    assert data["assessment"]["svi"] is None
    assert data["assessment"]["indicators"] == []

def test_assessment_invalid_session(client):
    res = client.post("/api/v1/sessions/invalid-id/assessment")
    assert res.status_code == 404
