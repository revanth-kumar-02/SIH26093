def create_user_auth_headers(user_id: str, role: UserRole) -> dict:
    token = create_access_token(
        subject=user_id,
        role=role.value,
        extra_claims={"username": f"u_{user_id}", "display_name": f"User {user_id}"}
    )
    return {"Authorization": f"Bearer {token}"}

import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.models.responder import Responder, UserRole
from app.db.models.case import Case, CaseStatus
from app.db.models.conversation import Conversation
from app.db.models.message import Message, MessageSenderType, MessageInputSource
from app.db.models.ai_signal import AISignal
from app.db.models.assessment import AssessmentModel
from app.db.models.svi import SVIResultModel
from app.db.models.recommendation import RecommendationModel
from app.db.models.recommendation_review import RecommendationReview
from app.db.models.audit import AuditEvent
from app.core.auth import hash_password, create_access_token
from app.services.memory_service import memory_service

client = TestClient(app)

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

def get_admin_headers() -> dict:
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin_user",
        "password": "AdminPassword@123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def get_people_headers() -> dict:
    resp = client.post("/api/v1/auth/login", json={
        "username": "people_user",
        "password": "PeoplePassword@123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ---------------------------------------------------------------------------
# 1. DATABASE CONNECTION & LOGICAL ENTITY PERSISTENCE
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_database_all_ten_entities_persistable():
    """Verify all 10 required logical entities can be created, persisted, and queried."""
    async with AsyncSessionLocal() as session:
        uid = f"user-{uuid.uuid4().hex[:8]}"
        cid = f"case-{uuid.uuid4().hex[:8]}"
        sid = f"sess-{uuid.uuid4().hex[:8]}"
        
        # 1. User
        user = Responder(
            username=uid,
            email=f"{uid}@example.com",
            password_hash=hash_password("SecurePassword@123"),
            display_name="Persistence Test User",
            role=UserRole.PEOPLE
        )
        session.add(user)
        await session.flush()

        # 2. Case
        case = Case(
            external_case_reference=f"NHAA-TEST-{uuid.uuid4().hex[:8].upper()}",
            status=CaseStatus.NEW,
            language="en",
            user_id=user.id
        )
        session.add(case)
        await session.flush()

        # 3. Session / Conversation
        conv = Conversation(
            case_id=case.id,
            session_id=sid,
            input_language="en",
            status="ACTIVE"
        )
        session.add(conv)
        await session.flush()

        # 4. Message
        msg = Message(
            conversation_id=conv.id,
            session_id=sid,
            sender_type=MessageSenderType.VICTIM,
            input_source=MessageInputSource.TEXT,
            content="I need immediate support and guidance.",
            language="en"
        )
        session.add(msg)
        await session.flush()

        # 5. AI Signal
        sig = AISignal(
            session_id=sid,
            message_id=msg.id,
            signal_type="TEXT_EMOTION",
            result={"top_emotion": "fear", "score": 0.85},
            confidence=0.85,
            model_name="SamLowe/roberta-base-go_emotions",
            model_version="1.0"
        )
        session.add(sig)
        await session.flush()

        # 6. Assessment
        assess = AssessmentModel(
            case_id=case.id,
            session_id=sid,
            assessment_version="google/gemma-3n-E2B-it",
            assessment_payload={
                "indicators": [{"indicator": "fear", "category": "emotional_distress", "status": "detected"}],
                "safety_concerns": ["Potential stalking behavior"]
            }
        )
        session.add(assess)
        await session.flush()

        # 7. SVI Assessment
        svi_record = SVIResultModel(
            case_id=case.id,
            session_id=sid,
            svi_version="v1.0",
            score=64.2,
            risk_category="HIGH",
            factor_contributions=[{"factor_id": "intimidation", "contribution": 35.0}],
            key_drivers=["Intimidation indicators observed"],
            uncertainties=["Missing speech audio"],
            immediate_safety_attention=False,
            urgent_human_review=True
        )
        session.add(svi_record)
        await session.flush()

        # 8. Recommendation
        rec = RecommendationModel(
            case_id=case.id,
            session_id=sid,
            category="COUNSELLING_SUPPORT",
            priority="high",
            reason="Victim exhibits acute fear and intimidation markers",
            supporting_indicators=["fear"],
            evidence_sources=["text"],
            responder_action="Provide trauma-informed crisis counselling",
            requires_human_review=True,
            status="PENDING"
        )
        session.add(rec)
        await session.flush()

        # 9. Recommendation Review
        rec_review = RecommendationReview(
            recommendation_id=rec.id,
            admin_id=None,
            decision="ACCEPTED",
            review_notes="Approved for psychological counselling triage",
            reviewed_at=datetime.now(timezone.utc)
        )
        session.add(rec_review)
        await session.flush()

        # 10. Audit Log
        audit = AuditEvent(
            case_id=case.id,
            actor_id=user.id,
            actor_type="PEOPLE",
            event_type="TEST_PERSISTENCE_EVENT",
            entity_type="CASE",
            entity_id=case.id,
            event_metadata={"test": True}
        )
        session.add(audit)
        await session.commit()

        # Verify all records queryable via ORM relationships
        queried_case = (await session.execute(
            select(Case)
            .options(
                selectinload(Case.conversations).selectinload(Conversation.messages),
                selectinload(Case.conversations).selectinload(Conversation.ai_signals),
                selectinload(Case.assessments),
                selectinload(Case.svi_results),
                selectinload(Case.recommendations).selectinload(RecommendationModel.reviews),
                selectinload(Case.audit_events)
            )
            .where(Case.id == case.id)
        )).scalars().first()

        assert queried_case is not None
        assert queried_case.user_id == user.id
        assert len(queried_case.conversations) == 1
        assert len(queried_case.conversations[0].messages) == 1
        assert len(queried_case.conversations[0].ai_signals) == 1
        assert len(queried_case.assessments) == 1
        assert len(queried_case.svi_results) == 1
        assert len(queried_case.recommendations) == 1
        assert len(queried_case.recommendations[0].reviews) == 1
        assert len(queried_case.audit_events) == 1

# ---------------------------------------------------------------------------
# 2. SESSION CONTINUITY & CONVERSATION HISTORY RETRIEVAL
# ---------------------------------------------------------------------------
def test_session_message_persistence_and_retrieval_api():
    """Verify messages sent via API are persisted and retrievable across re-queries."""
    sess_res = client.post("/api/v1/sessions", json={"language": "en"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]

    # Send 2 messages
    msg1 = client.post(f"/api/v1/sessions/{session_id}/messages", json={"message": "First message from victim"})
    assert msg1.status_code == 200
    msg2 = client.post(f"/api/v1/sessions/{session_id}/messages", json={"message": "Second message regarding safety"})
    assert msg2.status_code == 200

    # Retrieve persisted conversation messages from DB
    history_res = client.get(f"/api/v1/sessions/{session_id}/messages")
    assert history_res.status_code == 200
    msgs = history_res.json()
    assert len(msgs) >= 3  # 2 user messages + 2 system responses

    contents = [m["content"] for m in msgs]
    assert "First message from victim" in contents
    assert "Second message regarding safety" in contents

# ---------------------------------------------------------------------------
# 3. AI SIGNALS PERSISTENCE & RETRIEVAL API
# ---------------------------------------------------------------------------
def test_session_ai_signals_persisted():
    """Verify AI signals from messages are persisted in ai_signals table."""
    sess_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = sess_res.json()["session_id"]

    client.post(f"/api/v1/sessions/{session_id}/messages", json={"message": "I feel very stressed and fearful"})

    signals_res = client.get(f"/api/v1/sessions/{session_id}/signals")
    assert signals_res.status_code == 200
    signals = signals_res.json()
    assert len(signals) >= 1
    signal_types = [s["signal_type"] for s in signals]
    assert "TEXT_EMOTION" in signal_types or "STRESS" in signal_types

# ---------------------------------------------------------------------------
# 4. APPLICATION MEMORY CONTEXT RETRIEVAL
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_memory_service_bounded_retrieval():
    """Verify MemoryService compiles prior session context and enforces word boundaries."""
    async with AsyncSessionLocal() as session:
        # Create a Case with 2 prior sessions
        user = Responder(
            username=f"mem_usr_{uuid.uuid4().hex[:6]}",
            email=f"mem_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            display_name="Memory Test Complainant",
            role=UserRole.PEOPLE
        )
        session.add(user)
        await session.flush()

        case = Case(
            external_case_reference=f"NHAA-MEM-{uuid.uuid4().hex[:6].upper()}",
            status=CaseStatus.IN_REVIEW,
            user_id=user.id
        )
        session.add(case)
        await session.flush()

        # Prior session 1
        s1 = Conversation(
            case_id=case.id,
            session_id=f"prior-s1-{uuid.uuid4().hex[:6]}",
            status="CLOSED",
            started_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        session.add(s1)
        await session.flush()

        svi1 = SVIResultModel(
            case_id=case.id,
            session_id=s1.session_id,
            svi_version="v1.0",
            score=72.0,
            risk_category="HIGH",
            factor_contributions=[{"factor": "fear", "score": 72.0}],
            key_drivers=["Persistent harassment", "Fear of retaliation"],
            uncertainties=[],
            urgent_human_review=True
        )
        session.add(svi1)

        rec1 = RecommendationModel(
            case_id=case.id,
            session_id=s1.session_id,
            category="COUNSELLING_SUPPORT",
            priority="high",
            reason="Victim reported distress",
            responder_action="Provide emergency counselling",
            status="ACCEPTED",
            responder_decision="ACCEPTED",
            responder_note="Approved by triage team"
        )
        session.add(rec1)

        # Current session 2
        s2 = Conversation(
            case_id=case.id,
            session_id=f"curr-s2-{uuid.uuid4().hex[:6]}",
            status="ACTIVE",
            started_at=datetime.now(timezone.utc)
        )
        session.add(s2)
        await session.commit()

        # Retrieve bounded context for current session 2
        context = await memory_service.retrieve_bounded_context(session, s2.session_id, max_words=350)
        assert context != ""
        assert "HISTORICAL CASE MEMORY" in context
        assert "HIGH" in context
        assert "Persistent harassment" in context
        assert "COUNSELLING_SUPPORT: ACCEPTED" in context

        # Verify word boundary constraint
        words = context.split()
        assert len(words) <= 350

# ---------------------------------------------------------------------------
# 5. STRICT RBAC & OBJECT-LEVEL AUTHORIZATION TESTS
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_cases_rbac_people_cannot_access_other_cases():
    """Verify that a user with role PEOPLE cannot access another complainant's case."""
    async with AsyncSessionLocal() as session:
        # Create victim A and victim B
        user_a = Responder(
            username=f"victim_a_{uuid.uuid4().hex[:6]}",
            email=f"victim_a_{uuid.uuid4().hex[:6]}@test.com",
            password_hash=hash_password("Pass123!"),
            display_name="Victim A",
            role=UserRole.PEOPLE
        )
        user_b = Responder(
            username=f"victim_b_{uuid.uuid4().hex[:6]}",
            email=f"victim_b_{uuid.uuid4().hex[:6]}@test.com",
            password_hash=hash_password("Pass123!"),
            display_name="Victim B",
            role=UserRole.PEOPLE
        )
        session.add_all([user_a, user_b])
        await session.flush()

        case_b = Case(
            external_case_reference=f"NHAA-B-{uuid.uuid4().hex[:6].upper()}",
            status=CaseStatus.NEW,
            user_id=user_b.id
        )
        session.add(case_b)
        await session.commit()

        headers_a = create_user_auth_headers(user_id=user_a.id, role=UserRole.PEOPLE)

        # Victim A attempts to access Victim B's case detail
        res = client.get(f"/api/v1/cases/{case_b.id}", headers=headers_a)
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "FORBIDDEN"

        # Victim A attempts to access Victim B's sessions
        res_sess = client.get(f"/api/v1/cases/{case_b.id}/sessions", headers=headers_a)
        assert res_sess.status_code == 403

def test_people_cannot_access_admin_portal():
    """Verify that a user with role PEOPLE receives HTTP 403 for administrative routes."""
    headers_people = get_people_headers()

    res1 = client.get("/api/v1/admin/dashboard", headers=headers_people)
    assert res1.status_code == 403

    res2 = client.get("/api/v1/admin/audit", headers=headers_people)
    assert res2.status_code == 403

    res3 = client.get("/api/v1/responder/cases", headers=headers_people)
    assert res3.status_code == 403

def test_admin_can_access_cases_and_dashboard():
    """Verify that an ADMIN user has full access to triage cases, dashboard, and details."""
    headers_admin = get_admin_headers()

    dash_res = client.get("/api/v1/admin/dashboard", headers=headers_admin)
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert "active_cases" in data
    assert "risk_distribution" in data

    cases_res = client.get("/api/v1/cases", headers=headers_admin)
    assert cases_res.status_code == 200
    assert isinstance(cases_res.json(), list)
