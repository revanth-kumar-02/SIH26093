from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.schemas.emotion import (
    TextAnalysisRequest,
    TextEmotionResult,
    SpeechEmotionResult,
    EmotionSignal,
    MultimodalSessionState
)
from app.services.session_service import session_service
from app.services.emotion.text_emotion_service import text_emotion_service
from app.services.emotion.speech_emotion_service import speech_emotion_service
from app.core.security import generate_message_id

router = APIRouter(prefix="/sessions", tags=["Emotion Analysis"])

@router.post("/{session_id}/analyze/text", response_model=TextEmotionResult)
def analyze_text_emotion(session_id: str, request: TextAnalysisRequest):
    """Analyze text emotion across 28 GoEmotions taxonomy categories."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    try:
        result = text_emotion_service.analyze(request.text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Record internal typed signal in session state
    now_iso = datetime.now(timezone.utc).isoformat()
    signal = EmotionSignal(
        signal_id=generate_message_id(),
        session_id=session_id,
        source="text",
        timestamp=now_iso,
        text_emotion=result,
        metadata={
            "model": result.model_version,
            "latency_ms": result.duration_ms,
            "device": result.device
        }
    )
    session_service.add_emotion_signal(session_id, signal)

    return result

@router.post("/{session_id}/analyze/audio", response_model=SpeechEmotionResult)
async def analyze_speech_emotion(session_id: str, audio: UploadFile = File(...)):
    """Analyze speech emotion across 7 Wav2Vec2 emotion categories."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    audio_bytes = await audio.read()
    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty"
        )

    try:
        result = speech_emotion_service.analyze(audio_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech emotion analysis failed"
        )

    # Record internal typed signal in session state
    now_iso = datetime.now(timezone.utc).isoformat()
    signal = EmotionSignal(
        signal_id=generate_message_id(),
        session_id=session_id,
        source="speech",
        timestamp=now_iso,
        speech_emotion=result,
        metadata={
            "model": result.model_version,
            "latency_ms": result.duration_ms,
            "device": result.device
        }
    )
    session_service.add_emotion_signal(session_id, signal)

    return result

@router.get("/{session_id}/signals", response_model=List[EmotionSignal])
def get_session_signals(session_id: str):
    """Retrieve all structured emotion signals recorded for this session."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session_service.get_emotion_signals(session_id)

@router.get("/{session_id}/multimodal-state", response_model=MultimodalSessionState)
def get_multimodal_state(session_id: str):
    """Retrieve structured session-level representation of all multimodal signals.
    
    Contains:
    - speech_emotion_signals
    - text_emotion_signals
    - stress_signals
    - transcripts
    - input sources and timestamps
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session_service.get_multimodal_state(session_id)
