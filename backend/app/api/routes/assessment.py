from fastapi import APIRouter, HTTPException, status
from app.schemas.assessment import AssessmentResponse
from app.services.session_service import session_service
from app.services.assessment_service import assessment_service

router = APIRouter(prefix="/sessions", tags=["Assessment"])

@router.post("/{session_id}/assessment", response_model=AssessmentResponse)
def request_assessment(session_id: str):
    """Placeholder assessment endpoint establishing the API contract for Phase 3."""
    if not session_service.get_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return assessment_service.create_assessment_placeholder(session_id=session_id)
