import logging
from typing import Optional
from app.services.stress.base import BaseStressAdapter
from app.services.stress.adapter import MentalBertDreadditAdapter, MockStressAdapter
from app.schemas.stress import StressDetectionResult
from app.core.config import settings

logger = logging.getLogger(__name__)

class StressDetectionService:
    """Service abstraction for Dreaddit-trained stress detection."""

    def __init__(self, adapter: Optional[BaseStressAdapter] = None) -> None:
        if adapter is not None:
            self._adapter = adapter
        elif settings.USE_MOCK_STRESS:
            logger.info("Initializing StressDetectionService with MockStressAdapter")
            self._adapter = MockStressAdapter(device=settings.STRESS_DEVICE)
        else:
            logger.info(f"Initializing StressDetectionService with MentalBertDreadditAdapter ({settings.STRESS_MODEL_NAME})")
            self._adapter = MentalBertDreadditAdapter(
                model_name=settings.STRESS_MODEL_NAME,
                device=settings.STRESS_DEVICE
            )

    def is_loaded(self) -> bool:
        return self._adapter.is_loaded()

    def warmup(self) -> None:
        self._adapter.warmup()

    def unload(self) -> None:
        self._adapter.unload()

    def analyze(self, text: str) -> StressDetectionResult:
        """Analyze text for stress indicators.
        
        Note: Stress detection is strictly an internal signal indicator.
        It is NOT a medical diagnosis, depression diagnosis, or emergency trigger.
        """
        return self._adapter.analyze(text)

stress_detection_service = StressDetectionService()
