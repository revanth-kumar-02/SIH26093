from abc import ABC, abstractmethod
from typing import List, Optional
from app.services.llm.schemas import MultimodalAssessmentInput, TraumaAssessment, ConversationTurn

class BaseLLMAssessmentAdapter(ABC):
    """Abstract interface for LLM-based multimodal trauma assessment."""

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if model weights are loaded in memory."""
        pass

    @abstractmethod
    def warmup(self) -> None:
        """Preload model weights into memory."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload model to free system resources."""
        pass

    @abstractmethod
    def assess(self, input_data: MultimodalAssessmentInput) -> TraumaAssessment:
        """Perform trauma-informed evidence assessment on multimodal signals."""
        pass

    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        conversation_history: List[ConversationTurn],
        assessment: Optional[TraumaAssessment],
        language: str = "en",
    ) -> str:
        """Generate an empathetic, trauma-informed victim-facing conversational response.

        This is SEPARATE from the internal assessment JSON.
        The response is natural, concise, context-aware, and never claims diagnosis,
        certainty of danger, or autonomous emergency dispatch.
        """
        pass
