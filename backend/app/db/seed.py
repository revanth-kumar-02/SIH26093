import os
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.db.models.responder import Responder, UserRole
from app.db.models.case import Case, CaseStatus
from app.db.models.conversation import Conversation
from app.db.models.message import Message, MessageSenderType, MessageInputSource
from app.db.models.assessment import AssessmentModel
from app.db.models.svi import SVIResultModel
from app.db.models.recommendation import RecommendationModel
from app.db.models.recommendation_review import RecommendationReview
from app.db.models.ai_signal import AISignal
from app.db.models.audit import AuditEvent

async def seed_database(force_reset: bool = False):
    """Populate database with exactly 2 synthetic development accounts (1 ADMIN, 1 PEOPLE) and 5 demo cases."""
    async with AsyncSessionLocal() as session:
        existing_admin = (await session.execute(
            select(Responder).where(Responder.username == "admin_user")
        )).scalars().first()

        if existing_admin and not force_reset:
            print("Database already contains seed records. Skipping seeding.")
            return

        if force_reset:
            print("Resetting existing records...")
            await session.execute(delete(RecommendationReview))
            await session.execute(delete(AISignal))
            await session.execute(delete(AuditEvent))
            await session.execute(delete(RecommendationModel))
            await session.execute(delete(SVIResultModel))
            await session.execute(delete(AssessmentModel))
            await session.execute(delete(Message))
            await session.execute(delete(Conversation))
            await session.execute(delete(Case))
            await session.execute(delete(Responder))
            await session.commit()

        # Documented development/test seed profiles
        admin_email = os.getenv("ADMIN_EMAIL", "admin@nhaa.gov.in")
        people_email = os.getenv("PEOPLE_EMAIL", "people@nhaa.gov.in")

        print("Seeding exactly 2 synthetic accounts: 1 ADMIN, 1 PEOPLE...")
        admin = Responder(
            id="00000000-0000-0000-0000-000000000001",
            username="admin_user",
            email=admin_email,
            display_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True
        )
        people = Responder(
            id="00000000-0000-0000-0000-000000000002",
            username="people_user",
            email=people_email,
            display_name="Citizen / Complainant",
            role=UserRole.PEOPLE,
            is_active=True
        )
        session.add_all([admin, people])
        await session.flush()

        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # CASE D: Urgent Safety Review (Critical SVI 88.5, Active Danger)
        # External Reference: NHAA-2026-SYN-0812
        # -------------------------------------------------------------
        case_d = Case(
            external_case_reference="NHAA-2026-SYN-0812",
            status=CaseStatus.IN_REVIEW,
            language="en",
            consent_status="CONSENT_GIVEN",
            assigned_responder_id=admin.id,
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(minutes=45)
        )
        session.add(case_d)
        await session.flush()

        conv_d = Conversation(
            case_id=case_d.id,
            session_id="synth-sess-0812-crit",
            started_at=now - timedelta(hours=2),
            input_language="en",
            status="ACTIVE"
        )
        session.add(conv_d)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv_d.id,
                sender_type=MessageSenderType.VICTIM,
                input_source=MessageInputSource.VOICE,
                content="[DEMO / SYNTHETIC DATA] Please help me right now. My ex-partner followed me home, is banging violently on the door, and shouting that he will break the windows. I am hiding in the bathroom and terrified.",
                timestamp=now - timedelta(hours=2)
            ),
            Message(
                conversation_id=conv_d.id,
                sender_type=MessageSenderType.SYSTEM,
                input_source=MessageInputSource.TEXT,
                content="You are not alone. If you are in immediate physical danger, our priority is connecting you with designated human responders and emergency helpline 112 immediately. Please remain hidden in a secured space.",
                timestamp=now - timedelta(hours=1, minutes=58)
            )
        ])

        assessment_d = AssessmentModel(
            case_id=case_d.id,
            assessment_version="gemma-3n-e2b-v1.0",
            assessment_payload={
                "summary": "[DEMO / SYNTHETIC DATA] Imminent physical threat reported. Perpetrator actively present outside domicile attempting forced entry. Severe acute terror.",
                "indicators": [
                    {"category": "physical_safety", "confidence": 0.98, "evidence": "violent door pounding and threats of breaking windows"},
                    {"category": "imminent_danger", "confidence": 0.96, "evidence": "hiding in bathroom with perpetrator on premises"},
                    {"category": "acute_fear", "confidence": 0.95, "evidence": "voice tremor and explicit terror"}
                ],
                "uncertainties": []
            },
            created_at=now - timedelta(hours=1, minutes=55)
        )
        session.add(assessment_d)

        svi_d = SVIResultModel(
            case_id=case_d.id,
            svi_version="v1.0",
            score=88.5,
            risk_category="CRITICAL",
            factor_contributions={
                "physical_safety": 38.0,
                "threats_intimidation": 32.0,
                "acute_fear": 18.5
            },
            key_drivers=["Active Threat at Residence", "Forced Entry Threat", "Extreme Acute Distress"],
            uncertainties=[],
            immediate_safety_attention=True,
            urgent_human_review=True,
            created_at=now - timedelta(hours=1, minutes=55)
        )
        session.add(svi_d)

        rec_d1 = RecommendationModel(
            case_id=case_d.id,
            category="SAFETY_PLANNING",
            priority="CRITICAL",
            reason="[DEMO / SYNTHETIC DATA] Active intruder / domestic threat at residence. Immediate human responder escalation mandatory.",
            supporting_indicators=["imminent physical threat", "attempted forced entry"],
            evidence_sources=["voice_transcription", "acoustic_stress_signal", "gemma_assessment"],
            responder_action="Initiate immediate human emergency desk escalation; verify complainant physical safety and facilitate local PCR dispatch.",
            requires_human_review=True,
            status="PENDING",
            created_at=now - timedelta(hours=1, minutes=55)
        )
        rec_d2 = RecommendationModel(
            case_id=case_d.id,
            category="PSYCHOLOGICAL_FIRST_AID",
            priority="HIGH_PRIORITY",
            reason="[DEMO / SYNTHETIC DATA] Extreme panic and hyperarousal.",
            supporting_indicators=["acute fear", "trembling voice"],
            evidence_sources=["speech_emotion", "gemma_assessment"],
            responder_action="Provide grounding stabilization protocol once immediate physical perimeter is secured.",
            requires_human_review=True,
            status="PENDING",
            created_at=now - timedelta(hours=1, minutes=55)
        )
        session.add_all([rec_d1, rec_d2])

        # -------------------------------------------------------------
        # CASE C: High Vulnerability (Workplace Harassment & Coercion)
        # External Reference: NHAA-2026-SYN-0815
        # -------------------------------------------------------------
        case_c = Case(
            external_case_reference="NHAA-2026-SYN-0815",
            status=CaseStatus.IN_REVIEW,
            language="en",
            consent_status="CONSENT_GIVEN",
            assigned_responder_id=admin.id,
            created_at=now - timedelta(hours=5),
            updated_at=now - timedelta(hours=1)
        )
        session.add(case_c)
        await session.flush()

        conv_c = Conversation(
            case_id=case_c.id,
            session_id="synth-sess-0815-high",
            started_at=now - timedelta(hours=5),
            input_language="en",
            status="ACTIVE"
        )
        session.add(conv_c)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv_c.id,
                sender_type=MessageSenderType.VICTIM,
                input_source=MessageInputSource.TEXT,
                content="[DEMO / SYNTHETIC DATA] My project director threatened to withhold my clearance credentials and fabricate disciplinary charges if I file a complaint with the Internal Committee. I cannot sleep and feel totally trapped.",
                timestamp=now - timedelta(hours=5)
            )
        ])

        assessment_c = AssessmentModel(
            case_id=case_c.id,
            assessment_version="gemma-3n-e2b-v1.0",
            assessment_payload={
                "summary": "[DEMO / SYNTHETIC DATA] Severe retaliatory intimidation in workplace environment. Economic coercion and sleep impairment reported.",
                "indicators": [
                    {"category": "threats_intimidation", "confidence": 0.88, "evidence": "threats of fabricated disciplinary charges"},
                    {"category": "power_imbalance", "confidence": 0.84, "evidence": "senior project director power asymmetry"},
                    {"category": "emotional_distress", "confidence": 0.80, "evidence": "insomnia and feelings of being trapped"}
                ],
                "uncertainties": ["Status of formal Internal Committee grievance registry."]
            },
            created_at=now - timedelta(hours=4, minutes=55)
        )
        session.add(assessment_c)

        svi_c = SVIResultModel(
            case_id=case_c.id,
            svi_version="v1.0",
            score=72.0,
            risk_category="HIGH",
            factor_contributions={
                "threats_intimidation": 32.0,
                "power_imbalance": 24.0,
                "emotional_distress": 16.0
            },
            key_drivers=["Institutional Retaliation", "Power Asymmetry", "Sleep Disruption"],
            uncertainties=["Status of formal Internal Committee grievance registry."],
            immediate_safety_attention=False,
            urgent_human_review=False,
            created_at=now - timedelta(hours=4, minutes=55)
        )
        session.add(svi_c)

        rec_c = RecommendationModel(
            case_id=case_c.id,
            category="LEGAL_AID",
            priority="HIGH_PRIORITY",
            reason="[DEMO / SYNTHETIC DATA] Severe threat of professional retaliation and coercion to suppress statutory grievance.",
            supporting_indicators=["institutional retaliation", "threat of fabricated charges"],
            evidence_sources=["text_transcript", "gemma_assessment"],
            responder_action="Provide confidential referral to District Legal Services Authority (DLSA) panel advocate for PoSH Act advisory.",
            requires_human_review=True,
            status="ACCEPTED",
            responder_decision="ACCEPT",
            responder_note="Verified with complainant. Referred to DLSA workplace grievance cell.",
            reviewed_at=now - timedelta(hours=1),
            reviewed_by=admin.display_name,
            created_at=now - timedelta(hours=4, minutes=55)
        )
        session.add(rec_c)

        # -------------------------------------------------------------
        # CASE B: Moderate Vulnerability (Hindi / Situational Distress / New)
        # External Reference: NHAA-2026-SYN-0820
        # -------------------------------------------------------------
        case_b = Case(
            external_case_reference="NHAA-2026-SYN-0820",
            status=CaseStatus.NEW,
            language="hi",
            consent_status="CONSENT_GIVEN",
            assigned_responder_id=None,
            created_at=now - timedelta(hours=8),
            updated_at=now - timedelta(hours=8)
        )
        session.add(case_b)
        await session.flush()

        conv_b = Conversation(
            case_id=case_b.id,
            session_id="synth-sess-0820-mod",
            started_at=now - timedelta(hours=8),
            input_language="hi",
            status="ACTIVE"
        )
        session.add(conv_b)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv_b.id,
                sender_type=MessageSenderType.VICTIM,
                input_source=MessageInputSource.VOICE,
                content="[DEMO / SYNTHETIC DATA] मैं हाल ही में नए शहर आई हूँ और पड़ोस में कुछ लोग लगातार परेशान कर रहे हैं। यहाँ कोई पहचान नहीं है और बहुत अकेलापन महसूस हो रहा है।",
                timestamp=now - timedelta(hours=8)
            )
        ])

        assessment_b = AssessmentModel(
            case_id=case_b.id,
            assessment_version="gemma-3n-e2b-v1.0",
            assessment_payload={
                "summary": "[DEMO / SYNTHETIC DATA] Relocation-associated vulnerability coupled with local interpersonal friction.",
                "indicators": [
                    {"category": "social_vulnerability", "confidence": 0.72, "evidence": "no local support network"},
                    {"category": "emotional_distress", "confidence": 0.68, "evidence": "feelings of loneliness and anxiety"}
                ],
                "uncertainties": ["Exact frequency and nature of harassment requires responder clarification."]
            },
            created_at=now - timedelta(hours=7, minutes=55)
        )
        session.add(assessment_b)

        svi_b = SVIResultModel(
            case_id=case_b.id,
            svi_version="v1.0",
            score=45.0,
            risk_category="MODERATE",
            factor_contributions={
                "social_vulnerability": 25.0,
                "emotional_distress": 20.0
            },
            key_drivers=["Social Isolation", "Situational Anxiety"],
            uncertainties=["Exact nature of neighborhood friction requires intake clarification."],
            immediate_safety_attention=False,
            urgent_human_review=False,
            created_at=now - timedelta(hours=7, minutes=55)
        )
        session.add(svi_b)

        rec_b = RecommendationModel(
            case_id=case_b.id,
            category="SOCIAL_SUPPORT",
            priority="STANDARD",
            reason="[DEMO / SYNTHETIC DATA] Complainant reports isolation and neighborhood friction in unfamiliar locality.",
            supporting_indicators=["social isolation", "situational anxiety"],
            evidence_sources=["voice_transcription", "gemma_assessment"],
            responder_action="Initiate intake callback and connect with localized community welfare coordinator.",
            requires_human_review=True,
            status="PENDING",
            created_at=now - timedelta(hours=7, minutes=55)
        )
        session.add(rec_b)

        # -------------------------------------------------------------
        # CASE A: Low Vulnerability (English / General Procedural Inquiry / Closed)
        # External Reference: NHAA-2026-SYN-0825
        # -------------------------------------------------------------
        case_a = Case(
            external_case_reference="NHAA-2026-SYN-0825",
            status=CaseStatus.CLOSED,
            language="en",
            consent_status="CONSENT_GIVEN",
            assigned_responder_id=admin.id,
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=1)
        )
        session.add(case_a)
        await session.flush()

        conv_a = Conversation(
            case_id=case_a.id,
            session_id="synth-sess-0825-low",
            started_at=now - timedelta(days=2),
            ended_at=now - timedelta(days=2, minutes=-15),
            input_language="en",
            status="CLOSED"
        )
        session.add(conv_a)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv_a.id,
                sender_type=MessageSenderType.VICTIM,
                input_source=MessageInputSource.TEXT,
                content="[DEMO / SYNTHETIC DATA] Hello, I am inquiring about the official timeline for victim compensation filing and documentation prerequisites.",
                timestamp=now - timedelta(days=2)
            )
        ])

        assessment_a = AssessmentModel(
            case_id=case_a.id,
            assessment_version="gemma-3n-e2b-v1.0",
            assessment_payload={
                "summary": "[DEMO / SYNTHETIC DATA] General informational inquiry regarding procedural timelines.",
                "indicators": [],
                "uncertainties": []
            },
            created_at=now - timedelta(days=2)
        )
        session.add(assessment_a)

        svi_a = SVIResultModel(
            case_id=case_a.id,
            svi_version="v1.0",
            score=18.0,
            risk_category="LOW",
            factor_contributions={"emotional_distress": 18.0},
            key_drivers=["Procedural Query Anxiety"],
            uncertainties=[],
            immediate_safety_attention=False,
            urgent_human_review=False,
            created_at=now - timedelta(days=2)
        )
        session.add(svi_a)

        rec_a = RecommendationModel(
            case_id=case_a.id,
            category="SOCIAL_SUPPORT",
            priority="ROUTINE",
            reason="[DEMO / SYNTHETIC DATA] Procedural documentation inquiry regarding state scheme prerequisites.",
            supporting_indicators=["procedural inquiry"],
            evidence_sources=["text_transcript"],
            responder_action="Provide informational brochure link for compensation application process.",
            requires_human_review=False,
            status="ACCEPTED",
            responder_decision="ACCEPT",
            responder_note="Brochure sent via portal notification. Inquirer satisfied.",
            reviewed_at=now - timedelta(days=1),
            reviewed_by=admin.display_name,
            created_at=now - timedelta(days=2)
        )
        session.add(rec_a)

        # -------------------------------------------------------------
        # CASE E: Multiple Support Recommendations (Tamil / Coercion + Eviction / Awaiting Action)
        # External Reference: NHAA-2026-SYN-0830
        # -------------------------------------------------------------
        case_e = Case(
            external_case_reference="NHAA-2026-SYN-0830",
            status=CaseStatus.AWAITING_RESPONDER_ACTION,
            language="ta",
            consent_status="CONSENT_GIVEN",
            assigned_responder_id=admin.id,
            created_at=now - timedelta(hours=4),
            updated_at=now - timedelta(hours=1)
        )
        session.add(case_e)
        await session.flush()

        conv_e = Conversation(
            case_id=case_e.id,
            session_id="synth-sess-0830-multi",
            started_at=now - timedelta(hours=4),
            input_language="ta",
            status="ACTIVE"
        )
        session.add(conv_e)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv_e.id,
                sender_type=MessageSenderType.VICTIM,
                input_source=MessageInputSource.TEXT,
                content="[DEMO / SYNTHETIC DATA] என் மாமியார் வீட்டில் தொடர்ந்து கொடுமைப்படுத்துகிறார்கள். வீட்டை விட்டு வெளியேற்றி விடுவதாக மிரட்டுகிறார்கள். எனக்கு இரண்டு குழந்தைகள் உள்ளனர்.",
                timestamp=now - timedelta(hours=4)
            )
        ])

        assessment_e = AssessmentModel(
            case_id=case_e.id,
            assessment_version="gemma-3n-e2b-v1.0",
            assessment_payload={
                "summary": "[DEMO / SYNTHETIC DATA] Domestic harassment and threatened eviction with dependent minor children in Tamil.",
                "indicators": [
                    {"category": "shelter_insecurity", "confidence": 0.89, "evidence": "threatened imminent eviction with children"},
                    {"category": "domestic_abuse", "confidence": 0.84, "evidence": "sustained harassment from in-laws"}
                ],
                "uncertainties": ["Availability of maternal family shelter."]
            },
            created_at=now - timedelta(hours=3, minutes=50)
        )
        session.add(assessment_e)

        svi_e = SVIResultModel(
            case_id=case_e.id,
            svi_version="v1.0",
            score=71.0,
            risk_category="HIGH",
            factor_contributions={
                "shelter_insecurity": 30.0,
                "domestic_abuse": 24.0,
                "emotional_distress": 17.0
            },
            key_drivers=["Threatened Eviction with Minors", "Domestic Coercion", "Shelter Vulnerability"],
            uncertainties=["Availability of maternal family shelter."],
            immediate_safety_attention=False,
            urgent_human_review=True,
            created_at=now - timedelta(hours=3, minutes=50)
        )
        session.add(svi_e)

        rec_e1 = RecommendationModel(
            case_id=case_e.id,
            category="PSYCHOLOGICAL_FIRST_AID",
            priority="HIGH_PRIORITY",
            reason="[DEMO / SYNTHETIC DATA] High acute distress and panic regarding safety of dependent minors.",
            supporting_indicators=["acute maternal anxiety", "threat of homelessness"],
            evidence_sources=["text_transcript", "gemma_assessment"],
            responder_action="Schedule immediate trauma-informed tele-counseling support with regional language counselor.",
            requires_human_review=True,
            status="ACCEPTED",
            responder_decision="ACCEPT",
            responder_note="Accepted. Assigned to Tamil-speaking trauma counselor.",
            reviewed_at=now - timedelta(hours=1, minutes=10),
            reviewed_by=admin.display_name,
            created_at=now - timedelta(hours=3, minutes=50)
        )
        rec_e2 = RecommendationModel(
            case_id=case_e.id,
            category="LEGAL_AID",
            priority="HIGH_PRIORITY",
            reason="[DEMO / SYNTHETIC DATA] Threatened unlawful eviction under PWDVA.",
            supporting_indicators=["threatened unlawful eviction", "shared household right"],
            evidence_sources=["text_transcript", "gemma_assessment"],
            responder_action="Provide referral to Protection Officer / Legal Services Authority for emergency residence order.",
            requires_human_review=True,
            status="PENDING",
            created_at=now - timedelta(hours=3, minutes=50)
        )
        rec_e3 = RecommendationModel(
            case_id=case_e.id,
            category="SHELTER_ACCOMMODATION",
            priority="STANDARD",
            reason="[DEMO / SYNTHETIC DATA] Potential need for emergency temporary shelter for complainant and two dependent minors.",
            supporting_indicators=["imminent eviction threat", "minor dependents"],
            evidence_sources=["text_transcript", "gemma_assessment"],
            responder_action="Coordinate with local Swadhar Greh / Sakhi One Stop Centre (OSC) for contingency accommodation.",
            requires_human_review=True,
            status="PENDING",
            created_at=now - timedelta(hours=3, minutes=50)
        )
        session.add_all([rec_e1, rec_e2, rec_e3])

        audit_d = AuditEvent(
            case_id=case_d.id,
            actor_id=admin.id,
            actor_type="ADMIN",
            event_type="CASE_ASSIGNED",
            entity_type="CASE",
            entity_id=case_d.id,
            event_metadata={"priority": "CRITICAL", "safety_alert": True},
            created_at=now - timedelta(hours=1, minutes=50)
        )
        audit_c = AuditEvent(
            case_id=case_c.id,
            actor_id=admin.id,
            actor_type="ADMIN",
            event_type="RECOMMENDATION_ACCEPT",
            entity_type="RECOMMENDATION",
            entity_id=rec_c.id,
            event_metadata={"decision": "ACCEPT", "note": rec_c.responder_note},
            created_at=now - timedelta(hours=1)
        )
        audit_e = AuditEvent(
            case_id=case_e.id,
            actor_id=admin.id,
            actor_type="ADMIN",
            event_type="RECOMMENDATION_ACCEPT",
            entity_type="RECOMMENDATION",
            entity_id=rec_e1.id,
            event_metadata={"decision": "ACCEPT", "note": rec_e1.responder_note},
            created_at=now - timedelta(hours=1, minutes=10)
        )
        session.add_all([audit_d, audit_c, audit_e])

        await session.commit()
        print("Database seeded successfully with 2 accounts (1 ADMIN, 1 PEOPLE) and 5 synthetic demo cases (A-E)!")

if __name__ == "__main__":
    asyncio.run(seed_database(force_reset=True))
