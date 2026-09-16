import uuid
from datetime import datetime, timezone
from typing import Optional
import logging
from fastapi import APIRouter, HTTPException, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.db.models.svi import SVIResultModel
from app.db.models.conversation import Conversation
from app.db.models.case import Case, CaseStatus
from app.services.session_service import session_service
from app.services.llm.service import gemma_service
from app.services.llm.schemas import MultimodalAssessmentInput
from app.services.svi.schemas import SVIInput, SVIResult, SVIFactor
from app.services.svi.service import svi_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Stress Vulnerability Index (SVI)"])

@router.post("/{session_id}/svi", response_model=SVIResult)
async def calculate_session_svi(
    session_id: str,
    payload: Optional[SVIInput] = Body(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Calculate the deterministic Stress Vulnerability Index (SVI) for a session and persist to DB.
    
    Consumes structured assessment evidence or automatically performs assessment on
    accumulated session state.
    
    IMPORTANT:
    SVI is an AI-assisted risk triage aid for trained human helpline responders.
    It does NOT constitute a clinical diagnosis, psychiatric determination, or automated emergency dispatch.
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

    if payload is None:
        payload = SVIInput(session_id=session_id)
    else:
        payload.session_id = session_id

    # If no explicit assessment or indicators supplied, auto-evaluate from session state
    if payload.assessment is None and not payload.indicators:
        try:
            assessment_input = MultimodalAssessmentInput(session_id=session_id)
            transcripts = session.get("transcripts", [])
            if transcripts:
                assessment_input.transcript = transcripts[-1].get("text")
            elif session.get("messages"):
                assessment_input.transcript = session["messages"][-1].get("text", "")

            emotions = session_service.get_emotion_signals(session_id)
            for e in reversed(emotions):
                if e.source == "speech" and e.speech_emotion and not assessment_input.speech_emotion:
                    assessment_input.speech_emotion = e.speech_emotion
                if e.source == "text" and e.text_emotion and not assessment_input.text_emotion:
                    assessment_input.text_emotion = e.text_emotion

            stress_sigs = session_service.get_stress_signals(session_id)
            if stress_sigs:
                assessment_input.stress = stress_sigs[-1].stress

            assessment = gemma_service.assess(assessment_input)
            payload.assessment = assessment
        except Exception as e:
            logger.error(f"Error compiling assessment for SVI: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to compile underlying assessment evidence for SVI calculation"
            )

    result = svi_service.calculate_and_store_svi(payload)

    # Persist to PostgreSQL
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

        db_svi = SVIResultModel(
            case_id=case_id,
            session_id=session_id,
            svi_version=result.svi_version,
            score=result.score,
            risk_category=result.risk_category.value if hasattr(result.risk_category, "value") else str(result.risk_category),
            factor_contributions=[f.model_dump() for f in result.factor_contributions],
            key_drivers=result.key_drivers,
            uncertainties=result.uncertainties,
            immediate_safety_attention=result.immediate_safety_attention,
            urgent_human_review=result.urgent_human_review
        )
        db.add(db_svi)
        await db.commit()
    except Exception as dbe:
        logger.error(f"Failed to persist SVI to database: {dbe}")

    return result

@router.get("/{session_id}/svi", response_model=SVIResult)
async def get_session_svi(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the latest stored SVI calculation result for a session."""
    # Check DB first
    stmt = (
        select(SVIResultModel)
        .where(SVIResultModel.session_id == session_id)
        .order_by(desc(SVIResultModel.created_at))
    )
    res = await db.execute(stmt)
    db_svi = res.scalars().first()

    if db_svi:
        factors = [
            SVIFactor(**f) if isinstance(f, dict) else f
            for f in db_svi.factor_contributions
        ]
        return SVIResult(
            svi_version=db_svi.svi_version,
            session_id=db_svi.session_id or session_id,
            score=db_svi.score,
            risk_category=db_svi.risk_category,
            factor_contributions=factors,
            key_drivers=db_svi.key_drivers,
            uncertainties=db_svi.uncertainties,
            immediate_safety_attention=db_svi.immediate_safety_attention,
            urgent_human_review=db_svi.urgent_human_review,
            requires_human_review=True,
            calculation_timestamp=db_svi.created_at.isoformat(),
            audit_metadata={}
        )

    # In-memory fallback
    result = svi_service.get_svi(session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No SVI calculation recorded for this session yet"
        )
    return result
