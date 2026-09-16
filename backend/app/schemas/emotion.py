from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from app.schemas.stress import StressDetectionResult, StressSignal

class SpeechEmotionResult(BaseModel):
    """Structured Speech Emotion Recognition output."""
    emotion: str = Field(..., description="Highest probability emotion label (e.g. 'calm', 'fearful')")
    probabilities: Dict[str, float] = Field(..., description="Normalized probabilities across 7 Wav2Vec2 classes")
    model_version: Optional[str] = Field(default="Dpngtm/wav2vec2-emotion-recognition", description="Underlying model identifier")
    duration_ms: Optional[float] = Field(default=None, description="Inference latency in milliseconds")
    device: Optional[str] = Field(default=None, description="Hardware device used ('cuda' or 'cpu')")

class EmotionScore(BaseModel):
    """Individual emotion score in GoEmotions taxonomy."""
    label: str
    score: float

class TextEmotionResult(BaseModel):
    """Structured Text Emotion Recognition output across 28 GoEmotions taxonomy classes."""
    top_emotion: str = Field(..., description="Highest scoring emotion label")
    emotions: List[EmotionScore] = Field(..., description="Distribution across GoEmotions classes sorted by score")
    model_version: Optional[str] = Field(default="SamLowe/roberta-base-go_emotions", description="Underlying model identifier")
    duration_ms: Optional[float] = Field(default=None, description="Inference latency in milliseconds")
    device: Optional[str] = Field(default=None, description="Hardware device used ('cuda' or 'cpu')")

class EmotionSignal(BaseModel):
    """Application-level emotion indicator separating model specifics from internal assessment fusion."""
    signal_id: str = Field(..., description="Unique signal UUID")
    session_id: str = Field(..., description="Session identifier")
    source: str = Field(..., description="Signal source: 'speech' or 'text'")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    speech_emotion: Optional[SpeechEmotionResult] = Field(default=None, description="Speech emotion payload if source == 'speech'")
    text_emotion: Optional[TextEmotionResult] = Field(default=None, description="Text emotion payload if source == 'text'")
    stress: Optional[StressDetectionResult] = Field(default=None, description="Optional associated stress detection payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic/lifecycle metadata (e.g. latency, memory)")

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text to analyze")

class MultimodalSessionState(BaseModel):
    """Structured session-level aggregation of all multimodal signals (ASR, Speech Emotion, Text Emotion, Stress)."""
    session_id: str
    language: str
    status: str
    created_at: str
    speech_emotion_signals: List[EmotionSignal] = Field(default_factory=list, description="Historical speech emotion signals")
    text_emotion_signals: List[EmotionSignal] = Field(default_factory=list, description="Historical text emotion signals")
    stress_signals: List[StressSignal] = Field(default_factory=list, description="Historical stress signals from typed or transcribed text")
    transcripts: List[Dict[str, Any]] = Field(default_factory=list, description="Transcriptions generated from voice interactions")
    total_signals: int = Field(default=0, description="Total count of recorded multimodal signals")
