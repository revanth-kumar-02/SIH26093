import pytest
from app.services.llm.schemas import (
    MultimodalAssessmentInput,
    TraumaAssessment,
    AssessmentIndicator,
    EvidenceItem,
    ConversationTurn
)
from app.services.llm.gemma import GemmaAdapter, MockGemmaAdapter
from app.services.llm.service import GemmaService, gemma_service
from app.schemas.emotion import SpeechEmotionResult, TextEmotionResult, EmotionScore
from app.schemas.stress import StressDetectionResult
from app.services.session_service import session_service

@pytest.fixture(autouse=True)
def setup_mock_gemma():
    """Ensure mock adapter is active during tests for fast, deterministic evaluation."""
    original = gemma_service._adapter
    gemma_service.set_adapter(MockGemmaAdapter())
    yield
    gemma_service.set_adapter(original)

def test_gemma_service_initialization():
    """Verify Gemma service initialization and lifecycle methods."""
    mock_adapter = MockGemmaAdapter()
    service = GemmaService(adapter=mock_adapter)
    assert service.is_loaded() is True
    service.warmup()
    service.unload()

def test_multimodal_input_schema_validation():
    """Verify Pydantic input schema parses valid inputs and supports optional fields."""
    input_data = MultimodalAssessmentInput(
        session_id="session-test-01",
        transcript="I am scared and need help.",
        language="en"
    )
    assert input_data.session_id == "session-test-01"
    assert input_data.transcript == "I am scared and need help."
    assert input_data.speech_emotion is None
    assert input_data.stress is None
    assert input_data.conversation_context == []

def test_trauma_assessment_output_schema_validation():
    """Verify output schema validates indicators, categories, and review points."""
    indicator = AssessmentIndicator(
        indicator="acute_emotional_distress",
        category="emotional_distress",
        status="detected",
        confidence=0.85,
        evidence=[EvidenceItem(text="I am scared", source="text")],
        reason="Expressed verbal distress."
    )
    assessment = TraumaAssessment(
        session_id="session-test-01",
        indicators=[indicator],
        key_observations=["Observed verbal fear."],
        uncertainties=["Speech audio was absent."],
        safety_concerns=["No immediate physical danger noted."],
        responder_review_points=["Follow up with empathetic inquiry."],
        model_version="test-model",
        duration_ms=12.5,
        device="cpu"
    )
    assert len(assessment.indicators) == 1
    assert assessment.indicators[0].category == "emotional_distress"
    assert assessment.indicators[0].evidence[0].source == "text"

def test_malformed_model_output_fallback():
    """Verify non-JSON model generation falls back gracefully to structured fallback."""
    adapter = GemmaAdapter(model_id="mock-id", device="cpu")
    input_data = MultimodalAssessmentInput(session_id="session-fallback-01", transcript="test")
    fallback = adapter._build_error_fallback(input_data, raw_text="Invalid random text", duration_ms=50.0)
    assert isinstance(fallback, TraumaAssessment)
    assert fallback.session_id == "session-fallback-01"
    assert len(fallback.uncertainties) > 0

def test_missing_signals_handling():
    """Verify input with missing signals documents uncertainties explicitly."""
    adapter = MockGemmaAdapter()
    inp = MultimodalAssessmentInput(
        session_id="session-missing-01",
        transcript="Just checking if anyone is there."
    )
    res = adapter.assess(inp)
    assert isinstance(res, TraumaAssessment)
    # Both speech emotion, text emotion, and stress should be flagged in uncertainties
    assert any("speech" in u.lower() for u in res.uncertainties)
    assert any("stress" in u.lower() for u in res.uncertainties)

def test_text_only_input_evidence_attribution():
    """Verify text-only input attributes all textual evidence to 'text'."""
    adapter = MockGemmaAdapter()
    inp = MultimodalAssessmentInput(
        session_id="session-text-01",
        transcript="He keeps threatening to harm my family.",
        input_source="text"
    )
    res = adapter.assess(inp)
    threat_ind = next((i for i in res.indicators if i.indicator == "intimidation_and_threats"), None)
    assert threat_ind is not None
    assert threat_ind.status == "detected"
    assert all(ev.source == "text" for ev in threat_ind.evidence)

def test_speech_and_multimodal_synthesis():
    """Verify multimodal input synthesizes speech emotion, text emotion, and stress without hallucination."""
    adapter = MockGemmaAdapter()
    inp = MultimodalAssessmentInput(
        session_id="session-multi-01",
        transcript="He said he would track me down and hurt me.",
        speech_emotion=SpeechEmotionResult(
            emotion="fearful",
            probabilities={"fearful": 0.88, "calm": 0.12},
            model_version="Dpngtm/wav2vec2-emotion-recognition",
            duration_ms=40.0,
            device="cpu"
        ),
        text_emotion=TextEmotionResult(
            top_emotion="fear",
            emotions=[EmotionScore(label="fear", score=0.91)],
            model_version="SamLowe/roberta-base-go_emotions",
            duration_ms=15.0,
            device="cpu"
        ),
        stress=StressDetectionResult(
            label="stressed",
            score=0.95,
            probabilities={"not_stressed": 0.05, "stressed": 0.95},
            model_version="jtvallente/mentalbert_dreaddit_best",
            duration_ms=30.0,
            device="cpu"
        ),
        input_source="multimodal"
    )
    res = adapter.assess(inp)
    distress_ind = next((i for i in res.indicators if i.indicator == "acute_emotional_distress"), None)
    assert distress_ind is not None
    assert distress_ind.status == "detected"
    # Verify evidence comes from multiple modalities
    sources = {ev.source for ev in distress_ind.evidence}
    assert "speech" in sources or "multimodal" in sources

def test_safety_concerns_extraction():
    """Verify imminent physical danger triggers safety concerns and responder review points."""
    adapter = MockGemmaAdapter()
    inp = MultimodalAssessmentInput(
        session_id="session-safety-01",
        transcript="He is right outside with a knife and threatening to kill me right now!",
        input_source="text"
    )
    res = adapter.assess(inp)
    danger_ind = next((i for i in res.indicators if i.indicator == "imminent_physical_danger"), None)
    assert danger_ind is not None
    assert danger_ind.status == "detected"
    assert len(res.safety_concerns) > 0
    assert len(res.responder_review_points) > 0

def test_guardrail_communication_difficulty_not_trauma():
    """Verify fragmented narrative does NOT claim proof of trauma."""
    adapter = MockGemmaAdapter()
    inp = MultimodalAssessmentInput(
        session_id="session-comm-01",
        transcript="I... don't know...",
        input_source="text"
    )
    res = adapter.assess(inp)
    comm_ind = next((i for i in res.indicators if i.indicator == "fragmented_or_hesitant_communication"), None)
    assert comm_ind is not None
    assert "does not prove trauma" in comm_ind.reason.lower()

def test_api_analyze_multimodal_endpoint(client):
    """Verify POST /api/v1/sessions/{session_id}/analyze/multimodal returns 200 with TraumaAssessment."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    assert create_resp.status_code == 201
    session_id = create_resp.json()["session_id"]

    # Post explicit multimodal input
    payload = {
        "session_id": session_id,
        "transcript": "I am terrified and locked myself in the bathroom.",
        "input_source": "text",
        "language": "en"
    }
    resp = client.post(f"/api/v1/sessions/{session_id}/analyze/multimodal", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert "indicators" in data
    assert "key_observations" in data
    assert "uncertainties" in data
    assert "responder_review_points" in data
    assert len(data["indicators"]) > 0

def test_api_analyze_multimodal_invalid_session(client):
    """Verify 404 returned for nonexistent session."""
    resp = client.post("/api/v1/sessions/nonexistent-session/analyze/multimodal", json={})
    assert resp.status_code == 404

def test_api_analyze_multimodal_auto_enrichment(client):
    """Verify endpoint auto-populates missing signals from accumulated session evidence."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = create_resp.json()["session_id"]

    # Send a message to populate session state with message, text emotion, and stress signals
    client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "I am scared he is following me."}
    )

    # Call multimodal analysis with empty body
    resp = client.post(f"/api/v1/sessions/{session_id}/analyze/multimodal")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert len(data["indicators"]) > 0

def test_guardrail_no_svi_no_emergency_dispatch(client):
    """Verify TraumaAssessment never outputs SVI score, risk tier, or automated emergency dispatch."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = create_resp.json()["session_id"]

    resp = client.post(
        f"/api/v1/sessions/{session_id}/analyze/multimodal",
        json={"transcript": "He is going to kill me tonight!"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "svi" not in data
    assert "risk_level" not in data
    assert "emergency_dispatched" not in data
    assert "police_notified" not in data
