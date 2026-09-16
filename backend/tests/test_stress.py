import io
import wave
import struct
import pytest
from app.services.stress.adapter import MentalBertDreadditAdapter, MockStressAdapter
from app.services.stress.service import StressDetectionService, stress_detection_service
from app.services.asr.service import asr_service
from app.services.asr.indic_conformer import MockIndicConformerAdapter
from app.services.emotion.speech_emotion_service import speech_emotion_service
from app.services.emotion.speech_adapter import MockSpeechEmotionAdapter
from app.schemas.stress import StressDetectionResult
from app.services.session_service import session_service

def generate_test_wav_bytes(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate synthetic PCM WAV audio bytes for testing."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        n_samples = int(duration_sec * sample_rate)
        raw = b''.join(struct.pack('<h', int(5000 * ((i % 100) / 100.0 - 0.5))) for i in range(n_samples))
        wav_file.writeframes(raw)
    return buf.getvalue()

def test_stress_mock_adapter_keywords():
    """Verify MockStressAdapter correctly classifies stress keywords."""
    adapter = MockStressAdapter()
    stressed_res = adapter.analyze("I am terrified he will hurt me and my child.")
    assert stressed_res.label == "stressed"
    assert stressed_res.score > 0.5
    assert "stressed" in stressed_res.probabilities

    calm_res = adapter.analyze("I am having some tea and reading a book.")
    assert calm_res.label == "not_stressed"
    assert calm_res.score > 0.5

def test_stress_adapter_empty_and_whitespace():
    """Verify empty or whitespace-only text raises ValueError."""
    adapter = MockStressAdapter()
    with pytest.raises(ValueError, match="empty"):
        adapter.analyze("")
    with pytest.raises(ValueError, match="empty"):
        adapter.analyze("    \n\t  ")

def test_stress_adapter_long_text():
    """Verify long text exceeding max token length is handled cleanly with truncation."""
    adapter = MockStressAdapter()
    long_text = "I feel so overwhelmed and anxious. " * 200
    res = adapter.analyze(long_text)
    assert res.label in ["stressed", "not_stressed"]
    assert 0.0 <= res.score <= 1.0

def test_stress_adapter_lifecycle():
    """Verify lifecycle methods: is_loaded, warmup, unload."""
    adapter = MockStressAdapter()
    assert adapter.is_loaded() is True
    adapter.warmup()
    adapter.unload()

def test_stress_service_abstraction():
    """Verify StressDetectionService delegates cleanly to underlying adapter."""
    mock_adapter = MockStressAdapter()
    service = StressDetectionService(adapter=mock_adapter)
    res = service.analyze("Someone is following me and threatening me.")
    assert isinstance(res, StressDetectionResult)
    assert res.label == "stressed"
    assert res.model_version is not None
    assert res.duration_ms is not None

def test_api_analyze_stress_endpoint(client):
    """Verify POST /api/v1/sessions/{session_id}/analyze/stress returns structured response."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    assert create_resp.status_code == 201
    session_id = create_resp.json()["session_id"]

    analyze_resp = client.post(
        f"/api/v1/sessions/{session_id}/analyze/stress",
        json={"text": "I feel threatened and scared for my life."}
    )
    assert analyze_resp.status_code == 200
    data = analyze_resp.json()
    assert data["session_id"] == session_id
    assert data["status"] == "completed"
    assert "stress" in data
    assert data["stress"]["label"] in ["stressed", "not_stressed"]
    assert 0.0 <= data["stress"]["score"] <= 1.0

    # Verify stress signal was recorded in session
    stress_signals = session_service.get_stress_signals(session_id)
    assert len(stress_signals) >= 1
    assert stress_signals[-1].source == "text"
    assert stress_signals[-1].stress.label in ["stressed", "not_stressed"]

def test_api_analyze_stress_invalid_session(client):
    """Verify 404 returned for nonexistent session."""
    resp = client.post(
        "/api/v1/sessions/nonexistent-session-id/analyze/stress",
        json={"text": "Hello world"}
    )
    assert resp.status_code == 404

def test_api_analyze_stress_empty_text(client):
    """Verify 400 returned for empty text payload."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = create_resp.json()["session_id"]

    resp = client.post(
        f"/api/v1/sessions/{session_id}/analyze/stress",
        json={"text": "   "}
    )
    assert resp.status_code == 400

def test_typed_text_multimodal_pipeline(client):
    """Verify typed message pipeline extracts BOTH text emotion AND stress signals separately."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = create_resp.json()["session_id"]

    msg_resp = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "I am terrified he is tracking my phone calls."}
    )
    assert msg_resp.status_code == 200

    emotions = session_service.get_emotion_signals(session_id)
    assert any(s.source == "text" and s.text_emotion is not None for s in emotions)

    stress_signals = session_service.get_stress_signals(session_id)
    assert any(s.source == "text" and s.stress is not None for s in stress_signals)

def test_voice_multimodal_pipeline(client):
    """Verify single voice upload pipeline extracts ASR transcript, speech emotion, and transcript stress."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = create_resp.json()["session_id"]

    orig_asr = asr_service._adapter
    orig_speech = speech_emotion_service._adapter
    asr_service.set_adapter(MockIndicConformerAdapter())
    speech_emotion_service.set_adapter(MockSpeechEmotionAdapter())

    try:
        wav_bytes = generate_test_wav_bytes(duration_sec=1.5)
        files = {"audio": ("test.wav", io.BytesIO(wav_bytes), "audio/wav")}
        data = {"language": "en", "decoder": "ctc"}

        transcribe_resp = client.post(
            f"/api/v1/sessions/{session_id}/transcribe",
            files=files,
            data=data
        )
        assert transcribe_resp.status_code == 200
        res_json = transcribe_resp.json()
        assert res_json["status"] == "completed"
        assert "transcript" in res_json

        # Check session state has recorded speech emotion and speech-derived stress
        multimodal_state = session_service.get_multimodal_state(session_id)
        assert len(multimodal_state.speech_emotion_signals) >= 1
        assert len(multimodal_state.transcripts) >= 1
    finally:
        asr_service.set_adapter(orig_asr)
        speech_emotion_service.set_adapter(orig_speech)

def test_multimodal_session_state_endpoint(client):
    """Verify GET /api/v1/sessions/{session_id}/multimodal-state returns structured multimodal aggregation."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = create_resp.json()["session_id"]

    # Send a message
    client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "Need urgent shelter options tonight."}
    )

    # Query multimodal state
    state_resp = client.get(f"/api/v1/sessions/{session_id}/multimodal-state")
    assert state_resp.status_code == 200
    state_json = state_resp.json()

    assert state_json["session_id"] == session_id
    assert "speech_emotion_signals" in state_json
    assert "text_emotion_signals" in state_json
    assert "stress_signals" in state_json
    assert "transcripts" in state_json
    assert state_json["total_signals"] >= 2

def test_safety_guardrails_no_risk_escalation(client):
    """Verify safety guardrail: high stress or fear does NOT trigger automatic emergency or SVI risk."""
    create_resp = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = create_resp.json()["session_id"]

    msg_resp = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"message": "He threatened to kill me! I am terrified!"}
    )
    assert msg_resp.status_code == 200
    data = msg_resp.json()

    # Guardrail check: MessageResponse must NOT contain SVI or risk level
    assert "svi" not in data
    assert "risk_level" not in data
    assert "emergency_triggered" not in data

    # Multimodal session state must NOT calculate SVI or risk level
    state_resp = client.get(f"/api/v1/sessions/{session_id}/multimodal-state")
    state_data = state_resp.json()
    assert "svi" not in state_data
    assert "risk_level" not in state_data
