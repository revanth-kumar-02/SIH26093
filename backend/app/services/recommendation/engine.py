from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any, List
from app.services.llm.schemas import TraumaAssessment
from app.services.recommendation.schemas import (
    SupportRecommendationResult,
    SupportRecommendation,
    SupportCategory,
    RecommendationPriority
)
from app.services.recommendation.safety_guard import SafetyGuard

logger = logging.getLogger(__name__)

class SupportRecommendationEngine:
    """Translates structured assessment evidence into actionable support pathways for human responders.
    
    Adheres strictly to the principle of Human-In-The-Loop:
    - Never triggers autonomous police or emergency dispatches.
    - Never diagnoses mental illness.
    - Never maps isolated raw emotions to risk.
    """

    def __init__(self) -> None:
        pass

    def generate_recommendations(
        self,
        session_id: str,
        assessment: TraumaAssessment,
        session_context: Optional[Dict[str, Any]] = None
    ) -> SupportRecommendationResult:
        """Generate support pathways grounded in TraumaAssessment evidence."""
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Evaluate deterministic safety guard
        recommendations, immediate_safety_attention = SafetyGuard.evaluate_safety_and_recommendations(
            session_id=session_id,
            assessment=assessment
        )

        # 2. Inherit uncertainties from Phase 6 assessment
        uncertainties: List[str] = list(assessment.uncertainties) if assessment.uncertainties else []

        # If no recommendations were generated because no distress/safety indicators were detected,
        # note this fact objectively in uncertainties
        if not recommendations:
            uncertainties.append("No active crisis indicators detected in current assessment; routine informational assistance may suffice.")

        # 3. Compile audit metadata
        audit_metadata: Dict[str, Any] = {
            "assessment_model": assessment.model_version,
            "assessment_duration_ms": assessment.duration_ms,
            "indicators_evaluated": len(assessment.indicators),
            "safety_concerns_count": len(assessment.safety_concerns),
            "generated_at": now_iso,
            "session_context_available": bool(session_context)
        }

        return SupportRecommendationResult(
            session_id=session_id,
            recommendations=recommendations,
            immediate_safety_attention=immediate_safety_attention,
            uncertainties=uncertainties,
            responder_review_required=True,
            created_at=now_iso,
            audit_metadata=audit_metadata
        )

recommendation_engine = SupportRecommendationEngine()
