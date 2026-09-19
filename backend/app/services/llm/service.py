import logging
from typing import Optional
from app.services.llm.base import BaseLLMAssessmentAdapter
from app.services.llm.gemma import GemmaAdapter, MockGemmaAdapter
from app.services.llm.schemas import MultimodalAssessmentInput, TraumaAssessment
from app.core.config import settings

logger = logging.getLogger(__name__)

class GemmaService:
    """Service abstraction managing Gemma multimodal trauma-informed assessment.
    
    Ensures lifecycle cleanliness, prevents duplicate instances,
    and isolates LLM internals from client-facing application layers.
    """

    def __init__(self, adapter: Optional[BaseLLMAssessmentAdapter] = None) -> None:
        if adapter is not None:
            self._adapter = adapter
        else:
            model_id = settings.HF_CHAT_MODEL or settings.GEMMA_MODEL_ID
            logger.info(f"[AI] Initializing GemmaService with remote GemmaAdapter ({model_id})")
            self._adapter = GemmaAdapter(
                model_id=model_id,
                token=settings.HF_TOKEN,
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

    def generate_response(
        self,
        user_message: str,
        conversation_history: list = None,
        assessment: Optional[TraumaAssessment] = None,
        language: str = "en",
        recent_assistant_openings: Optional[list] = None,
        regeneration_directive: Optional[str] = None,
    ) -> str:
        """Generate a trauma-informed, empathetic, victim-facing conversational response."""
        if conversation_history is None:
            conversation_history = []
        return self._adapter.generate_response(
            user_message=user_message,
            conversation_history=conversation_history,
            assessment=assessment,
            language=language,
            recent_assistant_openings=recent_assistant_openings,
            regeneration_directive=regeneration_directive,
        )

    def analyze_completed_conversation(
        self,
        conversation_turns: list,
        text_emotions: Optional[list] = None,
        stress_signals: Optional[list] = None,
        language: str = "en"
    ) -> dict:
        """Analyze full conversation context to extract grounded summary and indicators."""
        return self._adapter.analyze_completed_conversation(
            conversation_turns=conversation_turns,
            text_emotions=text_emotions,
            stress_signals=stress_signals,
            language=language
        )


gemma_service = GemmaService()

