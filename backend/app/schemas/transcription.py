from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.emotion import SpeechEmotionResult
from app.schemas.stress import StressDetectionResult

class TranscriptionResponse(BaseModel):
    """Typed, versionable transcription response for IndicConformer-600M-Multi."""
    session_id: str
    text: str = Field(..., description="Transcribed speech text in the requested language")
    transcript: str = Field(..., description="Alias for text")
    language: str = Field(default="en", description="Language code used for transcription (e.g. 'ta', 'hi', 'en')")
    decoder: str = Field(default="ctc", description="Decoding strategy used ('ctc' or 'rnnt')")
    status: str = "completed"
    timestamp: Optional[str] = None
    speech_emotion: Optional[SpeechEmotionResult] = None
    stress: Optional[StressDetectionResult] = None
