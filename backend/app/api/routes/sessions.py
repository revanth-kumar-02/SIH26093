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
    """Send a message in an existing session and receive an empathetic, trauma-informed response.
    
    Multimodal Pipeline:
    Text Message -> GoEmotions TER -> Text Emotion Signal (persisted to DB)
    Text Message -> Dreaddit Stress -> Stress Signal (persisted to DB)
    Bounded Context -> Gemma 3n E2B IT Multimodal Assessment (persisted to DB)
    Assessment Indicators -> Deterministic SVI (persisted to DB)
    SVI & Assessment -> Tailored Recommendations (persisted to DB)
    Empathetic Grounded Response -> AI Message (persisted to DB)
    """
    session = session_service.get_session(session_id)
    language = request.language or (session.get("language", "en") if session else "en")
    if not session:
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        res = await db.execute(stmt)
        conv = res.scalars().first()
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        if not request.language:
            language = conv.input_language or "en"

    input_source = (
        MessageInputSource.VOICE
        if request.input_source and request.input_source.upper() == "VOICE"
        else MessageInputSource.TEXT
    )

    try:
        return await session_service.process_incoming_interaction(
            db=db,
            session_id=session_id,
            message=request.message,
            input_source=input_source,
            language=language
        )
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
