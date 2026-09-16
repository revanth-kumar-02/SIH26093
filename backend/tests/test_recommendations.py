import pytest
from app.services.llm.schemas import (
    TraumaAssessment,
    AssessmentIndicator,
    EvidenceItem
)
from app.services.recommendation.schemas import (
    SupportCategory,
    RecommendationPriority,
    ReviewStatus,
    RecommendationReviewRequest
)
from app.services.recommendation.engine import recommendation_engine
from app.services.recommendation.service import recommendation_service

def create_sample_assessment(
    indicators=None,
    safety_concerns=None,
    observations=None,
    uncertainties=None
) -> TraumaAssessment:
    """Helper to construct TraumaAssessment for unit testing."""
    return TraumaAssessment(
        session_id="test-session-rec",
        indicators=indicators or [],
        key_observations=observations or [],
        uncertainties=uncertainties or [],
        safety_concerns=safety_concerns or [],
        responder_review_points=["Review recommended support pathways."],
        model_version="google/gemma-3n-E2B-it",
        duration_ms=10.0,
        device="cpu"
    )

# ----------------- A. Counselling Support -----------------
def test_counselling_recommendation():
    """Verify COUNSELLING_SUPPORT is surfaced for acute emotional distress."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(
                indicator="acute_emotional_distress",
                category="emotional_distress",
                status="detected",
                confidence=0.85,
                evidence=[EvidenceItem(text="I am shaking with fear", source="text")],
                reason="Verbal fear observed."
            )
        ]
    )
    result = recommendation_engine.generate_recommendations("sess-01", assessment)
    categories = [r.category for r in result.recommendations]
    assert SupportCategory.COUNSELLING_SUPPORT in categories
    c_rec = next(r for r in result.recommendations if r.category == SupportCategory.COUNSELLING_SUPPORT)
    assert c_rec.requires_human_review is True
    assert "acute_emotional_distress" in c_rec.supporting_indicators

# ----------------- B. Legal Aid -----------------
def test_legal_aid_recommendation():
    """Verify LEGAL_AID is surfaced when intimidation and threats are detected."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(
                indicator="intimidation_and_threats",
                category="intimidation_coercion",
                status="detected",
                confidence=0.90,
                evidence=[EvidenceItem(text="He threatened to take my children", source="text")],
                reason="Coercive threat reported."
            )
        ]
    )
    result = recommendation_engine.generate_recommendations("sess-02", assessment)
    categories = [r.category for r in result.recommendations]
    assert SupportCategory.LEGAL_AID in categories
    l_rec = next(r for r in result.recommendations if r.category == SupportCategory.LEGAL_AID)
    assert l_rec.priority == RecommendationPriority.IMPORTANT

# ----------------- C. Medical Assistance -----------------
def test_medical_assistance_recommendation():
    """Verify MEDICAL_ASSISTANCE is surfaced when physical injury is observed."""
    assessment = create_sample_assessment(
        observations=["Complainant reports physical injury and bleeding from an assault."]
    )
    result = recommendation_engine.generate_recommendations("sess-03", assessment)
    categories = [r.category for r in result.recommendations]
    assert SupportCategory.MEDICAL_ASSISTANCE in categories
    m_rec = next(r for r in result.recommendations if r.category == SupportCategory.MEDICAL_ASSISTANCE)
    assert m_rec.requires_human_review is True

# ----------------- D. Safety Assistance -----------------
def test_safety_assistance_recommendation():
    """Verify SAFETY_ASSISTANCE is surfaced for active safety threats."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(
                indicator="imminent_physical_danger",
                category="immediate_safety",
                status="detected",
                confidence=0.95,
                evidence=[EvidenceItem(text="He is at my door", source="text")],
                reason="Active presence outside residence."
            )
        ]
    )
    result = recommendation_engine.generate_recommendations("sess-04", assessment)
    categories = [r.category for r in result.recommendations]
    assert SupportCategory.SAFETY_ASSISTANCE in categories
    assert result.immediate_safety_attention is True

# ----------------- E. Police Assistance Review -----------------
def test_police_assistance_review_never_automated():
    """Verify POLICE_ASSISTANCE is surfaced strictly as an advisory option with informed consent."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(
                indicator="intimidation_and_threats",
                category="intimidation_coercion",
                status="detected",
                confidence=0.88,
                evidence=[EvidenceItem(text="Stalking me constantly", source="text")],
                reason="Criminal intimidation pattern."
            )
        ]
    )
    result = recommendation_engine.generate_recommendations("sess-05", assessment)
    categories = [r.category for r in result.recommendations]
    assert SupportCategory.POLICE_ASSISTANCE in categories
    p_rec = next(r for r in result.recommendations if r.category == SupportCategory.POLICE_ASSISTANCE)
    assert "NEVER report without explicit consent" in p_rec.responder_action

# ----------------- F. Emergency Support Escalation -----------------
def test_emergency_support_escalation():
    """Verify EMERGENCY_SUPPORT is surfaced with URGENT priority for acute safety danger."""
    assessment = create_sample_assessment(
        safety_concerns=["Active physical threat with weapon outside door."]
    )
    result = recommendation_engine.generate_recommendations("sess-06", assessment)
    assert result.immediate_safety_attention is True
    e_rec = next(r for r in result.recommendations if r.category == SupportCategory.EMERGENCY_SUPPORT)
    assert e_rec.priority == RecommendationPriority.URGENT

# ----------------- G. Social Support -----------------
def test_social_support_recommendation():
    """Verify SOCIAL_SUPPORT is surfaced for shelter deprivation and isolation."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(
                indicator="social_and_material_vulnerability",
                category="vulnerability",
                status="detected",
                confidence=0.82,
                evidence=[EvidenceItem(text="No place to sleep tonight", source="text")],
                reason="Shelter insecurity."
            )
        ]
    )
    result = recommendation_engine.generate_recommendations("sess-07", assessment)
    categories = [r.category for r in result.recommendations]
    assert SupportCategory.SOCIAL_SUPPORT in categories

# ----------------- H. Multiple Simultaneous Recommendations -----------------
def test_multiple_simultaneous_recommendations():
    """Verify engine generates distinct multiple pathways without category duplication."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(indicator="acute_emotional_distress", category="emotional_distress", status="detected", confidence=0.8, evidence=[], reason="fear"),
            AssessmentIndicator(indicator="intimidation_and_threats", category="intimidation_coercion", status="detected", confidence=0.85, evidence=[], reason="threats"),
            AssessmentIndicator(indicator="social_and_material_vulnerability", category="vulnerability", status="detected", confidence=0.75, evidence=[], reason="homeless")
        ]
    )
    result = recommendation_engine.generate_recommendations("sess-08", assessment)
    categories = [r.category for r in result.recommendations]
    assert len(categories) == len(set(categories)) # No duplicates
    assert SupportCategory.COUNSELLING_SUPPORT in categories
    assert SupportCategory.LEGAL_AID in categories
    assert SupportCategory.SOCIAL_SUPPORT in categories

# ----------------- I. Insufficient Evidence -----------------
def test_no_recommendation_when_evidence_insufficient():
    """Verify non-crisis interaction generates no urgent escalation."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(indicator="acute_emotional_distress", category="emotional_distress", status="not_detected", confidence=0.9, evidence=[], reason="None")
        ]
    )
    result = recommendation_engine.generate_recommendations("sess-09", assessment)
    assert result.immediate_safety_attention is False
    assert len(result.recommendations) == 0
    assert any("routine" in u.lower() for u in result.uncertainties)

# ----------------- J & K. Uncertainties & Missing Signals -----------------
def test_uncertain_and_missing_signals_handling():
    """Verify assessment uncertainties are cleanly propagated to recommendation result."""
    assessment = create_sample_assessment(
        uncertainties=["Speech audio was absent; vocal acoustics unverified."]
    )
    result = recommendation_engine.generate_recommendations("sess-10", assessment)
    assert "Speech audio was absent; vocal acoustics unverified." in result.uncertainties

# ----------------- L, M, N. Human Review: Accept, Modify, Reject -----------------
def test_human_review_workflow(client):
    """Verify responder review lifecycle: accept, modify, reject with audit logs."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = create_resp.json()["session_id"]

    # Generate recommendations via API
    assessment_payload = {
        "session_id": session_id,
        "indicators": [
            {
                "indicator": "acute_emotional_distress",
                "category": "emotional_distress",
                "status": "detected",
                "confidence": 0.88,
                "evidence": [{"text": "I feel anxious", "source": "text"}],
                "reason": "Verbal distress"
            },
            {
                "indicator": "intimidation_and_threats",
                "category": "intimidation_coercion",
                "status": "detected",
                "confidence": 0.90,
                "evidence": [{"text": "He threatened me", "source": "text"}],
                "reason": "Threats"
            }
        ],
        "key_observations": [],
        "uncertainties": [],
        "safety_concerns": [],
        "responder_review_points": []
    }
    rec_resp = client.post(f"/api/v1/sessions/{session_id}/recommendations", json=assessment_payload)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert len(rec_data["recommendations"]) >= 2
    rec_1 = rec_data["recommendations"][0]
    rec_2 = rec_data["recommendations"][1]

    # 1. Accept recommendation 1
    review_resp_1 = client.post(
        f"/api/v1/sessions/{session_id}/recommendations/{rec_1['recommendation_id']}/review",
        json={"decision": "accepted", "responder_note": "Approved for legal aid referral"}
    )
    assert review_resp_1.status_code == 200
    assert review_resp_1.json()["recommendation"]["status"] == ReviewStatus.ACCEPTED.value
    assert review_resp_1.json()["recommendation"]["responder_decision"] == "accepted"

    # 2. Modify recommendation 2
    review_resp_2 = client.post(
        f"/api/v1/sessions/{session_id}/recommendations/{rec_2['recommendation_id']}/review",
        json={
            "decision": "modified",
            "responder_note": "Changed priority to routine as complainant requests follow-up next week",
            "modified_priority": "routine",
            "modified_action": "Follow-up counselling next week"
        }
    )
    assert review_resp_2.status_code == 200
    assert review_resp_2.json()["recommendation"]["status"] == ReviewStatus.MODIFIED.value
    assert review_resp_2.json()["recommendation"]["priority"] == "routine"

    # 3. Reject recommendation
    review_resp_3 = client.post(
        f"/api/v1/sessions/{session_id}/recommendations/{rec_1['recommendation_id']}/review",
        json={"decision": "rejected", "responder_note": "Complainant declined service"}
    )
    assert review_resp_3.status_code == 200
    assert review_resp_3.json()["recommendation"]["status"] == ReviewStatus.REJECTED.value

# ----------------- O. No Autonomous External Action -----------------
def test_guardrail_no_autonomous_external_action():
    """Verify that even extreme distress never creates automated dispatches."""
    assessment = create_sample_assessment(
        safety_concerns=["Immediate physical threat with knife outside door!"]
    )
    result = recommendation_engine.generate_recommendations("sess-guard", assessment)
    for r in result.recommendations:
        assert r.requires_human_review is True
        assert "call police automatically" not in r.responder_action.lower()

# ----------------- P. No Fabricated Evidence -----------------
def test_no_fabricated_evidence():
    """Verify all evidence sources and indicators match the input assessment."""
    ev_item = EvidenceItem(text="I am locked in room", source="text")
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(
                indicator="acute_emotional_distress",
                category="emotional_distress",
                status="detected",
                confidence=0.8,
                evidence=[ev_item],
                reason="reason"
            )
        ]
    )
    result = recommendation_engine.generate_recommendations("sess-ev", assessment)
    c_rec = next(r for r in result.recommendations if r.category == SupportCategory.COUNSELLING_SUPPORT)
    assert c_rec.evidence_sources == ["text"]

# ----------------- Q. Single Emotion Does NOT Trigger Recommendation -----------------
def test_single_emotion_does_not_trigger_emergency():
    """Verify that an isolated emotion signal without contextual indicators does not trigger emergency escalation."""
    # Assessment where emotional distress was NOT detected in conversation context
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(
                indicator="acute_emotional_distress",
                category="emotional_distress",
                status="not_detected",
                confidence=0.85,
                evidence=[],
                reason="Isolated acoustic fluctuation with no verbal corroboration"
            )
        ]
    )
    result = recommendation_engine.generate_recommendations("sess-isolated", assessment)
    assert result.immediate_safety_attention is False
    assert SupportCategory.EMERGENCY_SUPPORT not in [r.category for r in result.recommendations]

# ----------------- Section 14 Safety Scenarios 1 to 6 -----------------
def test_safety_scenario_1_low_distress_no_safety_concern():
    """Scenario 1: Low distress, no safety concerns -> no emergency escalation."""
    assessment = create_sample_assessment()
    result = recommendation_engine.generate_recommendations("sc-1", assessment)
    assert result.immediate_safety_attention is False
    assert SupportCategory.EMERGENCY_SUPPORT not in [r.category for r in result.recommendations]

def test_safety_scenario_2_sustained_emotional_distress():
    """Scenario 2: Sustained emotional distress with no immediate danger -> counselling surfaced."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(indicator="acute_emotional_distress", category="emotional_distress", status="detected", confidence=0.8, evidence=[], reason="grief")
        ]
    )
    result = recommendation_engine.generate_recommendations("sc-2", assessment)
    assert result.immediate_safety_attention is False
    assert SupportCategory.COUNSELLING_SUPPORT in [r.category for r in result.recommendations]

def test_safety_scenario_3_medical_concern():
    """Scenario 3: Possible medical concern -> medical assistance surfaced."""
    assessment = create_sample_assessment(
        observations=["Complainant sustained head injury from an assault."]
    )
    result = recommendation_engine.generate_recommendations("sc-3", assessment)
    assert SupportCategory.MEDICAL_ASSISTANCE in [r.category for r in result.recommendations]

def test_safety_scenario_4_intimidation_coercion():
    """Scenario 4: Possible intimidation/coercion -> safety/legal support surfaced."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(indicator="intimidation_and_threats", category="intimidation_coercion", status="detected", confidence=0.9, evidence=[], reason="threat")
        ]
    )
    result = recommendation_engine.generate_recommendations("sc-4", assessment)
    cats = [r.category for r in result.recommendations]
    assert SupportCategory.LEGAL_AID in cats

def test_safety_scenario_5_immediate_physical_danger():
    """Scenario 5: Immediate physical danger -> urgent safety/emergency pathway for human review."""
    assessment = create_sample_assessment(
        indicators=[
            AssessmentIndicator(indicator="imminent_physical_danger", category="immediate_safety", status="detected", confidence=0.95, evidence=[], reason="danger")
        ]
    )
    result = recommendation_engine.generate_recommendations("sc-5", assessment)
    assert result.immediate_safety_attention is True
    assert SupportCategory.EMERGENCY_SUPPORT in [r.category for r in result.recommendations]

def test_safety_scenario_6_suicidal_self_harm():
    """Scenario 6: Possible suicidal/self-harm indication -> urgent emergency support for human review."""
    assessment = create_sample_assessment(
        safety_concerns=["Possible suicidal ideation detected in narrative context."]
    )
    result = recommendation_engine.generate_recommendations("sc-6", assessment)
    assert result.immediate_safety_attention is True
    assert SupportCategory.EMERGENCY_SUPPORT in [r.category for r in result.recommendations]
