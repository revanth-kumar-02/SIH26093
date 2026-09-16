# SIH26093 — REST API Reference

Base URL: `/api/v1`

## 1. Victim Intake & Session Management
- `POST /sessions` — Create anonymous or pseudonymous intake session. Returns `session_id`.
- `GET /sessions/{session_id}` — Get active session state.
- `POST /sessions/{session_id}/messages` — Submit victim text message and receive calm, supportive conversational response.
- `POST /sessions/{session_id}/transcribe` — Submit 16kHz mono audio WAV and receive IndicConformer multilingual transcript.
- `POST /sessions/{session_id}/analyze/text` — Execute GoEmotions 28-class text emotion analysis.
- `POST /sessions/{session_id}/analyze/audio` — Execute Wav2Vec2 7-class speech emotion analysis.
- `POST /sessions/{session_id}/analyze/stress` — Execute MentalBERT Dreaddit stress classifier.
- `POST /sessions/{session_id}/analyze/multimodal` — Execute Gemma-3n multimodal evidence assessment.
- `POST /sessions/{session_id}/svi` — Compute deterministic Stress Vulnerability Index.
- `POST /sessions/{session_id}/recommendations` — Generate advisory support pathways for human review.

## 2. Authentication & Authorization
- `POST /auth/login` — Responder authentication with username/email and password. Returns JWT access and refresh tokens.
- `GET /auth/me` — Retrieve active responder profile and role.
- `POST /auth/refresh` — Issue fresh access token using valid refresh token.

## 3. Responder Portal Operations
- `GET /responder/cases` — List triage queue with filters (`case_status`, `risk_category`, `assigned_to_me`, `search`).
- `GET /responder/cases/{case_id}` — Retrieve full structured case details, conversation history, SVI breakdown, safety flags, and recommendations. (Object-level authorization enforced).
- `POST /responder/cases/{case_id}/assign` — Assign case to responder (Supervisor/Admin only).
- `POST /responder/cases/{case_id}/status` — Progress case status through valid lifecycle transitions.
- `POST /responder/cases/{case_id}/recommendations/{rec_id}/review` — Record responder decision (`ACCEPT`, `MODIFY`, `REJECT`) with notes. (Idempotent).
- `GET /responder/cases/{case_id}/audit` — Retrieve immutable append-only audit trail for case provenance.

## 4. Demo & Presentation Mode
- `GET /demo/cases` — List manifest of 5 synthetic SIH demonstration cases (Cases A-E).
- `POST /demo/reset` — Reset database and reseed with clean synthetic demo data.
