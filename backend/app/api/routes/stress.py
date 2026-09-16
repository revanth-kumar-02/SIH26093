from datetime import datetime, timezone
import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.stress import StressAnalysisRequest, StressAnalysisResponse, StressSignal
from app.services.session_service import session_service
from app.services.stress.service import stress_detection_service
from app.core.security import generate_message_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Stress Detection"])

@router.post("/{session_id}/analyze/stress", response_model=StressAnalysisResponse)
def analyze_stress(session_id: str, request: StressAnalysisRequest):
    """Analyze text for stress indicators using Dreaddit-trained transformer classifier.
    
    IMPORTANT:
    Stress detection is an internal evidence signal. It is NOT a clinical diagnosis,
    trauma confirmation, depression diagnosis, or emergency escalation trigger.
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    try:
        result = stress_detection_service.analyze(request.text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Stress analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stress analysis failed"
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    signal = StressSignal(
        signal_id=generate_message_id(),
        session_id=session_id,
        source="text",
        timestamp=now_iso,
        stress=result,
        model_version=result.model_version,
        metadata={
            "latency_ms": result.duration_ms,
            "device": result.device
        }
    )
    session_service.add_stress_signal(session_id, signal)

    return StressAnalysisResponse(
        session_id=session_id,
        stress=result,
        status="completed",
        timestamp=now_iso
    )
