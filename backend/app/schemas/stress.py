from pydantic import BaseModel, Field
from typing import Dict, Optional, Any

class StressDetectionResult(BaseModel):
    """Structured output from Dreaddit-trained stress detection classifier."""
    label: str = Field(..., description="Binary stress prediction: 'stressed' or 'not_stressed'")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence/probability score of the predicted label")
    probabilities: Dict[str, float] = Field(default_factory=dict, description="Normalized softmax probabilities for each class")
    model_version: Optional[str] = Field(default="jtvallente/mentalbert_dreaddit_best", description="Model checkpoint identifier")
    duration_ms: Optional[float] = Field(default=None, description="Inference latency in milliseconds")
    device: Optional[str] = Field(default=None, description="Hardware device used ('cuda' or 'cpu')")

class StressSignal(BaseModel):
    """Structured internal stress indicator for multimodal evidence aggregation."""
    signal_id: str = Field(..., description="Unique signal UUID")
    session_id: str = Field(..., description="Session identifier")
    source: str = Field(..., description="Signal origin: 'text' (typed message) or 'speech' (ASR transcript)")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    stress: StressDetectionResult = Field(..., description="Stress prediction result")
    model_version: Optional[str] = Field(default="jtvallente/mentalbert_dreaddit_best", description="Model version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic telemetry metadata (latency, device)")

class StressAnalysisRequest(BaseModel):
    """Input payload for dedicated stress analysis endpoint."""
    text: str = Field(..., min_length=1, description="Input text to analyze for stress indicators")

class StressAnalysisResponse(BaseModel):
    """API response payload for dedicated stress analysis endpoint."""
    session_id: str
    stress: StressDetectionResult
    status: str = "completed"
    timestamp: Optional[str] = None
