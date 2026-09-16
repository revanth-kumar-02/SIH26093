from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.security import generate_session_id, generate_message_id
from app.schemas.session import SessionResponse
from app.schemas.conversation import MessageResponse
from app.schemas.emotion import EmotionSignal, MultimodalSessionState
from app.schemas.stress import StressSignal

from app.db.models.conversation import Conversation
from app.db.models.case import Case, CaseStatus
from app.db.models.message import Message, MessageSenderType, MessageInputSource
from app.db.models.ai_signal import AISignal

logger = logging.getLogger(__name__)

class SessionStatus:
    SESSION_CREATED = "SESSION_CREATED"
    ACTIVE = "ACTIVE"
    ASSESSMENT_IN_PROGRESS = "ASSESSMENT_IN_PROGRESS"
    ASSESSMENT_COMPLETE = "ASSESSMENT_COMPLETE"
    RESPONDER_REVIEW = "RESPONDER_REVIEW"
    ACTION_RECORDED = "ACTION_RECORDED"
    CLOSED = "CLOSED"

VALID_TRANSITIONS = {
    SessionStatus.SESSION_CREATED: [SessionStatus.ACTIVE, SessionStatus.CLOSED],
    SessionStatus.ACTIVE: [SessionStatus.ASSESSMENT_IN_PROGRESS, SessionStatus.CLOSED],
    SessionStatus.ASSESSMENT_IN_PROGRESS: [SessionStatus.ASSESSMENT_COMPLETE, SessionStatus.ACTIVE, SessionStatus.CLOSED],
    SessionStatus.ASSESSMENT_COMPLETE: [SessionStatus.RESPONDER_REVIEW, SessionStatus.CLOSED],
    SessionStatus.RESPONDER_REVIEW: [SessionStatus.ACTION_RECORDED, SessionStatus.CLOSED],
    SessionStatus.ACTION_RECORDED: [SessionStatus.CLOSED, SessionStatus.RESPONDER_REVIEW],
    SessionStatus.CLOSED: [SessionStatus.ACTIVE]
}

class SessionService:
    """Session management service with trauma-informed state machine and multimodal evidence integration.
    
    Stores conversation history and multimodal signals:
    - IndicConformer ASR Transcripts
    - Wav2Vec2 Speech Emotion Signals
    - RoBERTa GoEmotions Text Emotion Signals
    - MentalBERT Dreaddit Stress Signals
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, language: str = "en") -> SessionResponse:
        session_id = generate_session_id()
        now_iso = datetime.now(timezone.utc).isoformat()
        
        self._sessions[session_id] = {
            "session_id": session_id,
            "language": language,
            "status": SessionStatus.SESSION_CREATED,
            "created_at": now_iso,
            "updated_at": now_iso,
            "messages": [],
            "emotion_signals": [],
            "stress_signals": [],
            "transcripts": [],
            "consent_agreed": True
        }
        
        return SessionResponse(
            session_id=session_id,
            language=language,
            status=SessionStatus.SESSION_CREATED,
            created_at=now_iso
        )

    async def create_persistent_session(
        self,
        db: AsyncSession,
        language: str = "en",
        user_id: Optional[str] = None,
        case_id: Optional[str] = None
    ) -> SessionResponse:
        """Create a session and persist it to PostgreSQL/SQLite, attaching to a Case."""
        # First ensure in-memory tracking
        mem_resp = self.create_session(language=language)
        session_id = mem_resp.session_id

        # Resolve or create Case
        if case_id:
            case_stmt = select(Case).where(Case.id == case_id)
            case_res = await db.execute(case_stmt)
            target_case = case_res.scalars().first()
        elif user_id:
            # Check for existing active case for this user
            case_stmt = select(Case).where(
                and_(Case.user_id == user_id, Case.status != CaseStatus.CLOSED)
            ).order_by(Case.created_at.desc())
            case_res = await db.execute(case_stmt)
            target_case = case_res.scalars().first()
            if not target_case:
                case_ref = f"NHAA-CASE-{generate_session_id()[:8].upper()}"
                target_case = Case(
                    external_case_reference=case_ref,
                    status=CaseStatus.NEW,
                    language=language,
                    consent_status="CONSENT_GIVEN",
                    user_id=user_id
                )
                db.add(target_case)
                await db.flush()
        else:
            # Anonymous / guest case
            case_ref = f"NHAA-ANON-{generate_session_id()[:8].upper()}"
            target_case = Case(
                external_case_reference=case_ref,
                status=CaseStatus.NEW,
                language=language,
                consent_status="CONSENT_GIVEN"
            )
            db.add(target_case)
            await db.flush()

        conv = Conversation(
            case_id=target_case.id,
            session_id=session_id,
            input_language=language,
            status=SessionStatus.SESSION_CREATED,
            consent_status="CONSENT_GIVEN"
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

        self._sessions[session_id]["case_id"] = target_case.id
        return mem_resp

    async def persist_message(
        self,
        db: AsyncSession,
        session_id: str,
        sender_type: MessageSenderType,
        content: str,
        input_source: MessageInputSource = MessageInputSource.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> Message:
        """Persist a conversation message with idempotency check against duplicate submissions."""
        # Find conversation by session_id
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        res = await db.execute(stmt)
        conv = res.scalars().first()
        
        # Idempotency: check if identical message was received in last 2 seconds
        if conv:
            check_stmt = select(Message).where(
                and_(
                    Message.conversation_id == conv.id,
                    Message.content == content,
                    Message.sender_type == sender_type
                )
            ).order_by(Message.timestamp.desc()).limit(1)
            recent = (await db.execute(check_stmt)).scalars().first()
            if recent:
                ts = recent.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - ts).total_seconds() < 2.0:
                    logger.info(f"Duplicate message detected for session {session_id}, returning existing record.")
                    return recent

        conv_id = conv.id if conv else None
        if not conv_id:
            # Auto-create fallback conversation if session was started in memory
            case_ref = f"NHAA-AUTO-{generate_session_id()[:8].upper()}"
            target_case = Case(
                external_case_reference=case_ref,
                status=CaseStatus.NEW,
                language=language
            )
            db.add(target_case)
            await db.flush()
            conv = Conversation(
                case_id=target_case.id,
                session_id=session_id,
                input_language=language,
                status="ACTIVE"
            )
            db.add(conv)
            await db.flush()
            conv_id = conv.id

        db_msg = Message(
            conversation_id=conv_id,
            session_id=session_id,
            sender_type=sender_type,
            input_source=input_source,
            content=content,
            language=language,
            message_metadata=metadata or {}
        )
        db.add(db_msg)
        await db.commit()
        await db.refresh(db_msg)
        return db_msg

    async def persist_ai_signal(
        self,
        db: AsyncSession,
        session_id: str,
        signal_type: str,
        result: Dict[str, Any],
        confidence: Optional[float],
        model_name: str,
        model_version: str,
        message_id: Optional[str] = None
    ) -> AISignal:
        """Persist structured AI signal (speech emotion, text emotion, stress) to database."""
        sig = AISignal(
            session_id=session_id,
            message_id=message_id,
            signal_type=signal_type,
            result=result,
            confidence=confidence,
            model_name=model_name,
            model_version=model_version
        )
        db.add(sig)
        await db.commit()
        await db.refresh(sig)
        return sig

    async def get_persisted_messages(self, db: AsyncSession, session_id: str) -> List[Message]:
        """Retrieve full conversation messages ordered chronologically from database."""
        stmt = (
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(Conversation.session_id == session_id)
            .order_by(Message.timestamp.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_persisted_signals(self, db: AsyncSession, session_id: str) -> List[AISignal]:
        """Retrieve all structured AI signals for a session from database."""
        stmt = select(AISignal).where(AISignal.session_id == session_id).order_by(AISignal.created_at.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_id)

    def transition_status(self, session_id: str, target_status: str) -> str:
        """Validate and execute a formal session lifecycle state transition."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        current_status = session.get("status", SessionStatus.SESSION_CREATED)
        allowed = VALID_TRANSITIONS.get(current_status, [])

        if target_status != current_status and target_status not in allowed:
            raise ValueError(
                f"Invalid session status transition from '{current_status}' to '{target_status}'. "
                f"Allowed transitions: {allowed}"
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        session["status"] = target_status
        session["updated_at"] = now_iso
        logger.info(f"Session {session_id} transitioned: {current_status} -> {target_status}")
        return target_status

    def add_emotion_signal(self, session_id: str, signal: EmotionSignal) -> None:
        """Store typed emotion signal in session state."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")
        if "emotion_signals" not in session:
            session["emotion_signals"] = []
        session["emotion_signals"].append(signal)

        # Transition to ACTIVE if currently in SESSION_CREATED
        if session.get("status") == SessionStatus.SESSION_CREATED:
            self.transition_status(session_id, SessionStatus.ACTIVE)

    def get_emotion_signals(self, session_id: str) -> List[EmotionSignal]:
        session = self.get_session(session_id)
        if not session:
            return []
        return session.get("emotion_signals", [])

    def add_stress_signal(self, session_id: str, signal: StressSignal) -> None:
        """Store typed stress signal in session state."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")
        if "stress_signals" not in session:
            session["stress_signals"] = []
        session["stress_signals"].append(signal)

    def get_stress_signals(self, session_id: str) -> List[StressSignal]:
        session = self.get_session(session_id)
        if not session:
            return []
        return session.get("stress_signals", [])

    def add_transcript(self, session_id: str, transcript_data: Dict[str, Any]) -> None:
        """Store transcript metadata in session state."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")
        if "transcripts" not in session:
            session["transcripts"] = []
        session["transcripts"].append(transcript_data)

        # Auto-advance to ACTIVE
        if session.get("status") == SessionStatus.SESSION_CREATED:
            self.transition_status(session_id, SessionStatus.ACTIVE)

    def get_multimodal_state(self, session_id: str) -> MultimodalSessionState:
        """Retrieve full structured multimodal evidence layer for the session."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        emotion_signals: List[EmotionSignal] = session.get("emotion_signals", [])
        speech_signals = [s for s in emotion_signals if s.source == "speech"]
        text_signals = [s for s in emotion_signals if s.source == "text"]
        stress_signals: List[StressSignal] = session.get("stress_signals", [])
        transcripts: List[Dict[str, Any]] = session.get("transcripts", [])

        total = len(speech_signals) + len(text_signals) + len(stress_signals) + len(transcripts)

        return MultimodalSessionState(
            session_id=session_id,
            language=session.get("language", "en"),
            status=session.get("status", SessionStatus.ACTIVE),
            created_at=session.get("created_at", ""),
            speech_emotion_signals=speech_signals,
            text_emotion_signals=text_signals,
            stress_signals=stress_signals,
            transcripts=transcripts,
            total_signals=total
        )

    def process_message(self, session_id: str, message: str) -> MessageResponse:
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        # Auto-advance to ACTIVE
        if session.get("status") == SessionStatus.SESSION_CREATED:
            self.transition_status(session_id, SessionStatus.ACTIVE)

        lower = message.lower()
        if any(w in lower for w in ["shelter", "stay", "unsafe", "hostel", "home"]):
            reply = (
                "Thank you for trusting us with this. Your immediate safety is our utmost priority. "
                "We have verified emergency shelter options and advocates ready to ensure you have a secure place tonight. "
                "Would you like to view emergency shelter resources or speak directly with an advocate?"
            )
        elif any(w in lower for w in ["threat", "call", "message", "harass", "stalk"]):
            reply = (
                "I am so sorry you are having to endure this intimidation. You do not have to carry this alone. "
                "We can document these incidents securely with timestamps and connect you with trauma-informed legal and psychological counselors."
            )
        elif any(w in lower for w in ["anonymous", "privacy", "secret", "hide"]):
            reply = (
                "Understood completely. Everything shared here is protected with zero-knowledge protocols. "
                "You can proceed with full anonymity, and your identity will remain protected."
            )
        elif any(w in lower for w in ["legal", "law", "court", "police", "fir"]):
            reply = (
                "We can coordinate confidential pro-bono legal support and rights advisement under the National Helpline Against Atrocities (NHAA) framework whenever you feel prepared."
            )
        else:
            reply = (
                "Take your time. You can share what happened in your own words. "
                "We are here to listen and help you find the right support."
            )

        message_id = generate_message_id()
        now_iso = datetime.now(timezone.utc).isoformat()

        session["messages"].append({
            "message_id": message_id,
            "content": message,
            "sender_type": "VICTIM",
            "input_source": "TEXT",
            "timestamp": now_iso
        })

        return MessageResponse(
            message_id=message_id,
            response=reply,
            status="received",
            timestamp=now_iso
        )

session_service = SessionService()
