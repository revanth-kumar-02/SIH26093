from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.conversation import Conversation
from app.db.models.message import MessageSenderType, MessageInputSource
from app.schemas.session import SessionCreateRequest, SessionResponse
from app.schemas.conversation import MessageSendRequest, MessageResponse
from app.schemas.emotion import EmotionSignal
from app.schemas.stress import StressSignal
from app.services.session_service import session_service
from app.services.emotion.text_emotion_service import text_emotion_service
from app.services.stress.service import stress_detection_service
from app.services.memory_service import memory_service
from app.core.security import generate_message_id
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])

class PersistedMessageItem(BaseModel):
    id: str
    content: str
    sender_type: str
    input_source: str
    timestamp: datetime
    language: str

class PersistedSignalItem(BaseModel):
    id: str
    session_id: str
    signal_type: str
    source: str = "text"
    result: Dict[str, Any]
    confidence: Optional[float] = None
    model_name: str
    model_version: str
    created_at: datetime
    text_emotion: Optional[Dict[str, Any]] = None
    speech_emotion: Optional[Dict[str, Any]] = None
    stress: Optional[Dict[str, Any]] = None

class SessionMemoryResponse(BaseModel):
    session_id: str
    historical_memory: str

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest = SessionCreateRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Create a new victim interaction session and persist it to PostgreSQL."""
    return await session_service.create_persistent_session(db=db, language=request.language)

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get status and details of an active session."""
    stmt = select(Conversation).where(Conversation.session_id == session_id)
    res = await db.execute(stmt)
    conv = res.scalars().first()
    if not conv:
        # Check in-memory fallback
        mem_session = session_service.get_session(session_id)
        if not mem_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        return SessionResponse(
            session_id=session_id,
            language=mem_session.get("language", "en"),
            status=mem_session.get("status", "ACTIVE"),
            created_at=mem_session.get("created_at", "")
        )

    return SessionResponse(
        session_id=conv.session_id,
        language=conv.input_language,
        status=conv.status,
        created_at=conv.created_at.isoformat()
    )

@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    request: MessageSendRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a message in an existing session and receive an empathetic triage response.
    
    Multimodal Text Pipeline:
    Text Message -> GoEmotions TER -> Text Emotion Signal (persisted to DB)
    Text Message -> Dreaddit Stress -> Stress Signal (persisted to DB)
    Both signals and messages are persisted to PostgreSQL.
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
        # Restore in-memory representation if DB has it
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

    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Persist user's incoming message to DB
    user_msg_db = await session_service.persist_message(
        db=db,
        session_id=session_id,
        sender_type=MessageSenderType.VICTIM,
        content=request.message,
        input_source=MessageInputSource.TEXT,
        language=session.get("language", "en")
    )

    # 2. Extract text emotion signal (GoEmotions)
    try:
        text_emotion_result = text_emotion_service.analyze(request.message)
        emotion_signal = EmotionSignal(
            signal_id=generate_message_id(),
            session_id=session_id,
            source="text",
            timestamp=now_iso,
            text_emotion=text_emotion_result,
            metadata={
                "model": text_emotion_result.model_version,
                "latency_ms": text_emotion_result.duration_ms,
                "device": text_emotion_result.device
            }
        )
        session_service.add_emotion_signal(session_id, emotion_signal)
        
        # Persist to DB
        await session_service.persist_ai_signal(
            db=db,
            session_id=session_id,
            message_id=user_msg_db.id if user_msg_db else None,
            signal_type="TEXT_EMOTION",
            result=text_emotion_result.model_dump(),
            confidence=text_emotion_result.emotions[0].score if text_emotion_result.emotions else None,
            model_name="SamLowe/roberta-base-go_emotions",
            model_version=text_emotion_result.model_version
        )
    except Exception as ex:
        logger.warning(f"Text emotion extraction skipped or failed: {ex}")

    # 3. Extract stress signal (MentalBERT Dreaddit)
    try:
        stress_result = stress_detection_service.analyze(request.message)
        stress_signal = StressSignal(
            signal_id=generate_message_id(),
            session_id=session_id,
            source="text",
            timestamp=now_iso,
            stress=stress_result,
            model_version=stress_result.model_version,
            metadata={
                "latency_ms": stress_result.duration_ms,
                "device": stress_result.device
            }
        )
        session_service.add_stress_signal(session_id, stress_signal)

        # Persist to DB
        await session_service.persist_ai_signal(
            db=db,
            session_id=session_id,
            message_id=user_msg_db.id if user_msg_db else None,
            signal_type="STRESS",
            result=stress_result.model_dump(),
            confidence=stress_result.score,
            model_name="jtvallente/mentalbert_dreaddit_best",
            model_version=stress_result.model_version
        )
    except Exception as ex:
        logger.warning(f"Stress detection on message skipped or failed: {ex}")

    try:
        msg_resp = session_service.process_message(session_id=session_id, message=request.message)
        
        # Persist system response to DB
        await session_service.persist_message(
            db=db,
            session_id=session_id,
            sender_type=MessageSenderType.SYSTEM,
            content=msg_resp.response,
            input_source=MessageInputSource.AI,
            language=session.get("language", "en")
        )

        return msg_resp
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

@router.get("/{session_id}/messages", response_model=List[PersistedMessageItem])
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve full persisted conversation messages from PostgreSQL."""
    msgs = await session_service.get_persisted_messages(db, session_id)
    return [
        PersistedMessageItem(
            id=m.id,
            content=m.content,
            sender_type=m.sender_type.value,
            input_source=m.input_source.value,
            timestamp=m.timestamp,
            language=m.language
        ) for m in msgs
    ]

@router.get("/{session_id}/signals", response_model=List[PersistedSignalItem])
async def get_session_signals(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all structured AI signals (emotions, stress) recorded for this session."""
    signals = await session_service.get_persisted_signals(db, session_id)
    return [
        PersistedSignalItem(
            id=s.id,
            session_id=s.session_id,
            signal_type=s.signal_type,
            source="speech" if "SPEECH" in s.signal_type.upper() else "text",
            result=s.result,
            confidence=s.confidence,
            model_name=s.model_name,
            model_version=s.model_version,
            created_at=s.created_at,
            text_emotion=s.result if s.signal_type == "TEXT_EMOTION" else None,
            speech_emotion=s.result if s.signal_type == "SPEECH_EMOTION" else None,
            stress=s.result if s.signal_type == "STRESS" else None
        ) for s in signals
    ]

@router.get("/{session_id}/memory", response_model=SessionMemoryResponse)
async def get_session_memory(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve controlled, bounded historical application memory for the session."""
    mem_context = await memory_service.retrieve_bounded_context(db, session_id)
    return SessionMemoryResponse(
        session_id=session_id,
        historical_memory=mem_context
    )
