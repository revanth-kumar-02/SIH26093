from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from app.schemas.emotion import SpeechEmotionResult, TextEmotionResult
from app.schemas.stress import StressDetectionResult

class ConversationTurn(BaseModel):
    """Contextual representation of prior conversation turns."""
    role: str = Field(..., description="'user' or 'assistant'")
    text: str = Field(..., description="Message text content")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp")

class MultimodalAssessmentInput(BaseModel):
    """Structured input container for Gemma-3n multimodal evidence reasoning.
    
    Preserves independent model signals without premature numerical collapse.
    """
    session_id: Optional[str] = Field(default=None, description="Active victim session ID")
    transcript: Optional[str] = Field(default=None, description="Current or latest ASR transcript / text message")
    conversation_context: List[ConversationTurn] = Field(default_factory=list, description="Recent conversation history")
    text_emotion: Optional[TextEmotionResult] = Field(default=None, description="GoEmotions 28-class TER output")
    speech_emotion: Optional[SpeechEmotionResult] = Field(default=None, description="Wav2Vec2 7-class SER output")
    stress: Optional[StressDetectionResult] = Field(default=None, description="Dreaddit MentalBERT stress result")
    speech_signals: Optional[Dict[str, Any]] = Field(default=None, description="Acoustic features / duration / SNR")
    language: Optional[str] = Field(default="en", description="Interaction language code ('en', 'ta', 'hi', etc.)")
    input_source: Optional[str] = Field(default="multimodal", description="Primary interaction source: 'voice', 'text', 'multimodal'")
    timestamp: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp")
    historical_memory: Optional[str] = Field(default=None, description="Controlled bounded context from prior sessions compiled by MemoryService")

class EvidenceItem(BaseModel):
    """Evidence snippet attributed to its specific input modality."""
    text: str = Field(..., description="Exact textual excerpt or acoustic indicator observed")
    source: str = Field(default="text", description="Ground-truth source origin of the evidence (e.g. text, speech, multimodal, text_emotion)")

class AssessmentIndicator(BaseModel):
    """Individual trauma-informed indicator with evidence grounding and confidence."""
    indicator: str = Field(..., description="Specific indicator label (e.g. 'fear', 'threats_of_violence', 'social_isolation')")
    category: Literal[
        "emotional_distress",
        "intimidation_coercion",
        "vulnerability",
        "immediate_safety",
        "communication_difficulty"
    ] = Field(..., description="High-level indicator category")
    status: Literal["detected", "not_detected", "uncertain"] = Field(..., description="Detection status based strictly on evidence")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence score")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Specific grounded evidence excerpts")
    reason: str = Field(..., description="Explanation of why the indicator was assigned this status")

class TraumaAssessment(BaseModel):
    """Evidence-based AI-assisted vulnerability and distress assessment.
    
    IMPORTANT: This assessment is an AI-generated decision aid for human responders.
    It does NOT constitute a clinical diagnosis, forensic validation, or final legal determination.
    """
    session_id: str = Field(..., description="Session identifier")
    indicators: List[AssessmentIndicator] = Field(default_factory=list, description="Structured indicators across all categories")
    key_observations: List[str] = Field(default_factory=list, description="Objective factual observations grounded in evidence")
    uncertainties: List[str] = Field(default_factory=list, description="Ambiguities, missing modalities, or conflicting signals")
    safety_concerns: List[str] = Field(default_factory=list, description="Potential safety-sensitive flags for responder prioritization")
    responder_review_points: List[str] = Field(default_factory=list, description="Actionable points requiring human responder validation")
    model_version: Optional[str] = Field(default="google/gemma-3n-E2B-it", description="LLM checkpoint identifier")
    duration_ms: Optional[float] = Field(default=None, description="Assessment inference latency in milliseconds")
    device: Optional[str] = Field(default=None, description="Hardware device ('cuda' or 'cpu')")
