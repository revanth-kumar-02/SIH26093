from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

class SupportCategory(str, Enum):
    """Taxonomy of support pathways for human responder triage."""
    COUNSELLING_SUPPORT = "COUNSELLING_SUPPORT"
    LEGAL_AID = "LEGAL_AID"
    MEDICAL_ASSISTANCE = "MEDICAL_ASSISTANCE"
    SAFETY_ASSISTANCE = "SAFETY_ASSISTANCE"
    POLICE_ASSISTANCE = "POLICE_ASSISTANCE"
    EMERGENCY_SUPPORT = "EMERGENCY_SUPPORT"
    SOCIAL_SUPPORT = "SOCIAL_SUPPORT"

class RecommendationPriority(str, Enum):
    ROUTINE = "routine"
    IMPORTANT = "important"
    URGENT = "urgent"

class ReviewStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    MODIFIED = "modified"
    REJECTED = "rejected"

class SupportRecommendation(BaseModel):
    """Structured support recommendation for human responder review."""
    recommendation_id: str = Field(..., description="Unique recommendation UUID")
    session_id: str = Field(..., description="Session identifier")
    category: SupportCategory = Field(..., description="Support taxonomy category")
    recommended: bool = Field(default=True, description="Whether this pathway is actively recommended")
    priority: RecommendationPriority = Field(..., description="Triage priority: routine, important, urgent")
    reason: str = Field(..., description="Evidence-grounded rationale for this recommendation")
    supporting_indicators: List[str] = Field(default_factory=list, description="Associated indicator labels from assessment")
    evidence_sources: List[str] = Field(default_factory=list, description="Origins of evidence: 'text', 'speech', 'multimodal'")
    responder_action: str = Field(..., description="Actionable guideline proposed for human responder")
    requires_human_review: bool = Field(default=True, description="Mandatory flag: AI suggestions require human approval")
    status: ReviewStatus = Field(default=ReviewStatus.PENDING_REVIEW, description="Review lifecycle status")
    responder_decision: Optional[str] = Field(default=None, description="Human decision ('accepted', 'modified', 'rejected')")
    responder_note: Optional[str] = Field(default=None, description="Responder commentary or adjustment rationale")
    reviewed_at: Optional[str] = Field(default=None, description="ISO timestamp of responder review")
    created_at: str = Field(..., description="ISO timestamp of recommendation generation")

class SupportRecommendationResult(BaseModel):
    """Aggregated support pathway suggestions with safety flags."""
    session_id: str = Field(..., description="Session identifier")
    recommendations: List[SupportRecommendation] = Field(default_factory=list, description="List of generated support recommendations")
    immediate_safety_attention: bool = Field(default=False, description="Flag indicating imminent danger or acute safety concern")
    uncertainties: List[str] = Field(default_factory=list, description="Uncertainties inherited from assessment layer")
    responder_review_required: bool = Field(default=True, description="Human oversight required flag")
    created_at: str = Field(..., description="Generation ISO timestamp")
    audit_metadata: Dict[str, Any] = Field(default_factory=dict, description="Audit tracking and diagnostic metadata")

class RecommendationReviewRequest(BaseModel):
    """Payload submitted by a human responder during review."""
    decision: Literal["accepted", "modified", "rejected"] = Field(..., description="Responder verdict")
    responder_note: Optional[str] = Field(default=None, description="Optional commentary or reasoning")
    modified_priority: Optional[RecommendationPriority] = Field(default=None, description="Adjusted priority if modified")
    modified_action: Optional[str] = Field(default=None, description="Adjusted action if modified")

class RecommendationReviewResponse(BaseModel):
    """Response returned upon successful responder review."""
    recommendation: SupportRecommendation
    status: str = "reviewed"
    timestamp: str
