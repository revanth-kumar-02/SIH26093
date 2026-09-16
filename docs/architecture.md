# SIH26093 — System Architecture

## 1. High-Level System Topology

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 CLIENT APPLICATIONS                    │
                  │  ┌───────────────────────┐  ┌───────────────────────┐  │
                  │  │ Flutter Victim Intake │  │ Flutter Responder Web │  │
                  │  │  (Android App & Web)  │  │   (Triage Console)    │  │
                  │  └───────────┬───────────┘  └───────────┬───────────┘  │
                  └──────────────┼──────────────────────────┼──────────────┘
                                 │ HTTP / JSON / Multipart  │ Bearer JWT Auth
                                 ▼                          ▼
                  ┌────────────────────────────────────────────────────────┐
                  │             FASTAPI ASYNC BACKEND SERVICES             │
                  │                                                        │
                  │  ┌──────────────────────────────────────────────────┐  │
                  │  │ API Gateway / Security / Auth / Object Auth      │  │
                  │  └───────────────────────┬──────────────────────────┘  │
                  │                          │                             │
                  │  ┌───────────────────────▼──────────────────────────┐  │
                  │  │ Orchestration & Session State Machine            │  │
                  │  └───────┬───────────────────────┬──────────────────┘  │
                  │          │                       │                     │
                  │          ▼                       ▼                     │
                  │  ┌───────────────┐       ┌───────────────┐             │
                  │  │ Multimodal AI │       │ Deterministic │             │
                  │  │ Signal Engine │       │ SVI Engine    │             │
                  │  └───────┬───────┘       └───────┬───────┘             │
                  │          │                       │                     │
                  │          └───────────┬───────────┘                     │
                  │                      ▼                                 │
                  │  ┌───────────────────────────────────────┐             │
                  │  │ Support Recommendation Engine         │             │
                  │  │ (Advisory Pathways for Human Review)  │             │
                  │  └───────────────────┬───────────────────┘             │
                  └──────────────────────┼─────────────────────────────────┘
                                         │ Async SQLAlchemy ORM
                                         ▼
                  ┌────────────────────────────────────────────────────────┐
                  │                 POSTGRESQL DATA STORE                  │
                  │  - Users & Roles: Exactly Two Roles (ADMIN, PEOPLE)   │
                  │  - Cases & Strict Lifecycle Status Machine             │
                  │  - Conversations & Multi-Source Turn Messages          │
                  │  - Assessments & Structured Indicators                 │
                  │  - Deterministic SVI Scores & Factor Provenance        │
                  │  - Support Recommendations & Human Review Decisions    │
                  │  - Immutable, Append-Only Audit Trail (Prov-O Style)   │
                  └────────────────────────────────────────────────────────┘
```

## 2. Core Architectural Separation

The system enforces a strict boundary between:
1. **Generative / Interpretive AI (Gemma 3n E2B IT):** Identifies qualitative indicators from transcripts, speech prosody, and emotion signals. It does **NOT** calculate risk scores or recommend punitive/emergency actions.
2. **Deterministic Risk Triage (SVI Engine v1.0):** Pure algorithmic mathematical calculation based on normalized weights and evidence confidence. Fully reproducible and transparent.
3. **Advisory Pathway Generation (Recommendation Engine):** Proposes support pathways (Legal, Medical, Shelter, Psychological, Social). Never executes autonomous external actions.
4. **Human Authority & Audit:** A certified human helpline responder must review, accept, modify, or reject every recommendation. All decisions are captured in an append-only audit trail.
