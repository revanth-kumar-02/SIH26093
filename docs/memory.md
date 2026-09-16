# Persistent Application Memory Architecture

**Project:** SIH26093 — AI-Based Real-Time Stress and Trauma Assessment Module  
**Service:** `backend/app/services/memory_service.py`  

---

## 1. Overview & Problem Definition

In psychological trauma assessment and crisis intake (e.g. NHAA 14566), victims often return across multiple sessions or days. Without persistent memory, the assessment system suffers from:
- Repeated questioning that re-traumatizes the victim.
- Inability to detect longitudinal escalation in trauma or risk factors.
- Loss of context from prior human responder reviews and recommendations.

However, naive memory implementations that dump the entire conversation database into the LLM prompt cause:
1. Context window explosion and high latency.
2. Hallucination and loss of focus on immediate distress.
3. Severe privacy leaks across sessions or users.

SIH26093 implements a **Dedicated Bounded Memory Service** backed by PostgreSQL.

---

## 2. Architecture & Data Flow

```
                      PostgreSQL Database
                               │
               (Indexed historical queries by case_id)
                               │
                               ▼
                    ┌─────────────────────┐
                    │    MemoryService    │
                    │  (Bounded Context)  │
                    └─────────────────────┘
                               │
     ┌─────────────────────────┼─────────────────────────┐
     ▼                         ▼                         ▼
Prior Session Summaries   Prior Human Reviews   Active Trauma Indicators
(Last 3 Sessions Max)   (Accepted / Modified)    (De-duplicated Set)
     │                         │                         │
     └─────────────────────────┼─────────────────────────┘
                               ▼
                    Token & Word Budget Guard
                    (Strict Max 350 Words)
                               │
                               ▼
               Formatted Historical Memory Block
                               │
                               ▼
                   Gemma 3n E2B IT Prompt
                 (Trauma Assessment Engine)
```

---

## 3. Controlled Context Retrieval Protocol

When `MemoryService.retrieve_bounded_context(session_id, db)` is called:

1. **Identify Parent Case**: Finds the `case_id` associated with the active session.
2. **Fetch Chronological History**: Gathers all prior completed sessions for that specific case (excluding the active one), ordered chronologically.
3. **Session Windowing**: Limits analysis to the last `MEMORY_MAX_PREVIOUS_SESSIONS` (default: 3).
4. **Extract Structured Signals**:
   - Prior SVI Risk Tiers (e.g., `HIGH (68.4)`, `MODERATE (45.2)`).
   - Confirmed Trauma Indicators from prior Gemma assessments.
   - Human Responder Review Decisions (e.g. "Counselling Support ACCEPTED by Admin").
5. **Bounded Word Formatting**: Formats concise bullet points and enforces `MEMORY_MAX_CONTEXT_WORDS` (default: 350 words). If the historical summary exceeds the limit, older entries are gracefully summarized.

### Example Grounded Memory Injected into Gemma:

```
[HISTORICAL MEMORY (Prior Sessions)]:
- Prior Session 1 (2026-09-14): SVI Risk: MODERATE (Score: 48.2). Indicators: intimidation, panic symptoms. Prior Human Action: Counselling support accepted.
- Prior Session 2 (2026-09-15): SVI Risk: HIGH (Score: 71.0). Indicators: physical threat, lack of safe shelter. Prior Human Action: Emergency shelter recommended.
Note: Evaluate current inputs against this longitudinal trajectory without re-asking established facts.
```

---

## 4. Privacy & Role-Based Access Control (RBAC)

The memory service enforces strict object-level security:

- **PEOPLE Role**:
  - Bound to their own `user_id`.
  - Can only retrieve memory and session history for cases they own (`case.user_id == current_user.id`).
  - Cannot query other users' cases or historical records.
- **ADMIN Role**:
  - Full administrative access to inspect longitudinal case memory, timeline, SVI trajectory, and human reviews for authorized triage.

---

## 5. Verification & Test Coverage

Verified via `backend/tests/test_persistence_memory.py`:
- `test_memory_service_bounded_retrieval`: Asserts that memory respects the 350-word cap, incorporates prior session indicators, prior SVI tiers, and human review decisions.
- `test_cases_rbac_people_cannot_access_other_cases`: Validates strict 403/404 isolation across distinct user accounts.
