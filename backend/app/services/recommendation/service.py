from datetime import datetime, timezone
import logging
from typing import Dict, Optional, Any, List
from app.services.llm.schemas import TraumaAssessment
from app.services.recommendation.schemas import (
    SupportRecommendationResult,
    SupportRecommendation,
    RecommendationReviewRequest,
    ReviewStatus
)
from app.services.recommendation.engine import recommendation_engine

logger = logging.getLogger(__name__)

class RecommendationService:
    """Service managing recommendation lifecycles, human responder reviews, and audit trails."""

    def __init__(self) -> None:
        # In-memory storage: session_id -> SupportRecommendationResult
        self._session_recommendations: Dict[str, SupportRecommendationResult] = {}
        # Audit log: list of all review actions taken by responders
        self._audit_trail: List[Dict[str, Any]] = []

    def generate_and_store_recommendations(
        self,
        session_id: str,
        assessment: TraumaAssessment,
        session_context: Optional[Dict[str, Any]] = None
    ) -> SupportRecommendationResult:
        """Generate support recommendations for a session and store for human review."""
        result = recommendation_engine.generate_recommendations(
            session_id=session_id,
            assessment=assessment,
            session_context=session_context
        )
        self._session_recommendations[session_id] = result
        return result

    def get_recommendations(self, session_id: str) -> Optional[SupportRecommendationResult]:
        """Retrieve stored recommendations for a session."""
        return self._session_recommendations.get(session_id)

    def review_recommendation(
        self,
        session_id: str,
        recommendation_id: str,
        review: RecommendationReviewRequest
    ) -> SupportRecommendation:
        """Process human responder decision (accept, modify, reject) on a specific pathway."""
        rec_result = self._session_recommendations.get(session_id)
        if not rec_result:
            raise KeyError(f"No recommendations found for session '{session_id}'")

        target_rec: Optional[SupportRecommendation] = None
        for r in rec_result.recommendations:
            if r.recommendation_id == recommendation_id:
                target_rec = r
                break

        if not target_rec:
            raise KeyError(f"Recommendation '{recommendation_id}' not found in session '{session_id}'")

        now_iso = datetime.now(timezone.utc).isoformat()

        # Update recommendation state
        target_rec.status = ReviewStatus(review.decision)
        target_rec.responder_decision = review.decision
        target_rec.responder_note = review.responder_note
        target_rec.reviewed_at = now_iso

        if review.decision == "modified":
            if review.modified_priority:
                target_rec.priority = review.modified_priority
            if review.modified_action:
                target_rec.responder_action = review.modified_action

        # Record structured audit entry
        audit_entry = {
            "session_id": session_id,
            "recommendation_id": recommendation_id,
            "category": target_rec.category.value,
            "decision": review.decision,
            "responder_note": review.responder_note,
            "reviewed_at": now_iso,
            "priority_after_review": target_rec.priority.value
        }
        self._audit_trail.append(audit_entry)
        logger.info(f"Responder reviewed recommendation {recommendation_id}: decision={review.decision}")

        return target_rec

recommendation_service = RecommendationService()
