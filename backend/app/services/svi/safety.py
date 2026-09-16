from typing import List, Tuple
from app.services.llm.schemas import AssessmentIndicator
from app.services.svi.schemas import RiskCategory

class SVISafetyEvaluator:
    """Safety override and urgent attention evaluation layer.
    
    Principles:
    1. Independent from numerical score: Acute lethal danger flags urgent review
       even if numerical score is moderate due to sparse conversational inputs.
    2. Zero autonomous external dispatch: Flags strictly prioritize human triage.
    """

    @classmethod
    def evaluate_safety_flags(
        cls,
        risk_category: RiskCategory,
        indicators: List[AssessmentIndicator],
        safety_concerns: List[str]
    ) -> Tuple[bool, bool]:
        """Evaluate (immediate_safety_attention, urgent_human_review)."""
        lower_sc = [sc.lower() for sc in safety_concerns]

        # 1. Immediate Physical Danger
        has_immediate_danger = any(
            ind.indicator == "imminent_physical_danger" and ind.status == "detected"
            for ind in indicators
        ) or any("knife" in s or "kill" in s or "weapon" in s or "right outside" in s for s in lower_sc)

        # 2. Self-Harm / Crisis Concern
        has_self_harm = any(
            ind.indicator in ["self_harm_indications", "suicidal_ideation_indicators"] and ind.status == "detected"
            for ind in indicators
        ) or any("suicid" in s or "self-harm" in s for s in lower_sc)

        immediate_safety_attention = bool(has_immediate_danger or has_self_harm)

        # Urgent human review is required if immediate safety attention is flagged
        # or if the overall SVI risk tier is CRITICAL
        urgent_human_review = bool(
            immediate_safety_attention or
            risk_category == RiskCategory.CRITICAL
        )

        return immediate_safety_attention, urgent_human_review
