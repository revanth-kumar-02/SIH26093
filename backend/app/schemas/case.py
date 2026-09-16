from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.db.models.case import CaseStatus
from app.db.models.responder import UserRole

class CaseListItem(BaseModel):
    id: str
    external_case_reference: str
    status: CaseStatus
    language: str
    consent_status: str
    assigned_responder_id: Optional[str] = None
    assigned_responder_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    latest_svi_score: Optional[float] = None
    latest_risk_category: Optional[str] = None
    immediate_safety_attention: bool = False
    urgent_human_review: bool = False

    model_config = ConfigDict(from_attributes=True)

class CaseListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CaseListItem]

class MessageItem(BaseModel):
    id: str
    sender_type: str
    input_source: str
    content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationSummary(BaseModel):
    session_id: str
    input_language: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    message_count: int
    messages: List[MessageItem]

from typing import Union

class SVIResultSummary(BaseModel):
    svi_version: str
    score: float
    risk_category: str
    factor_contributions: Union[Dict[str, Any], List[Any]]
    key_drivers: List[str]
    uncertainties: List[str]
    immediate_safety_attention: bool
    urgent_human_review: bool
    created_at: datetime

class RecommendationItem(BaseModel):
    id: str
    category: str
    priority: str
    reason: str
    supporting_indicators: List[str]
    evidence_sources: List[str]
    responder_action: str
    requires_human_review: bool
    status: str
    responder_decision: Optional[str] = None
    responder_note: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AuditEventRead(BaseModel):
    id: str
    event_type: str
    actor_id: str
    actor_type: str
    entity_type: str
    entity_id: Optional[str] = None
    event_metadata: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AssignedResponderInfo(BaseModel):
    id: str
    display_name: str
    email: str
    role: str

class CaseDetailResponse(BaseModel):
    id: str
    external_case_reference: str
    status: CaseStatus
    language: str
    consent_status: str
    assigned_responder: Optional[AssignedResponderInfo] = None
    created_at: datetime
    updated_at: datetime
    conversation_summary: Optional[ConversationSummary] = None
    ai_assessment: Optional[Dict[str, Any]] = None
    svi_result: Optional[SVIResultSummary] = None
    safety_flags: Dict[str, bool]
    recommendations: List[RecommendationItem]
    audit_history: List[AuditEventRead]

class CaseAssignRequest(BaseModel):
    responder_id: str

class CaseStatusUpdateRequest(BaseModel):
    status: CaseStatus

class RecommendationReviewRequest(BaseModel):
    decision: str = Field(..., description="ACCEPT, MODIFY, or REJECT")
    modified_action: Optional[str] = Field(None, description="Updated action if modified")
    modified_priority: Optional[str] = Field(None, description="Updated priority if modified")
    responder_note: Optional[str] = Field(None, description="Justification or observation note")


class DashboardAnalyticsResponse(BaseModel):
    active_cases: int
    urgent_review: int
    high_risk: int
    pending_reviews: int
    risk_distribution: Dict[str, int]
    requires_attention_cases: List[CaseListItem] = []
    recent_cases: List[CaseListItem] = []

class AdminAuditItem(BaseModel):
    id: str
    timestamp: datetime
    actor: str
    actor_id: str
    actor_type: str
    event: str
    entity: str
    entity_id: Optional[str] = None
    case_reference: Optional[str] = None
    case_id: Optional[str] = None
    details: Dict[str, Any] = {}
