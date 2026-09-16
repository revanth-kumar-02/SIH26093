from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.message import MessageSenderType, MessageInputSource
from app.db.models.conversation import Conversation
from app.schemas.transcription import TranscriptionResponse
from app.schemas.emotion import EmotionSignal, SpeechEmotionResult
from app.schemas.stress import StressSignal, StressDetectionResult
from app.services.session_service import session_service
from app.services.asr.service import asr_service
from app.services.asr.indic_conformer import LANGUAGE_NORMALIZATION
from app.services.emotion.speech_emotion_service import speech_emotion_service
from app.services.stress.service import stress_detection_service
from app.core.security import generate_message_id
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Transcription"])

@router.post("/{session_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    session_id: str,
    audio: UploadFile = File(..., description="Audio recording file (WAV, MP3, AAC, FLAC, M4A)"),
    language: Optional[str] = Form(None, description="Optional language code ('ta', 'hi', 'en', etc.)"),
    decoder: Optional[str] = Form(None, description="Optional decoder strategy ('ctc' or 'rnnt')"),
    db: AsyncSession = Depends(get_db)
):
    """Transcribe uploaded victim audio recording using IndicConformer-600M-Multi.
    
    Multimodal Convergence:
    Audio -> IndicConformer -> Transcript (persisted to DB as VOICE message)
    Audio -> Speech Emotion -> Speech Emotion Signal (persisted to DB)
    Transcript -> Stress Model -> Stress Signal (persisted to DB)
    
    IMPORTANT PRIVACY RULE:
    Raw audio bytes are processed in memory and NOT permanently stored in the database.
    Only the resulting transcript and structured AI signals are persisted.
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

    audio_bytes = await audio.read()
    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty"
        )

    # Determine language and decoder
    raw_lang = language or session.get("language") or "en"
    effective_lang = LANGUAGE_NORMALIZATION.get(raw_lang.strip().lower(), raw_lang.strip().lower())
    effective_decoder = (decoder or settings.ASR_DECODER).lower()

    try:
        transcribed_text = asr_service.transcribe(
            audio_bytes=audio_bytes,
            language=effective_lang,
            decoder=effective_decoder
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"ASR runtime error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech recognition service is currently initializing or unavailable."
        )
    except Exception as e:
        logger.error(f"ASR unexpected transcription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process voice audio at this time"
        )

    now_iso = datetime.now(timezone.utc).isoformat()

    # Persist voice message to DB
    voice_msg_db = None
    try:
        voice_msg_db = await session_service.persist_message(
            db=db,
            session_id=session_id,
            sender_type=MessageSenderType.VICTIM,
            content=transcribed_text,
            input_source=MessageInputSource.VOICE,
            language=effective_lang,
            metadata={"decoder": effective_decoder, "audio_bytes_length": len(audio_bytes)}
        )
    except Exception as pe:
        logger.warning(f"Voice message persistence warning: {pe}")

    # 1. Speech emotion extraction from the in-memory audio bytes
    speech_emotion_result: Optional[SpeechEmotionResult] = None
    try:
        speech_emotion_result = speech_emotion_service.analyze(audio_bytes)
        speech_signal = EmotionSignal(
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
        session_service.add_emotion_signal(session_id, speech_signal)

        # Persist speech emotion signal to DB
        await session_service.persist_ai_signal(
            db=db,
            session_id=session_id,
            message_id=voice_msg_db.id if voice_msg_db else None,
            signal_type="SPEECH_EMOTION",
            result=speech_emotion_result.model_dump(),
            confidence=speech_emotion_result.probabilities.get(speech_emotion_result.emotion, 0.0) if speech_emotion_result and speech_emotion_result.probabilities else 0.0,
            model_name="Dpngtm/wav2vec2-emotion-recognition",
            model_version=speech_emotion_result.model_version
        )
    except Exception as ex:
        logger.warning(f"Speech emotion extraction skipped or failed: {ex}")

    # 2. Stress detection from the resulting ASR transcript
    stress_result: Optional[StressDetectionResult] = None
    if transcribed_text and transcribed_text.strip():
        try:
            stress_result = stress_detection_service.analyze(transcribed_text)
            stress_signal = StressSignal(
                signal_id=generate_message_id(),
                session_id=session_id,
                source="speech",
                timestamp=now_iso,
                stress=stress_result,
                model_version=stress_result.model_version,
                metadata={
                    "latency_ms": stress_result.duration_ms,
                    "device": stress_result.device,
                    "derived_from": "asr_transcript"
                }
            )
            session_service.add_stress_signal(session_id, stress_signal)

            # Persist stress signal to DB
            await session_service.persist_ai_signal(
                db=db,
                session_id=session_id,
                message_id=voice_msg_db.id if voice_msg_db else None,
                signal_type="STRESS",
                result=stress_result.model_dump(),
                confidence=stress_result.score,
                model_name="jtvallente/mentalbert_dreaddit_best",
                model_version=stress_result.model_version
            )
        except Exception as ex:
            logger.warning(f"Stress detection from voice transcript skipped or failed: {ex}")

    msg_id = voice_msg_db.id if voice_msg_db else generate_message_id()

    # Record transcript in session state
    session_service.add_transcript(session_id, {
        "transcript_id": msg_id,
        "text": transcribed_text,
        "language": effective_lang,
        "decoder": effective_decoder,
        "timestamp": now_iso
    })

    return TranscriptionResponse(
        session_id=session_id,
        text=transcribed_text,
        transcript=transcribed_text,
        language=effective_lang,
        decoder=effective_decoder,
        status="completed",
        timestamp=now_iso,
        speech_emotion=speech_emotion_result,
        stress=stress_result
    )
