from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.recommendation.schemas import SupportRecommendation

class VerifiedEmergencyResource(BaseModel):
    title: str = Field(..., description="Official name of emergency helpline")
    number: str = Field(..., description="Verified contact digits, e.g. 112 or 181")
    description: str = Field(..., description="Actionable description")

class PersonalizedSupportPlan(BaseModel):
    """Structured personalized support plan generated from completed conversation context and AI signals."""
    session_id: str = Field(..., description="Session identifier")
    what_we_heard: str = Field(..., description="Personalized 2-4 sentence factual summary of what the user described")
    how_you_are_doing: str = Field(..., description="Calm emotional reflection acknowledging their feelings without clinical diagnosis")
    primary_concerns: List[str] = Field(default_factory=list, description="Core concerns extracted from user narrative")
    emotional_indicators: List[str] = Field(default_factory=list, description="Emotions explicitly identified")
    immediate_safety_needed: bool = Field(default=False, description="Whether acute physical danger or self-harm is indicated")
    immediate_safety_message: Optional[str] = Field(default=None, description="Sensitive guidance message if immediate safety is needed")
    verified_emergency_resource: Optional[VerifiedEmergencyResource] = Field(default=None, description="Verified emergency contact if needed")
    recommendations: List[SupportRecommendation] = Field(default_factory=list, description="Grounded support recommendations")
    has_human_assignment: bool = Field(default=False, description="Whether a real responder is assigned in database")
    human_assignment_details: Optional[Dict[str, Any]] = Field(default=None, description="Real responder name/role if assigned")
    human_review_status: str = Field(default="Human review recommended", description="Status of human oversight")
    human_review_message: str = Field(
        default="Some of what you shared may require a trained responder to review before external action is considered.",
        description="Explanation of human review process"
    )
    user_choices: List[Dict[str, str]] = Field(default_factory=list, description="Available voluntary choices for user")
    uncertainties: List[str] = Field(default_factory=list, description="Missing or ambiguous information noted")
    created_at: str = Field(..., description="Generation ISO timestamp")
