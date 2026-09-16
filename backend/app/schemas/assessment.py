from pydantic import BaseModel, Field
from typing import Optional, List

class AssessmentResult(BaseModel):
    risk_level: str = "not_available"
    svi: Optional[float] = None
    indicators: List[str] = Field(default_factory=list)

class AssessmentResponse(BaseModel):
    session_id: str
    status: str = "pending_review"
    assessment: AssessmentResult
