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
from app.core.security import generate_message_id

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

        # 3. Baseline guarantee: when distress or safety indicators are detected,
        #    ensure at minimum a routine Counselling Support recommendation for human responder awareness.
        has_detected_indicators = any(
            getattr(ind, "status", None) == "detected" for ind in assessment.indicators
        ) or bool(assessment.safety_concerns)

        has_counselling = any(
            r.category == SupportCategory.COUNSELLING_SUPPORT for r in recommendations
        )
        if has_detected_indicators and not has_counselling:
            recommendations.append(SupportRecommendation(
                recommendation_id=generate_message_id(),
                session_id=session_id,
                category=SupportCategory.COUNSELLING_SUPPORT,
                recommended=True,
                priority=RecommendationPriority.ROUTINE,
                reason=(
                    "Baseline counselling awareness pathway. The individual has voluntarily engaged the "
                    "support system. A human responder should ensure follow-up access to trauma-informed "
                    "counselling resources is offered, even if no acute crisis is currently detected."
                ),
                supporting_indicators=[],
                evidence_sources=["text"],
                responder_action=(
                    "Offer voluntary, confidential access to trauma-informed counselling or helpline "
                    "services. Record whether the individual wishes to be contacted for follow-up."
                ),
                requires_human_review=True,
                created_at=now_iso
            ))

        # If no recommendations were generated because no distress/safety indicators were detected,
        # note this fact objectively in uncertainties
        if not recommendations:
            uncertainties.append("No active crisis indicators detected in current assessment; routine informational assistance may suffice.")


        # 4. Compile audit metadata
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
