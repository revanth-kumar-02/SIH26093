from typing import Optional
from app.core.config import settings
from app.services.asr.base import BaseASRAdapter
from app.services.asr.indic_conformer import IndicConformerAdapter, MockIndicConformerAdapter

class ASRService:
    """Speech-to-Text orchestration service powered by IndicConformer-600M-Multi.
    
    Manages audio constraints, temporary audio lifecycles, and model adapter delegation.
    """

    def __init__(self, adapter: Optional[BaseASRAdapter] = None) -> None:
        if adapter is not None:
            self._adapter = adapter
        elif settings.USE_MOCK_ASR:
            self._adapter = MockIndicConformerAdapter(default_decoder=settings.ASR_DECODER)
        else:
            self._adapter = IndicConformerAdapter()

    def set_adapter(self, adapter: BaseASRAdapter) -> None:
        """Allow dynamic swapping of ASR model adapters for benchmarking."""
        self._adapter = adapter

    def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        decoder: Optional[str] = None
    ) -> str:
        """Process and transcribe audio bytes, enforcing privacy safeguards."""
        if not audio_bytes:
            raise ValueError("Audio content is empty.")

        if len(audio_bytes) > settings.MAX_AUDIO_BYTES:
            raise ValueError(f"Audio exceeds maximum allowed size of {settings.MAX_AUDIO_BYTES // (1024 * 1024)} MB.")

        try:
            return self._adapter.transcribe(
                audio_bytes=audio_bytes,
                language=language,
                decoder=decoder
            )
        finally:
            del audio_bytes

asr_service = ASRService()