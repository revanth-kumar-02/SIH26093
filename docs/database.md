# PostgreSQL Database Architecture & Persistence Layer

**Project:** SIH26093 — AI-Based Real-Time Stress and Trauma Assessment Module  
**Feature:** PostgreSQL Database + Persistent Application Memory  

---

## 1. Overview & Technology Stack

The persistence layer is designed to provide persistent memory for both victim/complainant intake journeys and administrative case management, replacing all transient in-memory state while maintaining backward compatibility with existing AI and evaluation pipelines.

- **RDBMS Target:** PostgreSQL 15+ (Local development & test compatibility via SQLite/PostgreSQL)
- **Driver:** `psycopg` / `psycopg3` (`postgresql+psycopg://`)
- **ORM:** SQLAlchemy 2.0+ with modern declarative mapping and typed schemas
- **Schema Versioning & Migrations:** Alembic
- **Connection Pooling:** SQLAlchemy `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`

---

## 2. Configuration & Environment Variables

Database credentials are read exclusively from environment variables with safe defaults and zero hardcoded credentials:

```bash
# PostgreSQL Connection URL
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/sih26093

# System Admin & People Initial Seed Credentials
ADMIN_EMAIL=admin@nhaa.gov.in
ADMIN_PASSWORD=<change-in-production>
PEOPLE_EMAIL=victim@nhaa.gov.in
PEOPLE_PASSWORD=<change-in-production>

# Persistent Application Memory Limits
MEMORY_MAX_CONTEXT_WORDS=350
MEMORY_MAX_PREVIOUS_SESSIONS=3
```

---

## 3. Logical Entities & Schema Architecture

The database implements **10 first-class logical entities** connected via foreign keys, cascading rules, and UTC timestamps:

```
USERS (PEOPLE, ADMIN)
  │
  ├── owned_cases ──> CASES
                         │
                         ├── sessions ──> SESSIONS (CONVERSATIONS)
                                            │
                                            ├── MESSAGES
                                            ├── AI_SIGNALS
                                            ├── ASSESSMENTS (Gemma 3n)
                                            ├── SVI_ASSESSMENTS (Deterministic SVI)
                                            └── RECOMMENDATIONS
                                                  │
                                                  └── reviews ──> RECOMMENDATION_REVIEWS

AUDIT_LOGS (Append-only audit trail)
```

### Entity Specifications

1. **`users` (`User` / `Responder`)**:
   - `id` (VARCHAR PK): e.g. `admin_system_001`, `victim_default_001`
   - `email` (VARCHAR UNIQUE, indexed)
   - `full_name` (VARCHAR)
   - `hashed_password` (VARCHAR, bcrypt encrypted, never exposed via API)
   - `role` (VARCHAR): Exactly two roles: `PEOPLE` and `ADMIN`
   - `is_active` (BOOLEAN)
   - `created_at`, `updated_at` (TIMESTAMP UTC)

2. **`cases` (`Case`)**:
   - `id` (VARCHAR PK): e.g. `CASE-2026-A1B2`
   - `external_case_reference` (VARCHAR UNIQUE, indexed)
   - `user_id` (VARCHAR FK -> `users.id`): Ownership for `PEOPLE` role
   - `assigned_admin_id` (VARCHAR FK -> `users.id`, optional): Case worker
   - `status` (VARCHAR): `active`, `pending_review`, `closed`
   - `created_at`, `updated_at`, `closed_at` (TIMESTAMP UTC)
   - `case_metadata` (JSONB): Structured non-PII triage tags

3. **`conversations` (`Conversation` / `Session`)**:
   - `id` (VARCHAR PK): e.g. `sess_abc123`
   - `case_id` (VARCHAR FK -> `cases.id`, indexed)
   - `session_name`, `language` (VARCHAR)
   - `status` (VARCHAR): `active`, `completed`, `interrupted`
   - `consent_status` (VARCHAR): Explicit consent tracking (`given`, `withheld`)
   - `started_at`, `ended_at`, `created_at`, `updated_at` (TIMESTAMP UTC)

4. **`messages` (`Message`)**:
   - `id` (VARCHAR PK): e.g. `msg_001`
   - `session_id` (VARCHAR FK -> `conversations.id`, indexed)
   - `sender_type` (VARCHAR): `PEOPLE` (user), `AI`, `SYSTEM`
   - `content` (TEXT): Anonymized transcript text (never raw audio)
   - `input_source` (VARCHAR): `text`, `voice`, `system`, `ai`
   - `language` (VARCHAR)
   - `message_metadata` (JSONB): Non-PII audio duration, confidence scores
   - `timestamp` (TIMESTAMP UTC)

5. **`ai_signals` (`AISignal`)**:
   - `id` (VARCHAR PK): e.g. `sig_001`
   - `session_id` (VARCHAR FK -> `conversations.id`, indexed)
   - `message_id` (VARCHAR FK -> `messages.id`, optional)
   - `signal_type` (VARCHAR): `text_emotion`, `speech_emotion`, `stress_detection`
   - `result` (JSONB): Model-specific structured output
   - `confidence` (FLOAT)
   - `model_name` (VARCHAR): e.g. `samlowe/roberta-base-go_emotions`
   - `model_version` (VARCHAR)
   - `created_at` (TIMESTAMP UTC)

6. **`assessments` (`Assessment`)**:
   - `id` (VARCHAR PK)
   - `session_id` (VARCHAR FK -> `conversations.id`, indexed)
   - `model_name` (VARCHAR): `google/gemma-3n-E2B-it`
   - `model_version` (VARCHAR)
   - `trauma_indicators`, `stress_markers`, `risk_factors` (JSONB)
   - `protective_factors`, `immediate_needs` (JSONB)
   - `uncertainty_score`, `model_confidence` (FLOAT)
   - `safety_flags` (JSONB)
   - `structured_output` (JSONB): Complete verified structured payload (zero hidden chain-of-thought)
   - `created_at` (TIMESTAMP UTC)

7. **`svi_assessments` (`SVIAssessment`)**:
   - `id` (VARCHAR PK)
   - `session_id` (VARCHAR FK -> `conversations.id`, indexed)
   - `total_svi_score` (FLOAT): Bounded 0.0 – 100.0
   - `risk_category` (VARCHAR): `LOW` (0-29.9), `MODERATE` (30-59.9), `HIGH` (60-84.9), `CRITICAL` (85-100)
   - `factor_contributions` (JSONB): 4 weighted factor breakdowns
   - `top_drivers` (JSONB)
   - `uncertainty_penalty` (FLOAT)
   - `safety_flags` (JSONB)
   - `urgent_human_review_required` (BOOLEAN)
   - `created_at` (TIMESTAMP UTC)

8. **`recommendations` (`Recommendation`)**:
   - `id` (VARCHAR PK)
   - `session_id` (VARCHAR FK -> `conversations.id`, indexed)
   - `category` (VARCHAR): `COUNSELLING_SUPPORT`, `LEGAL_AID`, `MEDICAL_ASSISTANCE`, `SAFETY_ASSISTANCE`, `POLICE_ASSISTANCE`, `EMERGENCY_SUPPORT`, `SOCIAL_SUPPORT`
   - `title`, `description` (TEXT)
   - `priority` (VARCHAR): `URGENT`, `HIGH`, `MEDIUM`, `LOW`
   - `rationale` (TEXT)
   - `status` (VARCHAR): `PENDING_REVIEW`, `ACCEPTED`, `MODIFIED`, `REJECTED`
   - `created_at`, `updated_at` (TIMESTAMP UTC)

9. **`recommendation_reviews` (`RecommendationReview`)**:
   - `id` (VARCHAR PK)
   - `recommendation_id` (VARCHAR FK -> `recommendations.id`, indexed)
   - `admin_id` (VARCHAR FK -> `users.id`, indexed)
   - `decision` (VARCHAR): `ACCEPTED`, `MODIFIED`, `REJECTED`
   - `modified_title`, `modified_description`, `modified_priority` (TEXT/VARCHAR)
   - `review_notes` (TEXT)
   - `reviewed_at` (TIMESTAMP UTC)

10. **`audit_logs` (`AuditLog`)**:
    - `id` (VARCHAR PK)
    - `actor_id` (VARCHAR, indexed)
    - `actor_role` (VARCHAR): `ADMIN` or `PEOPLE`
    - `action` (VARCHAR, indexed): e.g. `LOGIN`, `CASE_ACCESS`, `SVI_GENERATED`, `RECOMMENDATION_REVIEW`
    - `entity_type` (VARCHAR)
    - `entity_id` (VARCHAR, indexed)
    - `timestamp` (TIMESTAMP UTC, indexed)
    - `details` (JSONB): Anonymized audit metadata (never raw conversation content)

---

## 4. Alembic Migrations

Migrations are managed under `backend/alembic/`:

- `f1a2b3c4d5e6_persistent_memory_schema.py`: Initial schema creation for all 10 entities, foreign key constraints, JSONB column adaptation, and indexes.

### Migration Commands

```bash
# Apply migrations to latest
python -m alembic upgrade head

# Rollback one migration
python -m alembic downgrade -1

# Check current revision
python -m alembic current
```

---

## 5. Idempotency & Privacy Protection

1. **Idempotency**: Consecutive duplicate messages submitted by Flutter (e.g. on client-side retry or double tap) within 2 seconds are detected and deduplicated via `session_service.persist_message`.
2. **Audio Minimization**: Raw audio recordings are never persisted to disk or the database. Audio is streamed in memory for IndicConformer ASR transcription and Wav2Vec2 SER emotion extraction, then immediately discarded.
3. **Structured Non-PII**: Assessments store only clinical indicators, risk tier scores, and structured categories. Chain-of-thought reasoning is completely excluded.
