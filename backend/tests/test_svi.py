import pytest
from app.services.llm.schemas import (
    TraumaAssessment,
    AssessmentIndicator,
    EvidenceItem
)
from app.services.svi.config import SVI_CONFIG_VERSION, FACTOR_WEIGHTS, RISK_BANDS
from app.services.svi.schemas import SVIInput, SVIResult, RiskCategory
from app.services.svi.engine import svi_engine
from app.services.svi.service import svi_service

def make_indicator(
    indicator: str,
    category: str,
    status: str = "detected",
    confidence: float = 0.85,
    evidence_texts: list = None,
    evidence_source: str = "text"
) -> AssessmentIndicator:
    evidence = [EvidenceItem(text=t, source=evidence_source) for t in (evidence_texts or ["Default evidence excerpt"])]
    return AssessmentIndicator(
        indicator=indicator,
        category=category,
        status=status,
        confidence=confidence,
        evidence=evidence,
        reason=f"Observed {indicator}"
    )

# 1. Empty / Minimal Input
def test_svi_empty_minimal_input():
    inp = SVIInput(session_id="svi-test-empty")
    res = svi_engine.calculate_svi(inp)
    assert res.score == 0.0
    assert res.risk_category == RiskCategory.LOW
    assert res.immediate_safety_attention is False
    assert res.urgent_human_review is False
    assert res.requires_human_review is True

# 2. No Vulnerability Indicators
def test_svi_no_vulnerability_indicators():
    inp = SVIInput(
        session_id="svi-test-none",
        indicators=[
            make_indicator("acute_emotional_distress", "emotional_distress", status="not_detected"),
            make_indicator("intimidation_and_threats", "intimidation_coercion", status="not_detected")
        ]
    )
    res = svi_engine.calculate_svi(inp)
    assert res.score == 0.0
    assert res.risk_category == RiskCategory.LOW

# 3. Low Vulnerability
def test_svi_low_vulnerability():
    inp = SVIInput(
        session_id="svi-test-low",
        indicators=[
            make_indicator("acute_emotional_distress", "emotional_distress", status="detected", confidence=0.70)
        ]
    )
    res = svi_engine.calculate_svi(inp)
    assert 0.0 < res.score <= 29.9
    assert res.risk_category == RiskCategory.LOW

# 4. Moderate Vulnerability
def test_svi_moderate_vulnerability():
    inp = SVIInput(
        session_id="svi-test-mod",
        indicators=[
            make_indicator("acute_emotional_distress", "emotional_distress", status="detected", confidence=0.85),
            make_indicator("social_and_material_vulnerability", "vulnerability", status="detected", confidence=0.85),
            make_indicator("fragmented_or_hesitant_communication", "communication_difficulty", status="detected", confidence=0.80)
        ]
    )
    res = svi_engine.calculate_svi(inp)
    assert 30.0 <= res.score <= 59.9
    assert res.risk_category == RiskCategory.MODERATE

# 5. High Vulnerability
def test_svi_high_vulnerability():
    inp = SVIInput(
        session_id="svi-test-high",
        indicators=[
            make_indicator("intimidation_and_threats", "intimidation_coercion", status="detected", confidence=0.92),
            make_indicator("acute_emotional_distress", "emotional_distress", status="detected", confidence=0.90),
            make_indicator("social_and_material_vulnerability", "vulnerability", status="detected", confidence=0.88),
            make_indicator("fragmented_or_hesitant_communication", "communication_difficulty", status="detected", confidence=0.80)
        ]
    )
    res = svi_engine.calculate_svi(inp)
    assert 60.0 <= res.score <= 84.9
    assert res.risk_category == RiskCategory.HIGH

# 6. Critical Vulnerability
def test_svi_critical_vulnerability():
    inp = SVIInput(
        session_id="svi-test-crit",
        indicators=[
            make_indicator("imminent_physical_danger", "immediate_safety", status="detected", confidence=0.95),
            make_indicator("intimidation_and_threats", "intimidation_coercion", status="detected", confidence=0.95),
            make_indicator("self_harm_indications", "immediate_safety", status="detected", confidence=0.92),
            make_indicator("acute_emotional_distress", "emotional_distress", status="detected", confidence=0.90),
            make_indicator("social_and_material_vulnerability", "vulnerability", status="detected", confidence=0.90)
        ]
    )
    res = svi_engine.calculate_svi(inp)
    assert 85.0 <= res.score <= 100.0
    assert res.risk_category == RiskCategory.CRITICAL
    assert res.immediate_safety_attention is True
    assert res.urgent_human_review is True

# 7 & 8. Confidence Sensitivity
def test_svi_high_vs_low_confidence_sensitivity():
    inp_high = SVIInput(
        session_id="s-high",
        indicators=[make_indicator("intimidation_and_threats", "intimidation_coercion", confidence=0.95)]
    )
    inp_low = SVIInput(
        session_id="s-low",
        indicators=[make_indicator("intimidation_and_threats", "intimidation_coercion", confidence=0.30)]
    )
    res_high = svi_engine.calculate_svi(inp_high)
    res_low = svi_engine.calculate_svi(inp_low)
    assert res_high.score > res_low.score
    threat_high = next(f for f in res_high.factor_contributions if f.factor_id == "threats_intimidation")
    threat_low = next(f for f in res_low.factor_contributions if f.factor_id == "threats_intimidation")
    assert threat_high.contribution > threat_low.contribution

# 9. Uncertain Evidence Handling
def test_svi_uncertain_evidence_penalty():
    inp_det = SVIInput(
        session_id="s-det",
        indicators=[make_indicator("intimidation_and_threats", "intimidation_coercion", status="detected", confidence=0.85)]
    )
    inp_unc = SVIInput(
        session_id="s-unc",
        indicators=[make_indicator("intimidation_and_threats", "intimidation_coercion", status="uncertain", confidence=0.85)]
    )
    res_det = svi_engine.calculate_svi(inp_det)
    res_unc = svi_engine.calculate_svi(inp_unc)
    assert res_det.score > res_unc.score
    f_unc = next(f for f in res_unc.factor_contributions if f.factor_id == "threats_intimidation")
    assert f_unc.presence == 0.35 # Penalized presence

# 10. Missing Signals Handling
def test_svi_missing_signals_handling():
    inp = SVIInput(
        session_id="s-missing",
        indicators=[make_indicator("acute_emotional_distress", "emotional_distress", status="detected")],
        uncertainties=["Speech audio was absent."]
    )
    res = svi_engine.calculate_svi(inp)
    assert "Speech audio was absent." in res.uncertainties
    # Missing signals do not artificially jump score to high
    assert res.risk_category == RiskCategory.LOW

# 11. Duplicate Evidence Anti-Double Counting
def test_svi_duplicate_evidence_anti_double_counting():
    # Adding the identical text snippet 5 times must not multiply score
    ind_single = make_indicator("acute_emotional_distress", "emotional_distress", evidence_texts=["I am scared"])
    ind_multi_dups = make_indicator(
        "acute_emotional_distress",
        "emotional_distress",
        evidence_texts=["I am scared", "I am scared", "I am scared", "I am scared", "I am scared"]
    )
    res_single = svi_engine.calculate_svi(SVIInput(session_id="s1", indicators=[ind_single]))
    res_dups = svi_engine.calculate_svi(SVIInput(session_id="s2", indicators=[ind_multi_dups]))
    f_single = next(f for f in res_single.factor_contributions if f.factor_id == "emotional_distress")
    f_dups = next(f for f in res_dups.factor_contributions if f.factor_id == "emotional_distress")
    assert f_single.contribution == f_dups.contribution
    assert res_single.score == res_dups.score

# 12. Cross-Modal Corroboration Bonus
def test_svi_cross_modal_corroboration():
    ind_text_only = AssessmentIndicator(
        indicator="acute_emotional_distress",
        category="emotional_distress",
        status="detected",
        confidence=0.85,
        evidence=[EvidenceItem(text="I am afraid", source="text")],
        reason="text"
    )
    ind_multi = AssessmentIndicator(
        indicator="acute_emotional_distress",
        category="emotional_distress",
        status="detected",
        confidence=0.85,
        evidence=[
            EvidenceItem(text="I am afraid", source="text"),
            EvidenceItem(text="fearful vocal prosody", source="speech")
        ],
        reason="multi"
    )
    res_text = svi_engine.calculate_svi(SVIInput(session_id="m1", indicators=[ind_text_only]))
    res_multi = svi_engine.calculate_svi(SVIInput(session_id="m2", indicators=[ind_multi]))
    f_text = next(f for f in res_text.factor_contributions if f.factor_id == "emotional_distress")
    f_multi = next(f for f in res_multi.factor_contributions if f.factor_id == "emotional_distress")
    assert f_multi.corroborated is True
    assert f_text.corroborated is False
    assert f_multi.contribution > f_text.contribution

# 13, 14, 15. Single Emotion & Stress Guardrails
def test_single_emotion_and_stress_guardrails():
    """Fear or stress alone must NEVER create Critical or High risk."""
    ind_fear = make_indicator("acute_emotional_distress", "emotional_distress", confidence=0.99)
    res_fear = svi_engine.calculate_svi(SVIInput(session_id="g1", indicators=[ind_fear]))
    assert res_fear.risk_category == RiskCategory.LOW
    assert res_fear.score <= 20.0

def test_communication_difficulty_alone_not_trauma():
    """Communication difficulty alone has minimal contribution and does NOT create high SVI."""
    ind_comm = make_indicator("fragmented_or_hesitant_communication", "communication_difficulty", confidence=0.95)
    res = svi_engine.calculate_svi(SVIInput(session_id="comm-alone", indicators=[ind_comm]))
    assert res.score <= 5.0
    assert res.risk_category == RiskCategory.LOW

# 17 & 18. Immediate Safety & Self-Harm Flags
def test_immediate_safety_and_self_harm_flags():
    inp = SVIInput(
        session_id="s-flags",
        safety_concerns=["Immediate threat: aggressor has a weapon outside."]
    )
    res = svi_engine.calculate_svi(inp)
    assert res.immediate_safety_attention is True
    assert res.urgent_human_review is True

    inp_suicide = SVIInput(
        session_id="s-suicide",
        safety_concerns=["Possible suicidal ideation detected in narrative context."]
    )
    res_suicide = svi_engine.calculate_svi(inp_suicide)
    assert res_suicide.immediate_safety_attention is True
    assert res_suicide.urgent_human_review is True

# 19 & 20. Score Normalization & Boundaries
def test_score_normalization_and_boundaries():
    # Maximum possible input
    inp_max = SVIInput(
        session_id="s-max",
        indicators=[
            make_indicator("acute_emotional_distress", "emotional_distress", confidence=1.0),
            make_indicator("intimidation_and_threats", "intimidation_coercion", confidence=1.0),
            make_indicator("imminent_physical_danger", "immediate_safety", confidence=1.0),
            make_indicator("self_harm_indications", "immediate_safety", confidence=1.0),
            make_indicator("social_and_material_vulnerability", "vulnerability", confidence=1.0),
            make_indicator("fragmented_or_hesitant_communication", "communication_difficulty", confidence=1.0)
        ]
    )
    res = svi_engine.calculate_svi(inp_max)
    assert 0.0 <= res.score <= 100.0

# 21. Deterministic Repeated Calculations
def test_svi_deterministic_reproducibility():
    inp = SVIInput(
        session_id="s-repro",
        indicators=[
            make_indicator("intimidation_and_threats", "intimidation_coercion", confidence=0.88),
            make_indicator("acute_emotional_distress", "emotional_distress", confidence=0.82)
        ]
    )
    scores = [svi_engine.calculate_svi(inp).score for _ in range(50)]
    assert len(set(scores)) == 1 # 100% bit-identical

# 22. Configuration Versioning
def test_svi_configuration_versioning():
    inp = SVIInput(session_id="s-ver")
    res = svi_engine.calculate_svi(inp)
    assert res.svi_version == SVI_CONFIG_VERSION
    assert res.audit_metadata["config_version"] == SVI_CONFIG_VERSION

# 23 & 24. Pydantic Validation Bounds
def test_svi_schema_validation():
    with pytest.raises(Exception):
        # Confidence out of bounds
        make_indicator("test", "test", confidence=1.5)

# 25. No Automatic External Dispatch
def test_svi_no_automatic_external_dispatch():
    inp = SVIInput(
        session_id="s-no-dispatch",
        safety_concerns=["Immediate physical assault danger!"]
    )
    res = svi_engine.calculate_svi(inp)
    assert res.requires_human_review is True
    assert "dispatch_status" not in res.model_dump()
    assert "police_notified" not in res.model_dump()

# Sensitivity: Evidence Addition and Removal
def test_svi_evidence_addition_and_removal_sensitivity():
    ind_base = make_indicator("intimidation_and_threats", "intimidation_coercion", confidence=0.8)
    ind_added = make_indicator("acute_emotional_distress", "emotional_distress", confidence=0.8)
    res_base = svi_engine.calculate_svi(SVIInput(session_id="b1", indicators=[ind_base]))
    res_added = svi_engine.calculate_svi(SVIInput(session_id="b2", indicators=[ind_base, ind_added]))
    assert res_added.score > res_base.score

# API Integration Tests
def test_api_calculate_svi_endpoint(client):
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = create_resp.json()["session_id"]

    payload = {
        "session_id": session_id,
        "indicators": [
            {
                "indicator": "intimidation_and_threats",
                "category": "intimidation_coercion",
                "status": "detected",
                "confidence": 0.90,
                "evidence": [{"text": "Threatened me", "source": "text"}],
                "reason": "Threats"
            }
        ],
        "safety_concerns": [],
        "observations": []
    }
    resp = client.post(f"/api/v1/sessions/{session_id}/svi", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert "score" in data
    assert "risk_category" in data
    assert "factor_contributions" in data
    assert data["requires_human_review"] is True

    # Test GET endpoint
    get_resp = client.get(f"/api/v1/sessions/{session_id}/svi")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["score"] == data["score"]
    assert get_data["risk_category"] == data["risk_category"]
