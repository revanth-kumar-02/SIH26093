from abc import ABC, abstractmethod
from app.services.llm.schemas import MultimodalAssessmentInput, TraumaAssessment

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
