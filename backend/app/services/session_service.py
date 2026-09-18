from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.core.security import generate_session_id, generate_message_id
from app.schemas.session import SessionResponse
from app.schemas.conversation import MessageResponse
from app.schemas.emotion import EmotionSignal, MultimodalSessionState, SpeechEmotionResult
from app.schemas.stress import StressSignal, StressDetectionResult

from app.db.models.conversation import Conversation
from app.db.models.case import Case, CaseStatus
from app.db.models.message import Message, MessageSenderType, MessageInputSource
from app.db.models.ai_signal import AISignal
from app.db.models.assessment import AssessmentModel
from app.db.models.svi import SVIResultModel
from app.db.models.recommendation import RecommendationModel

from app.services.emotion.text_emotion_service import text_emotion_service
from app.services.stress.service import stress_detection_service
from app.services.memory_service import memory_service
from app.services.llm.service import gemma_service
from app.services.llm.schemas import MultimodalAssessmentInput, ConversationTurn
from app.services.svi.service import svi_service
from app.services.svi.schemas import SVIInput
from app.services.recommendation.service import recommendation_service

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

    async def process_incoming_interaction(
        self,
        db: AsyncSession,
        session_id: str,
        message: str,
        input_source: MessageInputSource = MessageInputSource.TEXT,
        speech_emotion_result: Optional[SpeechEmotionResult] = None,
        language: str = "en"
    ) -> MessageResponse:
        """Full end-to-end multimodal transaction pipeline:
        1. Validate/resolve Case & Conversation
        2. Persist user message to PostgreSQL
        3. Extract and persist text emotion (GoEmotions)
        4. Extract and persist stress signal (Dreaddit)
        5. Persist speech emotion if present (Wav2Vec2)
        6. Retrieve bounded historical context (PostgreSQL memory)
        7. Run Gemma 3n E2B IT assessment and persist
        8. Run deterministic SVI calculation and persist
        9. Generate recommendations and persist
        10. Synthesize empathetic response grounded in evidence
        11. Persist system response message
        12. Return structured MessageResponse
        """
        session = self.get_session(session_id)
        if not session:
            stmt = select(Conversation).where(Conversation.session_id == session_id)
            res = await db.execute(stmt)
            conv_db = res.scalars().first()
            if not conv_db:
                raise KeyError(f"Session '{session_id}' not found")
            self._sessions[session_id] = {
                "session_id": session_id,
                "language": conv_db.input_language or language,
                "status": "ACTIVE",
                "case_id": conv_db.case_id,
                "created_at": conv_db.created_at.isoformat() if conv_db.created_at else datetime.now(timezone.utc).isoformat(),
                "messages": [],
                "emotion_signals": [],
                "stress_signals": [],
                "transcripts": [],
                "consent_agreed": True
            }
            session = self.get_session(session_id)

        # Auto-advance to ACTIVE
        if session.get("status") == SessionStatus.SESSION_CREATED:
            self.transition_status(session_id, SessionStatus.ACTIVE)

        now_iso = datetime.now(timezone.utc).isoformat()
        clean_msg = message.strip()
        eff_lang = (language or session.get("language") or "en").lower()

        # Step 1 & 2: Persist user's incoming message
        user_msg = await self.persist_message(
            db=db,
            session_id=session_id,
            sender_type=MessageSenderType.VICTIM,
            content=clean_msg,
            input_source=input_source,
            language=eff_lang
        )

        session["messages"].append({
            "message_id": user_msg.id,
            "content": clean_msg,
            "sender_type": "VICTIM",
            "input_source": input_source.value,
            "timestamp": now_iso
        })

        # Step 3: Extract & persist text emotion (SamLowe/roberta-base-go_emotions)
        text_emotion_res = None
        try:
            text_emotion_res = text_emotion_service.analyze(clean_msg)
            t_sig = EmotionSignal(
                signal_id=generate_message_id(),
                session_id=session_id,
                source="text",
                timestamp=now_iso,
                text_emotion=text_emotion_res,
                metadata={
                    "model": text_emotion_res.model_version,
                    "latency_ms": text_emotion_res.duration_ms,
                    "device": text_emotion_res.device
                }
            )
            self.add_emotion_signal(session_id, t_sig)
            await self.persist_ai_signal(
                db=db,
                session_id=session_id,
                message_id=user_msg.id,
                signal_type="TEXT_EMOTION",
                result=text_emotion_res.model_dump(),
                confidence=text_emotion_res.emotions[0].score if text_emotion_res.emotions else None,
                model_name="SamLowe/roberta-base-go_emotions",
                model_version=text_emotion_res.model_version
            )
        except Exception as ex:
            logger.warning(f"Text emotion extraction warning: {ex}")

        # Step 4: Extract & persist stress signal (jtvallente/mentalbert_dreaddit_best)
        stress_res = None
        try:
            stress_res = stress_detection_service.analyze(clean_msg)
            s_sig = StressSignal(
                signal_id=generate_message_id(),
                session_id=session_id,
                source="text" if input_source == MessageInputSource.TEXT else "speech",
                timestamp=now_iso,
                stress=stress_res,
                model_version=stress_res.model_version,
                metadata={
                    "latency_ms": stress_res.duration_ms,
                    "device": stress_res.device
                }
            )
            self.add_stress_signal(session_id, s_sig)
            await self.persist_ai_signal(
                db=db,
                session_id=session_id,
                message_id=user_msg.id,
                signal_type="STRESS",
                result=stress_res.model_dump(),
                confidence=stress_res.score,
                model_name="jtvallente/mentalbert_dreaddit_best",
                model_version=stress_res.model_version
            )
        except Exception as ex:
            logger.warning(f"Stress detection warning: {ex}")

        # Step 5: Process speech emotion if supplied or in active session
        if not speech_emotion_result and session.get("emotion_signals"):
            for sig in reversed(session["emotion_signals"]):
                if getattr(sig, "source", None) == "speech" and getattr(sig, "speech_emotion", None):
                    speech_emotion_result = sig.speech_emotion
                    break

        if speech_emotion_result:
            try:
                has_sig = any(getattr(s, "source", None) == "speech" and getattr(s, "speech_emotion", None) == speech_emotion_result for s in session.get("emotion_signals", []))
                if not has_sig:
                    sp_sig = EmotionSignal(
                        signal_id=generate_message_id(),
                        session_id=session_id,
                        source="speech",
                        timestamp=now_iso,
                        speech_emotion=speech_emotion_result,
                        metadata={
                            "model": speech_emotion_result.model_version,
                            "latency_ms": speech_emotion_result.duration_ms,
                            "device": speech_emotion_result.device
                        }
                    )
                    self.add_emotion_signal(session_id, sp_sig)
                    await self.persist_ai_signal(
                        db=db,
                        session_id=session_id,
                        message_id=user_msg.id,
                        signal_type="SPEECH_EMOTION",
                        result=speech_emotion_result.model_dump(),
                        confidence=speech_emotion_result.probabilities.get(speech_emotion_result.emotion, 0.0) if speech_emotion_result.probabilities else 0.0,
                        model_name="Dpngtm/wav2vec2-emotion-recognition",
                        model_version=speech_emotion_result.model_version
                    )
            except Exception as ex:
                logger.warning(f"Speech emotion signal persistence warning: {ex}")

        # Step 6: Bounded memory retrieval across sessions
        hist_context = ""
        try:
            hist_context = await memory_service.retrieve_bounded_context(db, session_id)
        except Exception as me:
            logger.warning(f"Historical memory retrieval warning: {me}")

        # Step 7: Build multimodal assessment input & execute Gemma 3n E2B IT
        conversation_turns = []
        for m in session.get("messages", [])[-6:]:
            conversation_turns.append(ConversationTurn(
                role="user" if m.get("sender_type") == "VICTIM" else "assistant",
                text=m.get("content", ""),
                timestamp=m.get("timestamp")
            ))

        assessment_input = MultimodalAssessmentInput(
            session_id=session_id,
            transcript=clean_msg,
            conversation_context=conversation_turns,
            text_emotion=text_emotion_res,
            speech_emotion=speech_emotion_result,
            stress=stress_res,
            language=eff_lang,
            input_source="voice" if input_source == MessageInputSource.VOICE else "text",
            historical_memory=hist_context
        )

        assessment = gemma_service.assess(assessment_input)
        session["latest_assessment"] = assessment

        # Resolve Case ID
        case_id = session.get("case_id")
        if not case_id:
            conv_stmt = select(Conversation).where(Conversation.session_id == session_id)
            conv_res = await db.execute(conv_stmt)
            conv_row = conv_res.scalars().first()
            if conv_row:
                case_id = conv_row.case_id
            else:
                case_ref = f"NHAA-AUTO-{generate_session_id()[:8].upper()}"
                new_c = Case(external_case_reference=case_ref, status=CaseStatus.NEW, language=eff_lang)
                db.add(new_c)
                await db.flush()
                case_id = new_c.id

        # Persist assessment to PostgreSQL
        try:
            db_assessment = AssessmentModel(
                case_id=case_id,
                session_id=session_id,
                assessment_version=assessment.model_version,
                assessment_payload=assessment.model_dump()
            )
            db.add(db_assessment)
            await db.commit()
        except Exception as ae:
            logger.warning(f"Assessment persistence warning: {ae}")

        # Step 8: Deterministic SVI Calculation & Persistence
        svi_result = None
        try:
            svi_input = SVIInput(
                session_id=session_id,
                indicators=assessment.indicators,
                assessment=assessment
            )
            svi_result = svi_service.calculate_and_store_svi(svi_input)

            db_svi = SVIResultModel(
                case_id=case_id,
                session_id=session_id,
                svi_version=svi_result.svi_version,
                score=svi_result.score,
                risk_category=svi_result.risk_category.value if hasattr(svi_result.risk_category, "value") else str(svi_result.risk_category),
                factor_contributions=[f.model_dump() for f in svi_result.factor_contributions],
                key_drivers=svi_result.key_drivers,
                uncertainties=svi_result.uncertainties,
                immediate_safety_attention=svi_result.immediate_safety_attention,
                urgent_human_review=svi_result.urgent_human_review
            )
            db.add(db_svi)
            await db.commit()
        except Exception as se:
            logger.warning(f"SVI calculation/persistence warning: {se}")

        # Step 9: Recommendation Engine & Persistence
        try:
            risk_cat = svi_result.risk_category.value if (svi_result and hasattr(svi_result.risk_category, "value")) else "MEDIUM"
            rec_result = recommendation_service.generate_and_store_recommendations(
                session_id=session_id,
                assessment=assessment,
                session_context={"language": eff_lang, "svi_risk": risk_cat}
            )
            for rec in rec_result.recommendations:
                db_rec = RecommendationModel(
                    id=rec.recommendation_id,
                    case_id=case_id,
                    session_id=session_id,
                    category=rec.category.value if hasattr(rec.category, "value") else str(rec.category),
                    priority=rec.priority.value if hasattr(rec.priority, "value") else str(rec.priority),
                    reason=rec.reason,
                    supporting_indicators=rec.supporting_indicators,
                    evidence_sources=rec.evidence_sources,
                    responder_action=rec.responder_action,
                    requires_human_review=rec.requires_human_review,
                    status=rec.status.value if hasattr(rec.status, "value") else (str(rec.status) if rec.status else "PENDING_REVIEW")
                )
                db.add(db_rec)
            await db.commit()
        except Exception as re:
            logger.warning(f"Recommendation generation/persistence warning: {re}")

        # Step 10: Synthesize empathetic, grounded AI response via Gemma LLM
        ai_reply = self._synthesize_ai_response(
            message=clean_msg,
            assessment=assessment,
            svi_result=svi_result,
            language=eff_lang,
            conversation_turns=conversation_turns
        )

        # Step 11: Persist AI response message to PostgreSQL
        asst_msg = await self.persist_message(
            db=db,
            session_id=session_id,
            sender_type=MessageSenderType.SYSTEM,
            content=ai_reply,
            input_source=MessageInputSource.AI,
            language=eff_lang
        )

        session["messages"].append({
            "message_id": asst_msg.id,
            "content": ai_reply,
            "sender_type": "AI",
            "input_source": "AI",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return MessageResponse(
            message_id=asst_msg.id,
            response=ai_reply,
            status="received",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def _synthesize_ai_response(
        self,
        message: str,
        assessment: Any,
        svi_result: Optional[Any],
        language: str = "en",
        conversation_turns: Optional[List[ConversationTurn]] = None
    ) -> str:
        """Synthesizes trauma-informed empathetic assistant response via Gemma LLM,
        with robust language-specific fallback safety templates."""
        # 1. Try real Gemma conversational generation first
        try:
            llm_response = gemma_service.generate_response(
                user_message=message,
                conversation_history=conversation_turns or [],
                assessment=assessment,
                language=language
            )
            if llm_response and llm_response.strip():
                return llm_response.strip()
        except Exception as err:
            logger.warning(f"Gemma generate_response failed, using safety fallback template: {err}")

        # 2. Deterministic Safety Fallback Templates (Multilingual)
        is_immediate = False
        if svi_result:
            if getattr(svi_result, "immediate_safety_attention", False):
                is_immediate = True
            risk = getattr(svi_result, "risk_category", None)
            risk_val = risk.value if hasattr(risk, "value") else str(risk)
            if risk_val in ["CRITICAL", "HIGH"]:
                is_immediate = True

        lower = message.lower()
        if any(w in lower for w in ["unsafe", "danger", "shelter", "stay", "kill", "threat", "attack", "hurt"]):
            is_immediate = True

        lang_code = language.strip().lower()
        if lang_code.startswith("ta"):
            if is_immediate:
                return (
                    "உங்கள் குரலைக் கேட்கிறோம், இப்போது உங்கள் பாதுகாப்பே எங்களின் முதன்மையான நோக்கம். "
                    "நீங்கள் ஒரு பாதுகாப்பான இடத்தில் இருக்கிறீர்கள். உங்களுக்கு உடனடி உதவி அல்லது அவசர பாதுகாப்பு தேவைப்பட்டால், "
                    "எங்களின் டெமோ ஆதரவு எண் 9787872051 ஐத் தொடர்பு கொள்ளவும். நாங்கள் உங்களுக்காக அவசர தங்குமிடம் மற்றும் ஆலோசகரின் உதவியை ஒருங்கிணைக்கத் தயாராக உள்ளோம்."
                )
            return (
                "நீங்கள் பகிர்ந்துகொண்டதற்கு நன்றி. உங்கள் உணர்வுகளை நாங்கள் புரிந்துகொள்கிறோம். "
                "எதுவும் அவசரமில்லை, உங்கள் சொந்த வேகத்தில் நீங்கள் பேசலாம். உங்களுக்கு உதவ நாங்கள் எப்போதும் இங்கே இருக்கிறோம்."
            )
        elif lang_code.startswith("hi"):
            if is_immediate:
                return (
                    "हम आपकी बात सुन रहे हैं, और इस समय आपकी सुरक्षा हमारी सर्वोच्च प्राथमिकता है। "
                    "आप एक सुरक्षित स्थान पर हैं। यदि आपको तत्काल आपातकालीन सुरक्षा या आश्रय की आवश्यकता है, "
                    "तो कृपया हमारे डेमो सहायता नंबर 9787872051 पर संपर्क करें। हमारी टीम आपकी सहायता के लिए पूरी तरह तत्पर है।"
                )
            return (
                "अपनी बात साझा करने के लिए धन्यवाद। हम आपकी स्थिति और भावनाओं को समझते हैं। "
                "आराम से समय लें, हम हर कदम पर आपका साथ देने के लिए यहाँ हैं।"
            )
        elif lang_code.startswith("te"):
            if is_immediate:
                return (
                    "మేము మీ మాటలను వింటున్నాము, మీ భద్రత మా మొదటి ప్రాధాన్యత. మీరు సురక్షితమైన ప్రదేశంలో ఉన్నారు. "
                    "మీకు తక్షణ అత్యవసర రక్షణ లేదా ఆశ్రయం అవసరమైతే, దయచేసి మా డెమో సంప్రదింపు సంఖ్య 9787872051 కు కాల్ చేయండి."
                )
            return "మీ అనుభవాన్ని మాతో పంచుకున్నందుకు ధన్యవాదాలు. మీ సౌకర్యాన్ని బట్టి నెమ్మదిగా మాట్లాడవచ్చు, మేము మీకు సహాయం చేయడానికి సిద్ధంగా ఉన్నాము."
        elif lang_code.startswith("kn"):
            if is_immediate:
                return (
                    "ನಾವು ನಿಮ್ಮ ಮಾತನ್ನು ಆಲಿಸುತ್ತಿದ್ದೇವೆ, ನಿಮ್ಮ ಸುರಕ್ಷತೆಯೇ ನಮ್ಮ ಮೊದಲ ಆದ್ಯತೆ. "
                    "ನಿಮಗೆ ತಕ್ಷಣದ ತುರ್ತು ನೆರವು ಅಥವಾ ಆಶ್ರಯ ಬೇಕಾದರೆ, ದಯವಿಟ್ಟು ನಮ್ಮ ಡೆಮೊ ಸಂಪರ್ಕ ಸಂಖ್ಯೆ 9787872051 ಗೆ ಕರೆ ಮಾಡಿ."
                )
            return "ನಿಮ್ಮ ಅನುಭವವನ್ನು ಹಂಚಿಕೊಂಡಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮದೇ ಆದ ಗತಿಯಲ್ಲಿ ನೀವು ಮಾತನಾಡಬಹುದು, ನಾವು ನಿಮ್ಮೊಂದಿಗೆ ಇದ್ದೇವೆ."
        elif lang_code.startswith("ml"):
            if is_immediate:
                return (
                    "ഞങ്ങൾ നിങ്ങളുടെ വാക്കുകൾ കേൾക്കുന്നു, നിങ്ങളുടെ സുരക്ഷയാണ് ഞങ്ങളുടെ പ്രഥമ പരിഗണന. "
                    "നിങ്ങൾക്ക് അടിയന്തര സഹായം ആവശ്യമുണ്ടെങ്കിൽ, ദയവായി ഞങ്ങളുടെ ഡെമോ സപ്പോർട്ട് നമ്പറായ 9787872051-ൽ ബന്ധപ്പെടുക."
                )
            return "നിങ്ങൾ അനുഭവിച്ച കാര്യങ്ങൾ പങ്കുവെച്ചതിന് നന്ദി. സാവധാനം പറയൂ, ഞങ്ങൾ നിങ്ങളുടെ കൂടെയുണ്ട്."
        else:
            # English default
            if is_immediate:
                return (
                    "We hear you clearly, and your immediate safety is our utmost priority right now. "
                    "You are in a safe, confidential space. If you are in acute danger or need emergency shelter tonight, "
                    "please reach our dedicated Demo Support at 9787872051. Our priority response team is standing by to coordinate assistance."
                )
            if any(w in lower for w in ["legal", "court", "police", "fir", "rights"]):
                return (
                    "Thank you for sharing this. We understand how overwhelming legal procedures can feel. "
                    "We can coordinate confidential pro-bono legal support and rights advisement under the National Helpline Against Atrocities (NHAA) framework whenever you feel ready."
                )
            if any(w in lower for w in ["anonymous", "privacy", "secret"]):
                return (
                    "Understood completely. Everything you share here is protected with zero-knowledge trauma-informed protocols. "
                    "You are in complete control of what you share and when."
                )
            return (
                "Thank you for trusting us and sharing your experience. We are listening closely, and you can share as much or as little as feels comfortable. "
                "Take all the time you need—we are here to support you."
            )

    def process_message(self, session_id: str, message: str) -> MessageResponse:
        """Synchronous in-memory fallback helper preserved for unit tests."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        if session.get("status") == SessionStatus.SESSION_CREATED:
            self.transition_status(session_id, SessionStatus.ACTIVE)

        reply = self._synthesize_ai_response(message, None, None, session.get("language", "en"))
        msg_id = generate_message_id()
        now_iso = datetime.now(timezone.utc).isoformat()

        session["messages"].append({
            "message_id": msg_id,
            "content": message,
            "sender_type": "VICTIM",
            "input_source": "TEXT",
            "timestamp": now_iso
        })

        return MessageResponse(
            message_id=msg_id,
            response=reply,
            status="received",
            timestamp=now_iso
        )

session_service = SessionService()
