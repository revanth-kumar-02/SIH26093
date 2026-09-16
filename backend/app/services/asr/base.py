from abc import ABC, abstractmethod
from typing import Optional

class BaseASRAdapter(ABC):
    """Abstract interface for Speech-to-Text / ASR model adapters.
    
    Decouples the FastAPI application from specific ASR implementations.
    """

    @abstractmethod
    def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        decoder: Optional[str] = None
    ) -> str:
        """Transcribe raw audio bytes to text in the requested language.
        
        Args:
            audio_bytes: Raw audio binary content (WAV, MP3, AAC, FLAC, M4A, etc.)
            language: Language code ('ta', 'hi', 'te', 'kn', 'ml', 'en', etc.)
            decoder: Decoding strategy ('ctc' or 'rnnt')
                      
        Returns:
            Transcribed text string in the target language.
        """
        pass