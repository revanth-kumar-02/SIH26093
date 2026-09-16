from typing import Optional
from app.core.config import settings
from app.schemas.emotion import SpeechEmotionResult
from app.services.emotion.speech_base import BaseSpeechEmotionAdapter
from app.services.emotion.speech_adapter import Wav2Vec2EmotionAdapter, MockSpeechEmotionAdapter

class SpeechEmotionService:
    """Orchestration service for Speech Emotion Recognition."""

    def __init__(self, adapter: Optional[BaseSpeechEmotionAdapter] = None) -> None:
        if adapter is not None:
            self._adapter = adapter
        elif settings.USE_MOCK_EMOTION:
            self._adapter = MockSpeechEmotionAdapter()
        else:
            self._adapter = Wav2Vec2EmotionAdapter()

    def set_adapter(self, adapter: BaseSpeechEmotionAdapter) -> None:
        """Allow dynamic adapter swapping for benchmarking."""
        self._adapter = adapter

    def analyze(self, audio_bytes: bytes) -> SpeechEmotionResult:
        """Analyze speech emotion from raw audio bytes."""
        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Audio content is empty")

        if len(audio_bytes) > settings.MAX_AUDIO_BYTES:
            raise ValueError(f"Audio exceeds {settings.MAX_AUDIO_BYTES // (1024 * 1024)} MB limit")

        try:
            return self._adapter.analyze(audio_bytes=audio_bytes)
        finally:
            del audio_bytes

speech_emotion_service = SpeechEmotionService()
