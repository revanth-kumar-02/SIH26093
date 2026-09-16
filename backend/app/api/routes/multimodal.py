import uuid
from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.db.models.assessment import AssessmentModel
from app.db.models.conversation import Conversation
from app.db.models.case import Case, CaseStatus
from app.services.llm.schemas import (
    MultimodalAssessmentInput,
    TraumaAssessment,
    ConversationTurn
)
from app.services.session_service import session_service
from app.services.llm.service import gemma_service
from app.services.memory_service import memory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Multimodal LLM Assessment"])

@router.post("/{session_id}/analyze/multimodal", response_model=TraumaAssessment)
async def analyze_multimodal(
    session_id: str,
    payload: Optional[MultimodalAssessmentInput] = Body(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Execute Gemma-3n multimodal trauma-informed evidence assessment.
    
    Accepts explicit MultimodalAssessmentInput or automatically populates missing signals
    from accumulated session state (ASR transcripts, Wav2Vec2 SER, GoEmotions TER, Dreaddit stress),
    augments with bounded historical case memory, and persists the assessment to PostgreSQL.
    
    IMPORTANT:
    This produces an AI-assisted evidence assessment aid for trained human responders.
    It does NOT compute SVI, diagnose psychiatric conditions, or trigger automated police/emergency action.
    """
    session = session_service.get_session(session_id)
    if not session:
        # Check database
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        res = await db.execute(stmt)
        conv = res.scalars().first()
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        session_service._sessions[session_id] = {
            "session_id": session_id,
            "language": conv.input_language,
            "status": conv.status,
            "created_at": conv.created_at.isoformat(),
            "messages": [],
            "emotion_signals": [],
            "stress_signals": [],
            "transcripts": []
        }
        session = session_service.get_session(session_id)

    # Initialize or enrich input object
    if payload is None:
        payload = MultimodalAssessmentInput(session_id=session_id)
    else:
        payload.session_id = session_id

    # Retrieve and attach bounded historical case memory if not provided
    if not payload.historical_memory:
        try:
            historical_context = await memory_service.retrieve_bounded_context(db, session_id)
            if historical_context:
                payload.historical_memory = historical_context
        except Exception as me:
            logger.warning(f"Historical memory retrieval skipped: {me}")

    # Auto-fill missing signals from accumulated session evidence if not explicitly passed
    if not payload.transcript:
        transcripts = session.get("transcripts", [])
        if transcripts:
            payload.transcript = transcripts[-1].get("text", "")
        elif session.get("messages"):
            payload.transcript = session["messages"][-1].get("text", "")

    if not payload.conversation_context and session.get("messages"):
        turns = []
        for m in session.get("messages", [])[-6:]:
            turns.append(ConversationTurn(
                role=m.get("source", "user"),
                text=f"[length {m.get('user_message_length', 0)} chars]" if "user_message_length" in m else m.get("text", ""),
                timestamp=m.get("timestamp")
            ))
        payload.conversation_context = turns

    if not payload.speech_emotion:
        emotions = session_service.get_emotion_signals(session_id)
        speech_sigs = [s for s in emotions if s.source == "speech" and s.speech_emotion]
        if speech_sigs:
            payload.speech_emotion = speech_sigs[-1].speech_emotion

    if not payload.text_emotion:
        emotions = session_service.get_emotion_signals(session_id)
        text_sigs = [s for s in emotions if s.source == "text" and s.text_emotion]
        if text_sigs:
            payload.text_emotion = text_sigs[-1].text_emotion

    if not payload.stress:
        stress_sigs = session_service.get_stress_signals(session_id)
        if stress_sigs:
            payload.stress = stress_sigs[-1].stress

    if not payload.language:
        payload.language = session.get("language", "en")

    try:
        assessment = gemma_service.assess(payload)
        session["latest_assessment"] = assessment

        # Persist assessment to PostgreSQL
        conv_stmt = select(Conversation).where(Conversation.session_id == session_id)
        conv_res = await db.execute(conv_stmt)
        conv_obj = conv_res.scalars().first()
        case_id = conv_obj.case_id if conv_obj else None

        if not case_id:
            # Create a case if none exists
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

        db_assessment = AssessmentModel(
            case_id=case_id,
            session_id=session_id,
            assessment_version="google/gemma-3n-E2B-it",
            assessment_payload=assessment.model_dump()
        )
        db.add(db_assessment)
        await db.commit()
        await db.refresh(db_assessment)

        return assessment
    except Exception as e:
        logger.error(f"Multimodal assessment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Multimodal assessment reasoning failed"
        )

@router.get("/{session_id}/assessment", response_model=TraumaAssessment)
async def get_session_assessment(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the latest persisted Gemma multimodal trauma assessment for a session."""
    # First check DB
    stmt = (
        select(AssessmentModel)
        .where(AssessmentModel.session_id == session_id)
        .order_by(desc(AssessmentModel.created_at))
    )
    res = await db.execute(stmt)
    db_assessment = res.scalars().first()

    if db_assessment:
        return TraumaAssessment(**db_assessment.assessment_payload)

    # Fallback to session state in memory
    session = session_service.get_session(session_id)
    if session and "latest_assessment" in session:
        return session["latest_assessment"]

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No assessment recorded for this session yet"
    )
