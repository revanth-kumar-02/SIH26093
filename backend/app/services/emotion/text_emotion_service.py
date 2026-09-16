from typing import Optional
from app.core.config import settings
from app.schemas.emotion import TextEmotionResult
from app.services.emotion.text_base import BaseTextEmotionAdapter
from app.services.emotion.text_adapter import GoEmotionsAdapter, MockTextEmotionAdapter

class TextEmotionService:
    """Orchestration service for Text Emotion Recognition."""

    def __init__(self, adapter: Optional[BaseTextEmotionAdapter] = None) -> None:
        if adapter is not None:
            self._adapter = adapter
        elif settings.USE_MOCK_EMOTION:
            self._adapter = MockTextEmotionAdapter()
        else:
            self._adapter = GoEmotionsAdapter()

    def set_adapter(self, adapter: BaseTextEmotionAdapter) -> None:
        """Allow dynamic adapter swapping for benchmarking."""
        self._adapter = adapter

    def analyze(self, text: str) -> TextEmotionResult:
        """Analyze text emotion across GoEmotions taxonomy."""
        if not text or not text.strip():
            raise ValueError("Input text is empty")

        return self._adapter.analyze(text=text.strip())

text_emotion_service = TextEmotionService()
