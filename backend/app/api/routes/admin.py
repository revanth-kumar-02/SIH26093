from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.responder import Responder, UserRole
from app.db.models.case import Case, CaseStatus
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.assessment import AssessmentModel
from app.db.models.svi import SVIResultModel
from app.db.models.recommendation import RecommendationModel
from app.db.models.audit import AuditEvent

from app.schemas.case import (
    CaseListItem,
    CaseListResponse,
    CaseDetailResponse,
    ConversationSummary,
    MessageItem,
    SVIResultSummary,
    RecommendationItem,
    AuditEventRead,
    AssignedResponderInfo,
    CaseStatusUpdateRequest,
    RecommendationReviewRequest,
    DashboardAnalyticsResponse,
    AdminAuditItem
)
from app.core.auth import require_roles

router = APIRouter(prefix="/admin", tags=["Admin Web Operations"])

VALID_CASE_TRANSITIONS = {
    CaseStatus.NEW: [CaseStatus.IN_REVIEW, CaseStatus.CLOSED],
    CaseStatus.IN_REVIEW: [CaseStatus.AWAITING_RESPONDER_ACTION, CaseStatus.CLOSED],
    CaseStatus.AWAITING_RESPONDER_ACTION: [CaseStatus.ACTION_RECORDED, CaseStatus.CLOSED],
    CaseStatus.ACTION_RECORDED: [CaseStatus.CLOSED, CaseStatus.IN_REVIEW],
    CaseStatus.CLOSED: [CaseStatus.IN_REVIEW]
}

@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
async def get_admin_dashboard(
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve structured aggregates for the Admin Web Dashboard from live database records."""
    # Active cases
    active_stmt = select(func.count(Case.id)).where(Case.status != CaseStatus.CLOSED)
    active_res = await db.execute(active_stmt)
    active_cases = active_res.scalar() or 0

    # Load all non-closed cases with SVI to calculate risk distribution and urgent flags
    cases_stmt = (
        select(Case)
        .options(selectinload(Case.svi_results), selectinload(Case.assigned_responder))
        .where(Case.status != CaseStatus.CLOSED)
    )
    cases_res = await db.execute(cases_stmt)
    active_case_objs = cases_res.scalars().all()

    risk_dist = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    urgent_review_count = 0
    high_risk_count = 0
    requires_attention_cases: List[CaseListItem] = []
    recent_cases: List[CaseListItem] = []

    for c in active_case_objs:
        latest_svi = c.svi_results[-1] if c.svi_results else None
        risk_cat = latest_svi.risk_category if latest_svi else "LOW"
        if risk_cat in risk_dist:
            risk_dist[risk_cat] += 1
        else:
            risk_dist["LOW"] += 1

        is_urgent = False
        is_immediate = False
        if latest_svi:
            if latest_svi.urgent_human_review or latest_svi.immediate_safety_attention:
                is_urgent = True
                urgent_review_count += 1
            if latest_svi.immediate_safety_attention:
                is_immediate = True
            if latest_svi.risk_category in ("HIGH", "CRITICAL"):
                high_risk_count += 1

        item = CaseListItem(
            id=c.id,
            external_case_reference=c.external_case_reference,
            status=c.status,
            language=c.language,
            consent_status=c.consent_status,
            created_at=c.created_at,
            updated_at=c.updated_at,
            assigned_responder=AssignedResponderInfo(
                id=c.assigned_responder.id,
                display_name=c.assigned_responder.display_name,
                email=c.assigned_responder.email,
                role=c.assigned_responder.role.value
            ) if c.assigned_responder else None,
            latest_svi_score=latest_svi.score if latest_svi else None,
            latest_risk_category=latest_svi.risk_category if latest_svi else None,
            immediate_safety_attention=is_immediate,
            urgent_human_review=is_urgent
        )

        if is_urgent or is_immediate:
            requires_attention_cases.append(item)
        recent_cases.append(item)

    # Sort recent cases by updated_at descending
    recent_cases.sort(key=lambda x: x.updated_at, reverse=True)
    requires_attention_cases.sort(key=lambda x: x.updated_at, reverse=True)

    # Pending reviews count
    pending_stmt = (
        select(func.count(RecommendationModel.id))
        .where(
            RecommendationModel.status == "PENDING",
            RecommendationModel.requires_human_review == True
        )
    )
    pending_res = await db.execute(pending_stmt)
    pending_reviews = pending_res.scalar() or 0

    return DashboardAnalyticsResponse(
        active_cases=active_cases,
        urgent_review=urgent_review_count,
        high_risk=high_risk_count,
        pending_reviews=pending_reviews,
        risk_distribution=risk_dist,
        requires_attention_cases=requires_attention_cases[:10],
        recent_cases=recent_cases[:10]
    )

@router.get("/cases", response_model=CaseListResponse)
async def list_admin_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    case_status: Optional[CaseStatus] = Query(None, description="Filter by case status"),
    risk_category: Optional[str] = Query(None, description="Filter by risk category (LOW, MODERATE, HIGH, CRITICAL)"),
    search: Optional[str] = Query(None, description="Search by safe external case reference"),
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """List cases with filtering, search, and pagination for Admin review (ADMIN only)."""
    query = select(Case).options(
        selectinload(Case.assigned_responder),
        selectinload(Case.svi_results)
    )

    if case_status:
        query = query.where(Case.status == case_status)

    if search:
        clean_search = search.strip().upper()
        query = query.where(Case.external_case_reference.ilike(f"%{clean_search}%"))

    # Count total matching query
    count_query = select(func.count(Case.id))
    if case_status:
        count_query = count_query.where(Case.status == case_status)
    if search:
        clean_search = search.strip().upper()
        count_query = count_query.where(Case.external_case_reference.ilike(f"%{clean_search}%"))
    total_count = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(desc(Case.updated_at))
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    cases = result.scalars().all()

    items: List[CaseListItem] = []
    for c in cases:
        latest_svi = c.svi_results[-1] if c.svi_results else None

        if risk_category and (not latest_svi or latest_svi.risk_category != risk_category.upper()):
            continue

        item = CaseListItem(
            id=c.id,
            external_case_reference=c.external_case_reference,
            status=c.status,
            language=c.language,
            consent_status=c.consent_status,
            created_at=c.created_at,
            updated_at=c.updated_at,
            assigned_responder=AssignedResponderInfo(
                id=c.assigned_responder.id,
                display_name=c.assigned_responder.display_name,
                email=c.assigned_responder.email,
                role=c.assigned_responder.role.value
            ) if c.assigned_responder else None,
            latest_svi_score=latest_svi.score if latest_svi else None,
            latest_risk_category=latest_svi.risk_category if latest_svi else None,
            immediate_safety_attention=latest_svi.immediate_safety_attention if latest_svi else False,
            urgent_human_review=latest_svi.urgent_human_review if latest_svi else False
        )
        items.append(item)

    return CaseListResponse(
        total=total_count,
        page=page,
        page_size=page_size,
        items=items
    )

@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
async def get_admin_case_detail(
    case_id: str,
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve full clinical & operational details of a specific case (ADMIN only)."""
    stmt = (
        select(Case)
        .options(
            selectinload(Case.assigned_responder),
            selectinload(Case.conversations).selectinload(Conversation.messages),
            selectinload(Case.assessments),
            selectinload(Case.svi_results),
            selectinload(Case.recommendations),
            selectinload(Case.audit_events)
        )
        .where(Case.id == case_id)
    )
    result = await db.execute(stmt)
    c = result.scalars().first()

    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": f"Case with ID '{case_id}' was not found."}}
        )

    conv_summary = None
    if c.conversations:
        latest_conv = sorted(c.conversations, key=lambda cv: cv.started_at, reverse=True)[0]
        sorted_messages = sorted(latest_conv.messages, key=lambda m: m.timestamp)
        conv_summary = ConversationSummary(
            session_id=latest_conv.session_id,
            input_language=latest_conv.input_language,
            started_at=latest_conv.started_at,
            ended_at=latest_conv.ended_at,
            message_count=len(sorted_messages),
            messages=[
                MessageItem(
                    id=m.id,
                    sender_type=m.sender_type.value,
                    input_source=m.input_source.value,
                    content=m.content,
                    timestamp=m.timestamp
                ) for m in sorted_messages
            ]
        )

    latest_assessment = sorted(c.assessments, key=lambda a: a.created_at, reverse=True)[0] if c.assessments else None
    latest_svi = sorted(c.svi_results, key=lambda s: s.created_at, reverse=True)[0] if c.svi_results else None
    svi_summary = None
    if latest_svi:
        svi_summary = SVIResultSummary(
            svi_version=latest_svi.svi_version,
            score=latest_svi.score,
            risk_category=latest_svi.risk_category,
            factor_contributions=latest_svi.factor_contributions,
            key_drivers=latest_svi.key_drivers,
            uncertainties=latest_svi.uncertainties,
            immediate_safety_attention=latest_svi.immediate_safety_attention,
            urgent_human_review=latest_svi.urgent_human_review,
            created_at=latest_svi.created_at
        )

    recommendations = [
        RecommendationItem(
            id=r.id,
            category=r.category,
            priority=r.priority,
            reason=r.reason,
            supporting_indicators=r.supporting_indicators,
            evidence_sources=r.evidence_sources,
            responder_action=r.responder_action,
            requires_human_review=r.requires_human_review,
            status=r.status,
            responder_decision=r.responder_decision,
            responder_note=r.responder_note,
            created_at=r.created_at,
            reviewed_at=r.reviewed_at,
            reviewed_by=r.reviewed_by
        ) for r in sorted(c.recommendations, key=lambda r: r.created_at)
    ]

    audit_history = [
        AuditEventRead(
            id=e.id,
            event_type=e.event_type,
            actor_id=e.actor_id,
            actor_type=e.actor_type,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            event_metadata=e.event_metadata,
            created_at=e.created_at
        ) for e in sorted(c.audit_events, key=lambda e: e.created_at)
    ]

    return CaseDetailResponse(
        id=c.id,
        external_case_reference=c.external_case_reference,
        status=c.status,
        language=c.language,
        consent_status=c.consent_status,
        assigned_responder=AssignedResponderInfo(
            id=c.assigned_responder.id,
            display_name=c.assigned_responder.display_name,
            email=c.assigned_responder.email,
            role=c.assigned_responder.role.value
        ) if c.assigned_responder else None,
        created_at=c.created_at,
        updated_at=c.updated_at,
        conversation_summary=conv_summary,
        ai_assessment=latest_assessment.assessment_payload if latest_assessment else None,
        svi_result=svi_summary,
        safety_flags={
            "immediate_safety_attention": latest_svi.immediate_safety_attention if latest_svi else False,
            "urgent_human_review": latest_svi.urgent_human_review if latest_svi else False
        },
        recommendations=recommendations,
        audit_history=audit_history
    )


@router.post("/cases/{case_id}/status")
async def update_admin_case_status(
    case_id: str,
    body: CaseStatusUpdateRequest,
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Update case status following validated operational lifecycle (ADMIN only)."""
    stmt = select(Case).where(Case.id == case_id)
    res = await db.execute(stmt)
    case = res.scalars().first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found."}}
        )

    allowed_transitions = VALID_CASE_TRANSITIONS.get(case.status, [])
    if body.status != case.status and body.status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_STATUS_TRANSITION",
                    "message": f"Cannot transition from {case.status.value} to {body.status.value}."
                }
            }
        )

    old_status = case.status
    case.status = body.status
    case.updated_at = datetime.now(timezone.utc)

    audit = AuditEvent(
        case_id=case_id,
        actor_id=current_admin.id,
        actor_type=current_admin.role.value,
        event_type="CASE_STATUS_CHANGED",
        entity_type="CASE",
        entity_id=case_id,
        event_metadata={
            "old_status": old_status.value,
            "new_status": body.status.value,
            "admin_name": current_admin.display_name
        }
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "case_id": case.id,
        "previous_status": old_status.value,
        "new_status": case.status.value,
        "updated_at": case.updated_at.isoformat()
    }

@router.post("/recommendations/{recommendation_id}/review")
async def review_admin_recommendation(
    recommendation_id: str,
    body: RecommendationReviewRequest,
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Record human review decision (ACCEPT, MODIFY, REJECT) on an AI support recommendation (ADMIN only)."""
    rec_stmt = select(RecommendationModel).options(selectinload(RecommendationModel.case)).where(RecommendationModel.id == recommendation_id)
    rec_res = await db.execute(rec_stmt)
    rec = rec_res.scalars().first()

    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RECOMMENDATION_NOT_FOUND", "message": f"Recommendation with ID '{recommendation_id}' not found."}}
        )

    decision = body.decision.strip().upper()
    if decision not in ("ACCEPT", "MODIFY", "REJECT"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_DECISION", "message": "Decision must be ACCEPT, MODIFY, or REJECT."}}
        )

    original_action = rec.responder_action
    original_priority = rec.priority

    rec.status = decision
    rec.responder_decision = decision
    rec.responder_note = body.responder_note
    rec.reviewed_at = datetime.now(timezone.utc)
    rec.reviewed_by = current_admin.display_name

    if decision == "MODIFY":
        if body.modified_action:
            rec.responder_action = body.modified_action
        if body.modified_priority:
            rec.priority = body.modified_priority

    if rec.case and rec.case.status == CaseStatus.IN_REVIEW:
        rec.case.status = CaseStatus.AWAITING_RESPONDER_ACTION
        rec.case.updated_at = datetime.now(timezone.utc)

    audit = AuditEvent(
        case_id=rec.case_id,
        actor_id=current_admin.id,
        actor_type=current_admin.role.value,
        event_type=f"RECOMMENDATION_{decision}",
        entity_type="RECOMMENDATION",
        entity_id=rec.id,
        event_metadata={
            "category": rec.category,
            "original_action": original_action,
            "original_priority": original_priority,
            "modified_action": body.modified_action if decision == "MODIFY" else None,
            "modified_priority": body.modified_priority if decision == "MODIFY" else None,
            "responder_note": body.responder_note,
            "reviewer_name": current_admin.display_name
        }
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "recommendation_id": rec.id,
        "case_id": rec.case_id,
        "decision": decision,
        "status": rec.status,
        "priority": rec.priority,
        "responder_action": rec.responder_action,
        "reviewed_by": rec.reviewed_by,
        "reviewed_at": rec.reviewed_at.isoformat()
    }

@router.get("/audit", response_model=List[AdminAuditItem])
async def get_admin_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    case_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve system-wide audit records for administrator review without raw victim conversations."""
    stmt = (
        select(AuditEvent, Case.external_case_reference)
        .outerjoin(Case, AuditEvent.case_id == Case.id)
    )

    if case_id:
        stmt = stmt.where(AuditEvent.case_id == case_id)
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type.strip().upper())

    stmt = stmt.order_by(desc(AuditEvent.created_at))
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    res = await db.execute(stmt)
    rows = res.all()

    items: List[AdminAuditItem] = []
    for audit, case_ref in rows:
        # Sanitize details to ensure no raw victim conversation is exposed in audit view
        clean_metadata = {k: v for k, v in audit.event_metadata.items() if "raw_text" not in k and "transcript" not in k}
        items.append(
            AdminAuditItem(
                id=audit.id,
                timestamp=audit.created_at,
                actor=audit.actor_type,
                actor_id=audit.actor_id,
                actor_type=audit.actor_type,
                event=audit.event_type,
                entity=audit.entity_type,
                entity_id=audit.entity_id,
                case_reference=case_ref,
                case_id=audit.case_id,
                details=clean_metadata
            )
        )
    return items
