import io
import wave
import struct
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.asr.service import asr_service
from app.services.asr.indic_conformer import (
    MockIndicConformerAdapter,
    preprocess_audio_for_indic_conformer,
    SUPPORTED_INDIC_LANGUAGES
)

client = TestClient(app)

def create_synthetic_audio(duration_s: float = 1.0, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Generate in-memory WAV audio bytes for testing."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        num_samples = int(duration_s * sample_rate)
        raw = b''.join(struct.pack('<h', int(3000 * ((i % 100) / 100.0 - 0.5))) for i in range(num_samples * channels))
        wav.writeframes(raw)
    return buf.getvalue()

@pytest.fixture(autouse=True)
def use_mock_indic_conformer():
    """Ensure tests run against deterministic mock adapter without requiring gated HF token."""
    original_adapter = asr_service._adapter
    asr_service.set_adapter(MockIndicConformerAdapter())
    yield
    asr_service.set_adapter(original_adapter)

def test_transcribe_missing_session():
    """Verify transcription fails with 404 if session does not exist."""
    audio_bytes = create_synthetic_audio(1.0)
    files = {"audio": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")}
    res = client.post("/api/v1/sessions/non-existent-uuid/transcribe", files=files)
    assert res.status_code == 404
    assert res.json()["detail"] == "Session not found"

def test_transcribe_empty_audio():
    """Verify transcription rejects empty audio payload with 400."""
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    files = {"audio": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    res = client.post(f"/api/v1/sessions/{session_id}/transcribe", files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

def test_transcribe_corrupted_audio():
    """Verify corrupted audio bytes return 400 error."""
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    files = {"audio": ("corrupt.wav", io.BytesIO(b"CORRUPTED_HEADER_DATA_1234567890"), "audio/wav")}
    res = client.post(f"/api/v1/sessions/{session_id}/transcribe", files=files)
    assert res.status_code == 400
    assert "corrupt" in res.json()["detail"].lower() or "invalid" in res.json()["detail"].lower()

def test_transcribe_tamil_ctc():
    """Verify transcription in Tamil using CTC decoding."""
    session_res = client.post("/api/v1/sessions", json={"language": "ta"})
    session_id = session_res.json()["session_id"]

    audio_bytes = create_synthetic_audio(1.0)
    files = {"audio": ("voice.wav", io.BytesIO(audio_bytes), "audio/wav")}
    data = {"language": "ta", "decoder": "ctc"}

    res = client.post(f"/api/v1/sessions/{session_id}/transcribe", files=files, data=data)
    assert res.status_code == 200
    payload = res.json()
    assert payload["session_id"] == session_id
    assert payload["language"] == "ta"
    assert payload["decoder"] == "ctc"
    assert payload["status"] == "completed"
    assert "பாதுகாப்பான" in payload["text"]

def test_transcribe_tamil_rnnt():
    """Verify transcription in Tamil using RNNT decoding."""
    session_res = client.post("/api/v1/sessions", json={"language": "ta"})
    session_id = session_res.json()["session_id"]

    audio_bytes = create_synthetic_audio(1.0)
    files = {"audio": ("voice.wav", io.BytesIO(audio_bytes), "audio/wav")}
    data = {"language": "ta", "decoder": "rnnt"}

    res = client.post(f"/api/v1/sessions/{session_id}/transcribe", files=files, data=data)
    assert res.status_code == 200
    payload = res.json()
    assert payload["decoder"] == "rnnt"
    assert payload["language"] == "ta"
    assert len(payload["text"]) > 0

def test_transcribe_english_ctc():
    """Verify transcription in English using CTC decoding."""
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    audio_bytes = create_synthetic_audio(1.0)
    files = {"audio": ("voice.wav", io.BytesIO(audio_bytes), "audio/wav")}
    data = {"language": "en", "decoder": "ctc"}

    res = client.post(f"/api/v1/sessions/{session_id}/transcribe", files=files, data=data)
    assert res.status_code == 200
    payload = res.json()
    assert payload["language"] == "en"
    assert payload["decoder"] == "ctc"
    assert "shelter" in payload["text"].lower()

def test_transcribe_hindi_rnnt():
    """Verify transcription in Hindi using RNNT decoding."""
    session_res = client.post("/api/v1/sessions", json={"language": "hi"})
    session_id = session_res.json()["session_id"]

    audio_bytes = create_synthetic_audio(1.0)
    files = {"audio": ("voice.wav", io.BytesIO(audio_bytes), "audio/wav")}
    data = {"language": "hi", "decoder": "rnnt"}

    res = client.post(f"/api/v1/sessions/{session_id}/transcribe", files=files, data=data)
    assert res.status_code == 200
    payload = res.json()
    assert payload["language"] == "hi"
    assert payload["decoder"] == "rnnt"
    assert "आश्रय" in payload["text"]

def test_transcribe_unsupported_language():
    """Verify unsupported language code returns 400 error."""
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    audio_bytes = create_synthetic_audio(1.0)
    files = {"audio": ("voice.wav", io.BytesIO(audio_bytes), "audio/wav")}
    data = {"language": "french_unsupported"}

    res = client.post(f"/api/v1/sessions/{session_id}/transcribe", files=files, data=data)
    assert res.status_code == 400
    assert "unsupported language" in res.json()["detail"].lower()

def test_transcribe_invalid_decoder():
    """Verify invalid decoder returns 400 error."""
    session_res = client.post("/api/v1/sessions", json={"language": "en"})
    session_id = session_res.json()["session_id"]

    audio_bytes = create_synthetic_audio(1.0)
    files = {"audio": ("voice.wav", io.BytesIO(audio_bytes), "audio/wav")}
    data = {"language": "en", "decoder": "invalid_beam_search"}

    res = client.post(f"/api/v1/sessions/{session_id}/transcribe", files=files, data=data)
    assert res.status_code == 400
    assert "invalid decoder" in res.json()["detail"].lower()

def test_audio_preprocessing_stereo_to_mono():
    """Verify audio preprocessing downmixes stereo 44.1kHz to 16kHz mono tensor."""
    stereo_wav = create_synthetic_audio(duration_s=1.0, sample_rate=44100, channels=2)
    tensor = preprocess_audio_for_indic_conformer(stereo_wav)
    assert tensor.shape[0] == 1  # Mono
    assert 15000 <= tensor.shape[1] <= 17000  # Resampled to 16kHz