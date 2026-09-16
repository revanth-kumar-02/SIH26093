from app.schemas.assessment import AssessmentResponse, AssessmentResult

class AssessmentService:
    """Placeholder assessment service establishing the API contract for Phase 3.
    
    CRITICAL: Does NOT compute fake SVI scores or pretend a clinical assessment occurred.
    Returns a typed contract with status 'pending_review' and 'not_available' indicators.
    """

    def create_assessment_placeholder(self, session_id: str) -> AssessmentResponse:
        return AssessmentResponse(
            session_id=session_id,
            status="pending_review",
            assessment=AssessmentResult(
                risk_level="not_available",
                svi=None,
                indicators=[]
            )
        )

assessment_service = AssessmentService()
