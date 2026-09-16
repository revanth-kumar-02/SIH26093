import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def benchmark():
    print("Running Phase 9 Operational Benchmarks...")
    
    # 1. Login Latency (includes bcrypt verification, token signing, DB update, audit insert)
    t0 = time.perf_counter()
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "responder_user",
        "password": "ResponderPassword@123"
    })
    t_login = (time.perf_counter() - t0) * 1000.0
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Case List Latency (includes auth token decode, DB query with joins, pagination, SVI extraction)
    t0 = time.perf_counter()
    list_resp = client.get("/api/v1/responder/cases?page=1&page_size=20", headers=headers)
    t_case_list = (time.perf_counter() - t0) * 1000.0
    case_items = list_resp.json()["items"]
    case_id = case_items[0]["id"]

    # 3. Case Detail Latency (includes fetching case, conversations, messages, assessments, SVI, recs, audit log + audit write)
    t0 = time.perf_counter()
    detail_resp = client.get(f"/api/v1/responder/cases/{case_id}", headers=headers)
    t_case_detail = (time.perf_counter() - t0) * 1000.0

    # 4. Recommendation Review Latency (decision update + audit event append)
    rec_id = detail_resp.json()["recommendations"][0]["id"]
    t0 = time.perf_counter()
    review_resp = client.post(
        f"/api/v1/responder/cases/{case_id}/recommendations/{rec_id}/review",
        json={"decision": "ACCEPT", "responder_note": "Benchmark review verification"},
        headers=headers
    )
    t_review = (time.perf_counter() - t0) * 1000.0

    print(f"Login Latency: {t_login:.2f} ms")
    print(f"Case List Latency: {t_case_list:.2f} ms")
    print(f"Case Detail Latency: {t_case_detail:.2f} ms")
    print(f"Recommendation Review Latency: {t_review:.2f} ms")

if __name__ == "__main__":
    benchmark()
