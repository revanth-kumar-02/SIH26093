import time
from datetime import datetime, timezone
import logging
from typing import Dict, Any, List
from app.services.svi.schemas import SVIInput, SVIResult
from app.services.svi.config import SVI_CONFIG_VERSION, get_svi_configuration
from app.services.svi.scoring import calculate_svi_factors
from app.services.svi.safety import SVISafetyEvaluator

logger = logging.getLogger(__name__)

class SVIEngine:
    """Stress Vulnerability Index calculation engine.
    
    Guarantees:
    - 100% Determinism: same input + same configuration = exact same SVI score.
    - Full explainability: factor contributions, key drivers, and evidence sources.
    - Anti-double counting and cross-modal corroboration tracking.
    - Zero autonomous external dispatches.
    """

    def calculate_svi(self, input_data: SVIInput) -> SVIResult:
        """Calculate SVI score and categorical risk triage tier."""
        start_time = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Extract indicators from assessment or explicit list
        if input_data.assessment is not None:
            indicators = input_data.assessment.indicators
            safety_concerns = input_data.assessment.safety_concerns
            observations = input_data.assessment.key_observations
            uncertainties = list(input_data.assessment.uncertainties)
        else:
            indicators = input_data.indicators
            safety_concerns = input_data.safety_concerns
            observations = input_data.observations
            uncertainties = list(input_data.uncertainties)

        # 1. Deterministic mathematical factor calculation
        factors, score, risk_cat, key_drivers = calculate_svi_factors(
            indicators=indicators,
            safety_concerns=safety_concerns,
            observations=observations
        )

        # 2. Safety override & urgent review evaluation
        imm_safety, urgent_review = SVISafetyEvaluator.evaluate_safety_flags(
            risk_category=risk_cat,
            indicators=indicators,
            safety_concerns=safety_concerns
        )

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        audit_metadata: Dict[str, Any] = {
            "config_version": SVI_CONFIG_VERSION,
            "calculation_duration_ms": duration_ms,
            "total_indicators_evaluated": len(indicators),
            "safety_concerns_count": len(safety_concerns),
            "has_multimodal_assessment": input_data.assessment is not None,
            "scoring_parameters": get_svi_configuration()
        }

        return SVIResult(
            svi_version=SVI_CONFIG_VERSION,
            session_id=input_data.session_id,
            score=score,
            risk_category=risk_cat,
            factor_contributions=factors,
            key_drivers=key_drivers,
            uncertainties=uncertainties,
            immediate_safety_attention=imm_safety,
            urgent_human_review=urgent_review,
            requires_human_review=True,
            calculation_timestamp=now_iso,
            audit_metadata=audit_metadata
        )

svi_engine = SVIEngine()
