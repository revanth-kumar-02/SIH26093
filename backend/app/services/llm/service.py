import logging
from typing import Optional
from app.services.llm.base import BaseLLMAssessmentAdapter
from app.services.llm.gemma import GemmaAdapter, MockGemmaAdapter
from app.services.llm.schemas import MultimodalAssessmentInput, TraumaAssessment
from app.core.config import settings

logger = logging.getLogger(__name__)

class GemmaService:
    """Service abstraction managing Gemma-3n multimodal trauma-informed assessment.
    
    Ensures lifecycle cleanliness, prevents duplicate instances, supports offline mock fallbacks,
    and isolates LLM internals from client-facing application layers.
    """

    def __init__(self, adapter: Optional[BaseLLMAssessmentAdapter] = None) -> None:
        if adapter is not None:
            self._adapter = adapter
        elif settings.USE_MOCK_GEMMA or not settings.HF_TOKEN:
            logger.info("Initializing GemmaService with MockGemmaAdapter (offline/unauthenticated)")
            self._adapter = MockGemmaAdapter(device=settings.GEMMA_DEVICE)
        else:
            logger.info(f"Initializing GemmaService with GemmaAdapter ({settings.GEMMA_MODEL_ID})")
            self._adapter = GemmaAdapter(
                model_id=settings.GEMMA_MODEL_ID,
                device=settings.GEMMA_DEVICE
            )

    def set_adapter(self, adapter: BaseLLMAssessmentAdapter) -> None:
        """Allow dynamic adapter swapping for tests and evaluation."""
        self._adapter = adapter

    def is_loaded(self) -> bool:
        return self._adapter.is_loaded()

    def warmup(self) -> None:
        self._adapter.warmup()

    def unload(self) -> None:
        self._adapter.unload()

    def assess(self, input_data: MultimodalAssessmentInput) -> TraumaAssessment:
        """Execute trauma-informed evidence assessment on multimodal signals.
        
        Strict Guardrails:
        - NEVER diagnoses mental illness or psychiatric conditions.
        - Produces evidence-grounded assessment aid strictly for trained human responders.
        - Does NOT calculate SVI or auto-trigger emergency actions.
        """
        return self._adapter.assess(input_data)

gemma_service = GemmaService()
