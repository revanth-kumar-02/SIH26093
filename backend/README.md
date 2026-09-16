# SIH26093 — Backend (FastAPI)

AI-Based Real-Time Stress and Trauma Assessment Module for Victims/Complainants Accessing NHAA (14566) and Integrated Portal.

## Setup & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python -m pytest tests -v
```

### 3. Run FastAPI Development Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

- `GET /health` — Health check endpoint (`{"status": "ok"}`)
- `POST /api/v1/sessions` — Create a new victim interaction session
- `POST /api/v1/sessions/{session_id}/messages` — Send message and receive empathetic triage response
- `POST /api/v1/sessions/{session_id}/assessment` — Request assessment placeholder contract
- `GET /docs` — Swagger / OpenAPI documentation
- `GET /redoc` — ReDoc documentation

## Network Connectivity
- **Web**: `http://localhost:8000` or `http://127.0.0.1:8000`
- **Android Emulator**: `http://10.0.2.2:8000`
- **Physical Android Device**: `http://<LAN_IP>:8000` (e.g. `http://172.16.104.30:8000`)
