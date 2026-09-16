from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.llm.schemas import TraumaAssessment, AssessmentIndicator
from app.schemas.emotion import SpeechEmotionResult, TextEmotionResult
from app.schemas.stress import StressDetectionResult

class RiskCategory(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SVIFactor(BaseModel):
    """Individual vulnerability factor contributing to the overall SVI score."""
    factor_id: str = Field(..., description="Unique factor key (e.g. 'threats_intimidation')")
    name: str = Field(..., description="Human-readable factor title")
    group: str = Field(..., description="Factor category group (A through F)")
    weight: float = Field(..., ge=0.0, description="Baseline theoretical weight from configuration")
    presence: float = Field(..., ge=0.0, le=1.0, description="Presence value derived from indicator detection status")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of the observed evidence (0.0 - 1.0)")
    evidence_strength: float = Field(..., ge=0.0, le=1.0, description="Strength factor based on corroborated evidence excerpts")
    contribution: float = Field(..., ge=0.0, description="Final numerical contribution to the raw SVI score")
    corroborated: bool = Field(default=False, description="True if corroborated across multiple input modalities")
    evidence_sources: List[str] = Field(default_factory=list, description="Modality sources: 'text', 'speech', 'multimodal'")

class SVIInput(BaseModel):
    """Input payload for Stress Vulnerability Index calculation.
    
    Consumes structured assessment evidence rather than raw conversational text.
    """
    session_id: str = Field(..., description="Session identifier")
    assessment: Optional[TraumaAssessment] = Field(default=None, description="Structured Phase 6 assessment")
    indicators: List[AssessmentIndicator] = Field(default_factory=list, description="Explicit indicators if assessment omitted")
    safety_concerns: List[str] = Field(default_factory=list, description="Immediate safety flags")
    observations: List[str] = Field(default_factory=list, description="Factual observations")
    uncertainties: List[str] = Field(default_factory=list, description="Missing modalities or ambiguous signals")
    stress: Optional[StressDetectionResult] = Field(default=None, description="Optional Dreaddit stress result")
    speech_emotion: Optional[SpeechEmotionResult] = Field(default=None, description="Optional Wav2Vec2 speech emotion result")
    text_emotion: Optional[TextEmotionResult] = Field(default=None, description="Optional GoEmotions text emotion result")
    language: Optional[str] = Field(default="en", description="Interaction language")

class SVIResult(BaseModel):
    """Deterministic, explainable Stress Vulnerability Index output for responder review."""
    svi_version: str = Field(default="v1.0", description="Configuration rubric version")
    session_id: str = Field(..., description="Session identifier")
    score: float = Field(..., ge=0.0, le=100.0, description="Normalized SVI score (0.0 to 100.0)")
    risk_category: RiskCategory = Field(..., description="Categorical risk triage tier (LOW, MODERATE, HIGH, CRITICAL)")
    factor_contributions: List[SVIFactor] = Field(default_factory=list, description="Breakdown of individual factor contributions")
    key_drivers: List[str] = Field(default_factory=list, description="Top contributing factors driving the score")
    uncertainties: List[str] = Field(default_factory=list, description="Explicit uncertainties and missing signals")
    immediate_safety_attention: bool = Field(default=False, description="Immediate physical danger or acute safety flag")
    urgent_human_review: bool = Field(default=False, description="Urgent responder attention required flag")
    requires_human_review: bool = Field(default=True, description="Mandatory flag: SVI is an advisory aid for human responders")
    calculation_timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    audit_metadata: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters and diagnostic telemetry")
