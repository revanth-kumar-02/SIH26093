import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.db.base import Base
from app.db.models.responder import Responder, UserRole
from app.db.models.case import Case, CaseStatus
from app.db.models.conversation import Conversation
from app.db.models.message import Message, MessageSenderType, MessageInputSource
from app.db.models.assessment import AssessmentModel
from app.db.models.svi import SVIResultModel
from app.db.models.recommendation import RecommendationModel
from app.db.models.audit import AuditEvent

def test_database_two_role_constraint():
    """Verify that UserRole strictly contains ONLY PEOPLE and ADMIN, with no legacy roles."""
    members = list(UserRole.__members__.keys())
    assert sorted(members) == ["ADMIN", "PEOPLE"]
    assert len(members) == 2
    assert "RESPONDER" not in members
    assert "SUPERVISOR" not in members

    with pytest.raises(AttributeError):
        _ = getattr(UserRole, "RESPONDER")

    with pytest.raises(AttributeError):
        _ = getattr(UserRole, "SUPERVISOR")

def test_database_user_lifecycle():
    async def run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            admin = Responder(
                username="test_admin",
                email="test_admin@nhaa.gov.in",
                display_name="Test Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            people = Responder(
                username="test_people",
                email="test_people@nhaa.gov.in",
                display_name="Test Citizen",
                role=UserRole.PEOPLE,
                is_active=True
            )
            session.add_all([admin, people])
            await session.commit()
            await session.refresh(admin)
            await session.refresh(people)

            assert admin.id is not None
            assert admin.username == "test_admin"
            assert admin.role == UserRole.ADMIN

            assert people.id is not None
            assert people.username == "test_people"
            assert people.role == UserRole.PEOPLE

        await engine.dispose()

    asyncio.run(run())

def test_database_case_and_relationships():
    async def run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            admin = Responder(
                username="admin_case_owner",
                email="case_owner@nhaa.gov.in",
                password_hash="$2b$12$synthetic_hash",
                display_name="Case Owner Admin",
                role=UserRole.ADMIN
            )
            session.add(admin)
            await session.flush()

            case = Case(
                external_case_reference="NHAA-2026-TEST-001",
                status=CaseStatus.NEW,
                language="en",
                consent_status="CONSENT_GIVEN",
                assigned_responder_id=admin.id
            )
            session.add(case)
            await session.flush()

            conv = Conversation(
                case_id=case.id,
                session_id="test-session-uuid-1",
                started_at=datetime.now(timezone.utc),
                input_language="en",
                status="ACTIVE"
            )
            session.add(conv)
            await session.flush()

            msg1 = Message(
                conversation_id=conv.id,
                sender_type=MessageSenderType.VICTIM,
                input_source=MessageInputSource.TEXT,
                content="I need emergency assistance regarding domestic safety."
            )
            session.add(msg1)

            assessment = AssessmentModel(
                case_id=case.id,
                assessment_version="gemma-3n-e2b-v1.0",
                assessment_payload={"summary": "High acute fear", "indicators": []}
            )
            session.add(assessment)

            svi = SVIResultModel(
                case_id=case.id,
                svi_version="v1.0",
                score=85.0,
                risk_category="CRITICAL",
                factor_contributions={"physical_safety": 35.0},
                key_drivers=["Physical safety risk"],
                uncertainties=[],
                immediate_safety_attention=True,
                urgent_human_review=True
            )
            session.add(svi)

            rec = RecommendationModel(
                case_id=case.id,
                category="SAFETY_PLANNING",
                priority="CRITICAL",
                reason="Active domestic violence threat",
                supporting_indicators=["physical_safety"],
                evidence_sources=["text"],
                responder_action="Contact emergency coordination desk",
                requires_human_review=True,
                status="PENDING"
            )
            session.add(rec)

            audit = AuditEvent(
                case_id=case.id,
                actor_id=admin.id,
                actor_type="ADMIN",
                event_type="CASE_CREATED",
                entity_type="CASE",
                entity_id=case.id,
                event_metadata={"external_case_reference": case.external_case_reference}
            )
            session.add(audit)

            await session.commit()

            stmt = select(Case).where(Case.id == case.id)
            result = await session.execute(stmt)
            fetched_case = result.scalars().first()

            assert fetched_case is not None
            assert fetched_case.external_case_reference == "NHAA-2026-TEST-001"
            assert fetched_case.assigned_responder_id == admin.id
            assert fetched_case.status == CaseStatus.NEW

        await engine.dispose()

    asyncio.run(run())
