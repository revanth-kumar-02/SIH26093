# SIH26093 — Threat Model & Security Mitigations

| Threat ID | Threat Description | Attack Vector | Technical Mitigation |
|:---|:---|:---|:---|
| **T-01** | Unauthorized Case Access | Modifying `/cases/{case_id}` (IDOR) | Server-side object-level authorization enforcing responder assignment and role hierarchy. |
| **T-02** | Credential Theft / Impersonation | Replay attacks / brute force | Strong bcrypt password hashing (12 rounds) + short-lived signed JWTs. |
| **T-03** | Sensitive Data Leakage | Transcript / PII exposure in logs | Structured logging restricted to UUIDs (`session_id`, `case_id`). Audio/PII excluded from telemetry. |
| **T-04** | AI Hallucination & Fabrication | LLM inventing false trauma evidence | Rigid Pydantic schemas, evidence quotation requirements, and human responder oversight. |
| **T-05** | Erroneous Risk Escalation | Emotion/stress model misclassifying dialect | Strict mathematical SVI v1.0 separation; single emotion cannot inflate risk. |
| **T-06** | Double-Counting Evidence Inflation | Same complaint repeated across modalities | Cross-modal deduplication and mathematical corroboration capping in SVI. |
| **T-07** | Autonomous Harmful Action | Untrained model triggering police raid | Zero autonomous external dispatch APIs; all recommendations require human sign-off. |
