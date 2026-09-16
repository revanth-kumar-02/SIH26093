import uuid
from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.db.models.recommendation import RecommendationModel
from app.db.models.recommendation_review import RecommendationReview
from app.db.models.conversation import Conversation
from app.db.models.case import Case, CaseStatus
from app.db.models.audit import AuditEvent
from app.services.llm.schemas import TraumaAssessment, MultimodalAssessmentInput
from app.services.llm.service import gemma_service
from app.services.session_service import session_service
from app.services.recommendation.schemas import (
    SupportRecommendationResult,
    RecommendationReviewRequest,
    RecommendationReviewResponse,
    SupportRecommendation
)
from app.services.recommendation.service import recommendation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Support Recommendations"])

@router.post("/{session_id}/recommendations", response_model=SupportRecommendationResult)
async def generate_recommendations(
    session_id: str,
    assessment: Optional[TraumaAssessment] = Body(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Generate structured support pathway recommendations for human responder review and persist to DB.
    
    Consumes TraumaAssessment from Phase 6 or automatically performs assessment on accumulated session state.
    Strictly advisory: Requires human responder review; does NOT make automated external calls.
    """
    session = session_service.get_session(session_id)
    if not session:
        # Check database
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        res = await db.execute(stmt)
        if not res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        session_service._sessions[session_id] = {
            "session_id": session_id,
            "language": "en",
            "status": "ACTIVE",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
            "emotion_signals": [],
            "stress_signals": [],
            "transcripts": []
        }
        session = session_service.get_session(session_id)

    # If no assessment passed in request body, perform assessment on current session state
    if assessment is None:
        try:
            input_data = MultimodalAssessmentInput(session_id=session_id)
            transcripts = session.get("transcripts", [])
            if transcripts:
                input_data.transcript = transcripts[-1].get("text")
            elif session.get("messages"):
                input_data.transcript = session["messages"][-1].get("text", "")

            emotions = session_service.get_emotion_signals(session_id)
            for e in reversed(emotions):
                if e.source == "speech" and e.speech_emotion and not input_data.speech_emotion:
                    input_data.speech_emotion = e.speech_emotion
                if e.source == "text" and e.text_emotion and not input_data.text_emotion:
                    input_data.text_emotion = e.text_emotion

            stress_sigs = session_service.get_stress_signals(session_id)
            if stress_sigs:
                input_data.stress = stress_sigs[-1].stress

            assessment = gemma_service.assess(input_data)
        except Exception as e:
            logger.error(f"Error generating assessment for recommendations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate underlying assessment for recommendation engine"
            )

    result = recommendation_service.generate_and_store_recommendations(
        session_id=session_id,
        assessment=assessment,
        session_context={"language": session.get("language", "en")}
    )

    # Persist recommendations to PostgreSQL
    try:
        conv_stmt = select(Conversation).where(Conversation.session_id == session_id)
        conv_res = await db.execute(conv_stmt)
        conv_obj = conv_res.scalars().first()
        case_id = conv_obj.case_id if conv_obj else None

        if not case_id:
            case_ref = f"NHAA-AUTO-{uuid.uuid4().hex[:8].upper()}"
            new_c = Case(external_case_reference=case_ref, status=CaseStatus.NEW)
            db.add(new_c)
            await db.flush()
            case_id = new_c.id
            if conv_obj:
                conv_obj.case_id = case_id
            else:
                conv_obj = Conversation(case_id=case_id, session_id=session_id)
                db.add(conv_obj)
                await db.flush()

        for rec in result.recommendations:
            db_rec = RecommendationModel(
                id=rec.recommendation_id,
                case_id=case_id,
                session_id=session_id,
                category=rec.category,
                priority=rec.priority,
                reason=rec.reason,
                supporting_indicators=rec.supporting_indicators,
                evidence_sources=rec.evidence_sources,
                responder_action=rec.responder_action,
                requires_human_review=rec.requires_human_review,
                status=rec.status or "PENDING"
            )
            db.add(db_rec)
        await db.commit()
    except Exception as dbe:
        logger.error(f"Failed to persist recommendations to DB: {dbe}")

    return result

@router.get("/{session_id}/recommendations", response_model=SupportRecommendationResult)
async def get_session_recommendations(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve existing support recommendations for a session."""
    # Check DB first
    stmt = (
        select(RecommendationModel)
        .where(RecommendationModel.session_id == session_id)
        .order_by(RecommendationModel.created_at.asc())
    )
    res = await db.execute(stmt)
    db_recs = res.scalars().all()

    if db_recs:
        recs = [
            SupportRecommendation(
                recommendation_id=r.id,
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
                created_at=r.created_at.isoformat() if r.created_at else None
            ) for r in db_recs
        ]
        return SupportRecommendationResult(
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            recommendations=recs,
            total_recommendations=len(recs),
            requires_immediate_safety_action=any(r.priority == "immediate" for r in recs)
        )

    # In-memory fallback
    result = recommendation_service.get_recommendations(session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendations have been generated for this session yet"
        )
    return result

@router.post(
    "/{session_id}/recommendations/{recommendation_id}/review",
    response_model=RecommendationReviewResponse
)
async def review_recommendation(
    session_id: str,
    recommendation_id: str,
    review: RecommendationReviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """Record human responder review action (accept, modify, reject) on a support pathway."""
    # In-memory review
    try:
        updated_rec = recommendation_service.review_recommendation(
            session_id=session_id,
            recommendation_id=recommendation_id,
            review=review
        )
    except KeyError:
        updated_rec = None

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # DB review & audit logging
    stmt = select(RecommendationModel).where(RecommendationModel.id == recommendation_id)
    rec_res = await db.execute(stmt)
    db_rec = rec_res.scalars().first()

    if db_rec:
        decision_val = review.decision.upper()
        db_rec.status = decision_val
        db_rec.responder_decision = decision_val
        db_rec.responder_note = review.responder_note
        db_rec.reviewed_at = now
        db_rec.reviewed_by = "ADMIN"

        # Record RecommendationReview entity
        mod_rec = {}
        if getattr(review, "modified_priority", None):
            mod_rec["priority"] = review.modified_priority
        if getattr(review, "modified_action", None):
            mod_rec["action"] = review.modified_action

        rec_review = RecommendationReview(
            recommendation_id=db_rec.id,
            admin_id=None,
            decision=decision_val,
            modified_recommendation=mod_rec if mod_rec else None,
            review_notes=review.responder_note,
            reviewed_at=now
        )
        db.add(rec_review)

        # Record AuditEvent
        audit = AuditEvent(
            case_id=db_rec.case_id,
            actor_id="ADMIN",
            actor_type="ADMIN",
            event_type=f"RECOMMENDATION_{decision_val}",
            entity_type="RECOMMENDATION",
            entity_id=db_rec.id,
            event_metadata={
                "decision": decision_val,
                "notes": review.responder_note,
                "category": db_rec.category
            }
        )
        db.add(audit)
        await db.commit()
        await db.refresh(db_rec)

    if not updated_rec and not db_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found"
        )

    if not updated_rec and db_rec:
        updated_rec = SupportRecommendation(
            recommendation_id=db_rec.id,
            category=db_rec.category,
            priority=db_rec.priority,
            reason=db_rec.reason,
            supporting_indicators=db_rec.supporting_indicators,
            evidence_sources=db_rec.evidence_sources,
            responder_action=db_rec.responder_action,
            requires_human_review=db_rec.requires_human_review,
            status=db_rec.status,
            responder_decision=db_rec.responder_decision,
            responder_note=db_rec.responder_note,
            created_at=db_rec.created_at.isoformat()
        )

    return RecommendationReviewResponse(
        recommendation=updated_rec,
        status="reviewed",
        timestamp=now_iso
    )
