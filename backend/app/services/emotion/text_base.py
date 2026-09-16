from abc import ABC, abstractmethod
from app.schemas.emotion import TextEmotionResult

class BaseTextEmotionAdapter(ABC):
    """Abstract interface for Text Emotion Recognition (TER) model adapters."""

    @abstractmethod
    def analyze(self, text: str) -> TextEmotionResult:
        """Extract structured 28-class GoEmotions scores from text input."""
        pass
