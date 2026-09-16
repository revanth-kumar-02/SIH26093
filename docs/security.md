# SIH26093 — Security & Hardening Architecture

## 1. Authentication
- **Password Hashing:** Passwords hashed using bcrypt (`passlib.context.CryptContext` with `schemes=["bcrypt"]`, 12 rounds). Plaintext passwords are never logged, stored, or transmitted.
- **JWT Lifespan:** Access tokens expire after 60 minutes. Refresh tokens valid for 7 days.
- **Algorithms:** HMAC-SHA256 (`HS256`) signed with strong internal secret keys.

## 2. Server-Side Object-Level Authorization (IDOR Defense)
- Endpoint access is validated server-side based on responder role and case assignment:
  - **ADMIN Role:** Full administrative access to triage queue, case assignment, SVI breakdown, recommendation review (accept/modify/reject), and audit trail.
  - **PEOPLE Role:** Restricted exclusively to permitted victim/complainant-facing session functionality. Attempting to access administrative or responder endpoints returns HTTP 403 `INSUFFICIENT_PERMISSIONS`. No access to other people's cases or administrative audit data.
- No direct database access from Flutter frontend.

## 3. Idempotency & Concurrency Protection
- Repeated calls to `POST /cases/{case_id}/recommendations/{rec_id}/review` with identical decision and notes return the existing record without appending redundant audit entries.
- Repeated calls to `POST /cases/{case_id}/status` with identical status return cleanly without duplicating state machine audits.

## 4. Input Validation & Error Sanitization
- All request parameters validated using strict Pydantic schemas.
- Free-text search on case list is restricted strictly to safe case reference codes (`ilike %...%`), eliminating SQL injection and preventing search against sensitive victim narrative content.
- Custom exception handling strips internal stack traces, database schemas, and filesystem paths before responding to clients.
