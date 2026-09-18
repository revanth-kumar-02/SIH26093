from datetime import datetime, timezone
from typing import List, Optional
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
    CaseAssignRequest,
    CaseStatusUpdateRequest,
    RecommendationReviewRequest
)
from app.core.auth import require_roles

router = APIRouter(prefix="/responder", tags=["Admin & Responder Operations"])

VALID_CASE_TRANSITIONS = {
    CaseStatus.NEW: [CaseStatus.IN_REVIEW, CaseStatus.CLOSED],
    CaseStatus.IN_REVIEW: [CaseStatus.AWAITING_RESPONDER_ACTION, CaseStatus.CLOSED],
    CaseStatus.AWAITING_RESPONDER_ACTION: [CaseStatus.ACTION_RECORDED, CaseStatus.CLOSED],
    CaseStatus.ACTION_RECORDED: [CaseStatus.CLOSED, CaseStatus.IN_REVIEW],
    CaseStatus.CLOSED: [CaseStatus.IN_REVIEW]
}

@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    case_status: Optional[CaseStatus] = Query(None, description="Filter by case status"),
    risk_category: Optional[str] = Query(None, description="Filter by risk category (LOW, MODERATE, HIGH, CRITICAL)"),
    assigned_to_me: bool = Query(False, description="Filter cases assigned to current administrator"),
    search: Optional[str] = Query(None, description="Search by safe external case reference only"),
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """List triage cases with filters, pagination, and latest risk summaries (ADMIN only)."""
    query = select(Case).options(
        selectinload(Case.assigned_responder),
        selectinload(Case.svi_results)
    )

    if assigned_to_me:
        query = query.where(Case.assigned_responder_id == current_admin.id)

    if case_status:
        query = query.where(Case.status == case_status)

    if search:
        clean_search = search.strip().upper()
        query = query.where(Case.external_case_reference.ilike(f"%{clean_search}%"))

    count_stmt = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0

    query = query.order_by(desc(Case.updated_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    cases = result.scalars().all()

    items = []
    for c in cases:
        latest_svi = sorted(c.svi_results, key=lambda s: s.created_at, reverse=True)[0] if c.svi_results else None
        
        if risk_category and (not latest_svi or latest_svi.risk_category.upper() != risk_category.upper()):
            continue

        items.append(CaseListItem(
            id=c.id,
            external_case_reference=c.external_case_reference,
            status=c.status,
            language=c.language,
            consent_status=c.consent_status,
            assigned_responder_id=c.assigned_responder_id,
            assigned_responder_name=c.assigned_responder.display_name if c.assigned_responder else None,
            created_at=c.created_at,
            updated_at=c.updated_at,
            latest_svi_score=latest_svi.score if latest_svi else None,
            latest_risk_category=latest_svi.risk_category if latest_svi else None,
            immediate_safety_attention=latest_svi.immediate_safety_attention if latest_svi else False,
            urgent_human_review=latest_svi.urgent_human_review if latest_svi else False
        ))

    return CaseListResponse(
        total=total_count,
        page=page,
        page_size=page_size,
        items=items
    )

@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
async def get_case_detail(
    case_id: str,
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve comprehensive structured case details, SVI, assessment, and recommendations (ADMIN only)."""
    stmt = (
        select(Case)
        .where(Case.id == case_id)
        .options(
            selectinload(Case.assigned_responder),
            selectinload(Case.conversations).selectinload(Conversation.messages),
            selectinload(Case.assessments),
            selectinload(Case.svi_results),
            selectinload(Case.recommendations),
            selectinload(Case.audit_events)
        )
    )
    result = await db.execute(stmt)
    c = result.scalars().first()

    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": f"Case with ID '{case_id}' not found."}}
        )

    conv_summary = None
    if c.conversations:
        latest_conv = sorted(c.conversations, key=lambda cv: cv.started_at, reverse=True)[0]
        sorted_messages = sorted(latest_conv.messages, key=lambda m: m.timestamp)
        conv_summary = ConversationSummary(
            session_id=latest_conv.session_id or str(latest_conv.id),
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

@router.post("/cases/{case_id}/assign")
async def assign_case(
    case_id: str,
    payload: CaseAssignRequest,
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Assign case to an administrator/staff member (ADMIN only)."""
    stmt = select(Case).where(Case.id == case_id)
    case_res = await db.execute(stmt)
    case = case_res.scalars().first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found."}}
        )

    resp_stmt = select(Responder).where(Responder.id == payload.responder_id)
    resp_res = await db.execute(resp_stmt)
    target_user = resp_res.scalars().first()

    if not target_user or not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_RESPONDER", "message": "Target user not found or inactive."}}
        )

    if case.assigned_responder_id == target_user.id:
        return {
            "success": True,
            "message": f"Case {case.external_case_reference} is already assigned to {target_user.display_name}.",
            "case_id": case.id,
            "assigned_responder_id": target_user.id,
            "status": case.status.value
        }

    prev_responder_id = case.assigned_responder_id
    case.assigned_responder_id = target_user.id
    if case.status == CaseStatus.NEW:
        case.status = CaseStatus.IN_REVIEW
    case.updated_at = datetime.now(timezone.utc)

    audit = AuditEvent(
        case_id=case.id,
        actor_id=current_admin.id,
        actor_type=current_admin.role.value,
        event_type="CASE_ASSIGNED",
        entity_type="CASE",
        entity_id=case.id,
        event_metadata={
            "previous_responder_id": prev_responder_id,
            "assigned_to_id": target_user.id,
            "assigned_to_name": target_user.display_name
        }
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "message": f"Case {case.external_case_reference} assigned to {target_user.display_name}.",
        "case_id": case.id,
        "assigned_responder_id": target_user.id,
        "status": case.status.value
    }

@router.post("/cases/{case_id}/status")
async def update_case_status(
    case_id: str,
    payload: CaseStatusUpdateRequest,
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Update case lifecycle status with strict transition validation (ADMIN only)."""
    stmt = select(Case).where(Case.id == case_id)
    case_res = await db.execute(stmt)
    case = case_res.scalars().first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found."}}
        )

    if case.status == payload.status:
        return {
            "success": True,
            "case_id": case.id,
            "previous_status": case.status.value,
            "new_status": payload.status.value
        }

    allowed_transitions = VALID_CASE_TRANSITIONS.get(case.status, [])
    if payload.status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_STATUS_TRANSITION", "message": f"Cannot transition case from {case.status.value} to {payload.status.value}."}}
        )

    prev_status = case.status
    case.status = payload.status
    case.updated_at = datetime.now(timezone.utc)

    audit = AuditEvent(
        case_id=case.id,
        actor_id=current_admin.id,
        actor_type=current_admin.role.value,
        event_type="CASE_STATUS_CHANGED",
        entity_type="CASE",
        entity_id=case.id,
        event_metadata={
            "previous_status": prev_status.value,
            "new_status": payload.status.value
        }
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "case_id": case.id,
        "previous_status": prev_status.value,
        "new_status": payload.status.value
    }

@router.post("/cases/{case_id}/recommendations/{rec_id}/review")
async def review_recommendation(
    case_id: str,
    rec_id: str,
    body: RecommendationReviewRequest,
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Record human administrative decision on an AI recommendation (ACCEPT, MODIFY, REJECT) with idempotency."""
    case_stmt = select(Case).where(Case.id == case_id)
    case_res = await db.execute(case_stmt)
    case = case_res.scalars().first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found."}}
        )

    valid_decisions = ["ACCEPT", "MODIFY", "REJECT"]
    decision = body.decision.upper()
    if decision not in valid_decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_DECISION", "message": f"Decision must be one of {valid_decisions}."}}
        )

    stmt = select(RecommendationModel).where(
        RecommendationModel.id == rec_id,
        RecommendationModel.case_id == case_id
    )
    rec_res = await db.execute(stmt)
    rec = rec_res.scalars().first()

    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RECOMMENDATION_NOT_FOUND", "message": "Recommendation not found for this case."}}
        )

    if (rec.status == decision and
        rec.responder_note == body.responder_note and
        (decision != "MODIFY" or rec.responder_action == body.modified_action)):
        return {
            "success": True,
            "recommendation_id": rec.id,
            "decision": decision,
            "status": rec.status,
            "responder_action": rec.responder_action,
            "reviewed_by": rec.reviewed_by,
            "reviewed_at": rec.reviewed_at.isoformat() if rec.reviewed_at else None
        }

    original_action = rec.responder_action
    
    rec.status = decision
    rec.responder_decision = decision
    rec.responder_note = body.responder_note
    rec.reviewed_at = datetime.now(timezone.utc)
    rec.reviewed_by = current_admin.display_name

    if decision == "MODIFY" and body.modified_action:
        rec.responder_action = body.modified_action

    if case.status == CaseStatus.IN_REVIEW:
        case.status = CaseStatus.AWAITING_RESPONDER_ACTION

    audit = AuditEvent(
        case_id=case_id,
        actor_id=current_admin.id,
        actor_type=current_admin.role.value,
        event_type=f"RECOMMENDATION_{decision}",
        entity_type="RECOMMENDATION",
        entity_id=rec.id,
        event_metadata={
            "category": rec.category,
            "original_action": original_action,
            "modified_action": body.modified_action if decision == "MODIFY" else None,
            "responder_note": body.responder_note,
            "reviewer_name": current_admin.display_name
        }
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "recommendation_id": rec.id,
        "decision": decision,
        "status": rec.status,
        "responder_action": rec.responder_action,
        "reviewed_by": rec.reviewed_by,
        "reviewed_at": rec.reviewed_at.isoformat()
    }

@router.get("/cases/{case_id}/audit", response_model=List[AuditEventRead])
async def get_case_audit_trail(
    case_id: str,
    current_admin: Responder = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve complete append-only audit trail for a case (ADMIN only)."""
    case_stmt = select(Case).where(Case.id == case_id)
    case_res = await db.execute(case_stmt)
    case = case_res.scalars().first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found."}}
        )

    stmt = (
        select(AuditEvent)
        .where(AuditEvent.case_id == case_id)
        .order_by(desc(AuditEvent.created_at))
    )
    res = await db.execute(stmt)
    events = res.scalars().all()

    return [
        AuditEventRead(
            id=e.id,
            event_type=e.event_type,
            actor_id=e.actor_id,
            actor_type=e.actor_type,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            event_metadata=e.event_metadata,
            created_at=e.created_at
        ) for e in events
    ]
