from abc import ABC, abstractmethod
from app.schemas.emotion import SpeechEmotionResult

class BaseSpeechEmotionAdapter(ABC):
    """Abstract interface for Speech Emotion Recognition (SER) model adapters."""

    @abstractmethod
    def analyze(self, audio_bytes: bytes) -> SpeechEmotionResult:
        """Extract structured emotional indicators from raw audio bytes."""
        pass
