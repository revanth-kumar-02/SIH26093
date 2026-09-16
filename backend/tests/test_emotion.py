import io
import time
import wave
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.session_service import session_service
from app.services.asr.service import asr_service
from app.services.asr.indic_conformer import MockIndicConformerAdapter
from app.services.emotion.speech_emotion_service import speech_emotion_service
from app.services.emotion.speech_adapter import (
    MockSpeechEmotionAdapter,
    Wav2Vec2EmotionAdapter,
    preprocess_audio,
    WAV2VEC2_EMOTION_LABELS
)
from app.services.emotion.text_emotion_service import text_emotion_service
from app.services.emotion.text_adapter import (
    MockTextEmotionAdapter,
    GoEmotionsAdapter,
    GO_EMOTIONS_TAXONOMY
)
from app.core.telemetry import get_system_resources

client = TestClient(app)

def create_synthetic_wav(duration_s: float = 1.0, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Generate synthetic PCM WAV bytes."""
    import struct
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        num_samples = int(duration_s * sample_rate)
        raw = b''.join(struct.pack('<h', int(5000 * ((i % 100) / 100.0 - 0.5))) for i in range(num_samples * channels))
        wav.writeframes(raw)
    return buf.getvalue()

# ----------------- Speech Emotion Tests -----------------

def test_speech_preprocessing_valid_wav():
    """Verify preprocessing resamples, downmixes stereo to mono, and normalizes."""
    stereo_wav = create_synthetic_wav(duration_s=1.5, sample_rate=44100, channels=2)
    waveform = preprocess_audio(stereo_wav)
    assert waveform is not None
    assert len(waveform.shape) == 1  # Mono
    assert abs(waveform).max() <= 1.01  # Normalized

def test_speech_preprocessing_duration_padding():
    """Verify very short audio (<0.25s) is padded to minimum duration."""
    short_wav = create_synthetic_wav(duration_s=0.1, sample_rate=16000, channels=1)
    waveform = preprocess_audio(short_wav)
    assert len(waveform) >= 4000  # >= 0.25s at 16kHz

def test_speech_preprocessing_duration_truncation():
    """Verify overly long audio (>15s) is truncated to bound latency and memory."""
    long_wav = create_synthetic_wav(duration_s=16.0, sample_rate=16000, channels=1)
    waveform = preprocess_audio(long_wav)
    assert len(waveform) <= 15 * 16000  # Cap at 15s

def test_speech_preprocessing_corrupted_audio():
    """Verify corrupted/invalid audio raises clean ValueError."""
    corrupt_bytes = b'NOT_A_VALID_AUDIO_HEADER_12345678901234567890'
    with pytest.raises(ValueError, match="Invalid or corrupted"):
        preprocess_audio(corrupt_bytes)

def test_speech_emotion_mock_adapter():
    """Verify mock adapter returns structured 7-class distribution."""
    adapter = MockSpeechEmotionAdapter()
    wav = create_synthetic_wav(duration_s=1.0)
    result = adapter.analyze(wav)
    assert result.emotion in WAV2VEC2_EMOTION_LABELS
    assert len(result.probabilities) == 7
    for label in WAV2VEC2_EMOTION_LABELS:
        assert label in result.probabilities

def test_speech_emotion_label_mapping():
    """Verify Wav2Vec2 standard labels match expected 7 classes."""
    expected_labels = ["angry", "calm", "disgust", "fearful", "happy", "sad", "surprised"]
    assert sorted(WAV2VEC2_EMOTION_LABELS) == sorted(expected_labels)

# ----------------- Text Emotion Tests -----------------

def test_text_emotion_empty_input():
    """Verify empty or whitespace text raises ValueError."""
    adapter = MockTextEmotionAdapter()
    with pytest.raises(ValueError, match="empty"):
        adapter.analyze("")
    with pytest.raises(ValueError, match="empty"):
        adapter.analyze("    ")

def test_text_emotion_valid_output_schema():
    """Verify output conforms to GoEmotions schema."""
    adapter = MockTextEmotionAdapter()
    result = adapter.analyze("I am scared for my safety tonight")
    assert result.top_emotion == "fear"
    assert len(result.emotions) >= 3
    assert result.emotions[0].score >= 0.0

def test_text_emotion_multilingual_input():
    """Verify multilingual input behavior does not crash and yields valid signals."""
    adapter = MockTextEmotionAdapter()
    # Tamil
    ta_res = adapter.analyze("நான் மிகவும் பயப்படுகிறேன், எனக்கு பாதுகாப்பு வேண்டும்")
    assert ta_res.top_emotion in ["fear", "nervousness", "neutral"]
    # Hindi
    hi_res = adapter.analyze("मुझे बहुत डर लग रहा है, कृपया मदद करें")
    assert hi_res.top_emotion in ["fear", "nervousness", "neutral"]

def test_text_taxonomy_completeness():
    """Verify full 28 GoEmotions taxonomy is defined."""
    assert len(GO_EMOTIONS_TAXONOMY) == 28
    assert "fear" in GO_EMOTIONS_TAXONOMY
    assert "sadness" in GO_EMOTIONS_TAXONOMY
    assert "neutral" in GO_EMOTIONS_TAXONOMY

# ----------------- Integration & API Tests -----------------

def test_api_transcribe_with_speech_emotion():
    """Verify voice upload endpoint returns both transcript and speech_emotion typed."""
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    original_speech = speech_emotion_service._adapter
    original_asr = asr_service._adapter
    asr_service.set_adapter(MockIndicConformerAdapter())
    speech_emotion_service.set_adapter(MockSpeechEmotionAdapter())

    try:
        wav = create_synthetic_wav(duration_s=1.0)
        files = {"audio": ("test.wav", io.BytesIO(wav), "audio/wav")}
        data = {"language": "en"}
        res = client.post(f"/api/v1/sessions/{session_id}/transcribe", files=files, data=data)
        assert res.status_code == 200
        payload = res.json()
        assert "transcript" in payload
        assert "speech_emotion" in payload
        assert payload["speech_emotion"]["emotion"] in WAV2VEC2_EMOTION_LABELS
        assert "probabilities" in payload["speech_emotion"]
    finally:
        speech_emotion_service.set_adapter(original_speech)
        asr_service.set_adapter(original_asr)

def test_api_chat_message_records_text_emotion():
    """Verify chat message records text emotion signal internally in session."""
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    original_adapter = text_emotion_service._adapter
    text_emotion_service.set_adapter(MockTextEmotionAdapter())

    try:
        msg_res = client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Someone is threatening me at my hostel"}
        )
        assert msg_res.status_code == 200
        signals_res = client.get(f"/api/v1/sessions/{session_id}/signals")
        assert signals_res.status_code == 200
        signals = signals_res.json()
        assert len(signals) >= 1
        assert signals[0]["source"] == "text"
        assert signals[0]["text_emotion"]["top_emotion"] == "fear"
    finally:
        text_emotion_service.set_adapter(original_adapter)

def test_api_analyze_text_endpoint():
    """Verify dedicated POST /sessions/{id}/analyze/text."""
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    original_adapter = text_emotion_service._adapter
    text_emotion_service.set_adapter(MockTextEmotionAdapter())

    try:
        res = client.post(
            f"/api/v1/sessions/{session_id}/analyze/text",
            json={"text": "I need urgent shelter assistance"}
        )
        assert res.status_code == 200
        payload = res.json()
        assert "top_emotion" in payload
        assert "emotions" in payload
    finally:
        text_emotion_service.set_adapter(original_adapter)

def test_api_error_handling_empty_and_missing():
    """Verify API returns safe, trauma-informed errors without stack traces."""
    res = client.post("/api/v1/sessions/non-existent-uuid/analyze/text", json={"text": "hello"})
    assert res.status_code == 404
    assert res.json()["detail"] == "Session not found"

    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    files = {"audio": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    res = client.post(f"/api/v1/sessions/{session_id}/analyze/audio", files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

def test_resource_monitoring_telemetry():
    """Measure latency, memory, and device reporting."""
    # Warmup first call
    _ = get_system_resources()
    start = time.perf_counter()
    resources = get_system_resources()
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert "ram_rss_mb" in resources or "ram_error" in resources
    assert elapsed_ms < 500.0