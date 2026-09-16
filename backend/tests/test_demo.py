import pytest
from starlette.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_get_demo_cases_manifest(client):
    response = client.get("/api/v1/demo/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == 5
    tags = [c["case_id_tag"] for c in cases]
    assert "Case A" in tags
    assert "Case B" in tags
    assert "Case C" in tags
    assert "Case D" in tags
    assert "Case E" in tags
    for c in cases:
        assert c["disclaimer"] == "DEMO / SYNTHETIC DATA"

def test_demo_database_reset(client):
    response = client.post("/api/v1/demo/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["cases_count"] == 5
    assert "DEMO / SYNTHETIC DATA" in data["notice"]
