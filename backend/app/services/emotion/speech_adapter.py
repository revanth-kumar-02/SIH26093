import io
import time
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from app.services.emotion.speech_base import BaseSpeechEmotionAdapter
from app.schemas.emotion import SpeechEmotionResult
from app.core.config import settings
from app.core.telemetry import resolve_device, get_system_resources

logger = logging.getLogger(__name__)

# Standard 7 Wav2Vec2 emotion recognition labels from Dpngtm/wav2vec2-emotion-recognition
WAV2VEC2_EMOTION_LABELS = [
    "angry", "calm", "disgust", "fearful", "happy", "sad", "surprised"
]

TARGET_SAMPLE_RATE = 16000
MAX_DURATION_SECONDS = 15.0  # Cap at 15s to guarantee fast latency & protect memory
MIN_DURATION_SECONDS = 0.25  # Minimum 250ms of audio

def preprocess_audio(audio_bytes: bytes) -> np.ndarray:
    """Robust audio preprocessing:
    1. Decode any audio container (WAV/MP3/AAC/OGG/M4A) via PyAV.
    2. Resample to 16,000 Hz mono float32.
    3. Detect invalid or corrupt audio.
    4. Duration constraints: pad very short audio, truncate overly long audio.
    5. Peak-amplitude normalization to [-1.0, 1.0] preventing clipping.
    """
    if not audio_bytes or len(audio_bytes) < 32:
        raise ValueError("Audio data is empty or too short to be valid audio")

    try:
        import av
        container = av.open(io.BytesIO(audio_bytes))
    except Exception as e:
        logger.warning(f"Audio decoding failed: {e}")
        raise ValueError("Invalid or corrupted audio file format")

    try:
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=TARGET_SAMPLE_RATE)
        arrays = []
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                arrays.append(resampled.to_ndarray())
    except Exception as e:
        logger.warning(f"Audio stream extraction failed: {e}")
        raise ValueError("Failed to decode audio stream")

    if not arrays:
        raise ValueError("No audible audio frames found in stream")

    waveform = np.concatenate(arrays, axis=1).squeeze(0).astype(np.float32)

    # Duration handling
    min_samples = int(MIN_DURATION_SECONDS * TARGET_SAMPLE_RATE)
    max_samples = int(MAX_DURATION_SECONDS * TARGET_SAMPLE_RATE)

    if len(waveform) < min_samples:
        # Pad with silence or repeat to reach minimum length
        pad_len = min_samples - len(waveform)
        waveform = np.pad(waveform, (0, pad_len), mode="constant")
    elif len(waveform) > max_samples:
        # Truncate to first max_samples for fast bounded inference
        waveform = waveform[:max_samples]

    # Peak normalization: scale to [-1.0, 1.0] safely
    max_amp = float(np.max(np.abs(waveform)))
    if max_amp > 1e-6:
        waveform = waveform / max_amp

    return waveform

class Wav2Vec2EmotionAdapter(BaseSpeechEmotionAdapter):
    """Production Speech Emotion Recognition adapter using Wav2Vec2."""

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None) -> None:
        self.model_name = model_name or settings.SPEECH_EMOTION_MODEL
        self.device = resolve_device(device or settings.EMOTION_DEVICE)
        self._extractor = None
        self._model = None
        self._is_loaded = False
        logger.info(f"Initialized Wav2Vec2EmotionAdapter on device: {self.device}")

    def is_loaded(self) -> bool:
        return self._is_loaded

    def warmup(self) -> None:
        """Pre-load model weights into memory once."""
        self._load()

    def unload(self) -> None:
        """Free memory if needed."""
        self._extractor = None
        self._model = None
        self._is_loaded = False
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _load(self) -> None:
        if not self._is_loaded:
            import torch
            from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
            logger.info(f"Loading Wav2Vec2 SER model: {self.model_name} on {self.device}...")
            self._extractor = AutoFeatureExtractor.from_pretrained(self.model_name)
            self._model = AutoModelForAudioClassification.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()
            self._is_loaded = True
            res = get_system_resources()
            logger.info(f"Wav2Vec2 model loaded successfully. System RAM RSS: {res.get('ram_rss_mb')} MB")

    def analyze(self, audio_bytes: bytes) -> SpeechEmotionResult:
        if not audio_bytes:
            raise ValueError("Audio bytes are empty")

        self._load()
        import torch

        start_time = time.perf_counter()

        # Preprocessing: 16kHz mono, bounded duration, normalized
        waveform = preprocess_audio(audio_bytes)

        inputs = self._extractor(waveform, sampling_rate=TARGET_SAMPLE_RATE, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = self._model(**inputs).logits
            probs = torch.nn.functional.softmax(logits, dim=-1)[0].cpu().numpy()

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        id2label = getattr(self._model.config, "id2label", None) or {
            str(i): WAV2VEC2_EMOTION_LABELS[i] for i in range(len(WAV2VEC2_EMOTION_LABELS))
        }

        prob_dict: Dict[str, float] = {}
        for idx, prob in enumerate(probs):
            lbl = id2label.get(str(idx), id2label.get(idx, f"label_{idx}"))
            prob_dict[str(lbl).lower()] = float(round(float(prob), 4))

        top_emotion = max(prob_dict.items(), key=lambda item: item[1])[0]

        return SpeechEmotionResult(
            emotion=top_emotion,
            probabilities=prob_dict,
            model_version=self.model_name,
            duration_ms=latency_ms,
            device=self.device
        )

class MockSpeechEmotionAdapter(BaseSpeechEmotionAdapter):
    """Deterministic Mock SER adapter for testing."""

    def __init__(self, device: str = "cpu") -> None:
        self.device = device

    def is_loaded(self) -> bool:
        return True

    def warmup(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def analyze(self, audio_bytes: bytes) -> SpeechEmotionResult:
        if not audio_bytes:
            raise ValueError("Audio bytes are empty")
        if len(audio_bytes) < 8:
            raise ValueError("Audio data is corrupted or too short")

        return SpeechEmotionResult(
            emotion="calm",
            probabilities={
                "angry": 0.04,
                "calm": 0.68,
                "disgust": 0.02,
                "fearful": 0.09,
                "happy": 0.03,
                "sad": 0.10,
                "surprised": 0.04
            },
            model_version="mock-wav2vec2-ser",
            duration_ms=4.2,
            device=self.device
        )
