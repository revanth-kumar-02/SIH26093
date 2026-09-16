from typing import List, Dict, Any, Tuple, Set
from app.services.llm.schemas import AssessmentIndicator, EvidenceItem
from app.services.svi.config import (
    FACTOR_WEIGHTS,
    PRESENCE_MULTIPLIERS,
    CORROBORATION_MULTIPLIER,
    RISK_BANDS
)
from app.services.svi.schemas import SVIFactor, RiskCategory
from app.services.svi.factors import FACTOR_METADATA, map_indicators_to_factors

def calculate_svi_factors(
    indicators: List[AssessmentIndicator],
    safety_concerns: List[str],
    observations: List[str]
) -> Tuple[List[SVIFactor], float, RiskCategory, List[str]]:
    """Deterministic mathematical calculation of SVI factors, score, and risk category."""
    grouped_indicators = map_indicators_to_factors(indicators)
    factors: List[SVIFactor] = []

    lower_safety = [sc.lower() for sc in safety_concerns]
    lower_obs = [obs.lower() for obs in observations]

    for factor_id, meta in FACTOR_METADATA.items():
        base_weight = FACTOR_WEIGHTS.get(factor_id, 10.0)
        group_inds = grouped_indicators.get(factor_id, [])

        # Check if safety concerns or observations explicitly reference this factor
        has_safety_ref = False
        if factor_id == "immediate_physical_danger":
            has_safety_ref = any("knife" in s or "kill" in s or "physical" in s or "danger" in s or "weapon" in s for s in lower_safety)
        elif factor_id == "self_harm_crisis":
            has_safety_ref = any("suicid" in s or "self-harm" in s for s in lower_safety + lower_obs)

        if not group_inds and not has_safety_ref:
            factors.append(SVIFactor(
                factor_id=factor_id,
                name=meta["name"],
                group=meta["group"],
                weight=base_weight,
                presence=0.0,
                confidence=0.0,
                evidence_strength=0.0,
                contribution=0.0,
                corroborated=False,
                evidence_sources=[]
            ))
            continue

        # -------------------------------------------------------------
        # Anti-Double Counting & Deduplication Logic
        # -------------------------------------------------------------
        unique_evidence: Dict[str, EvidenceItem] = {}
        all_sources: Set[str] = set()

        for ind in group_inds:
            for ev in ind.evidence:
                norm_key = ev.text.strip().lower()[:60]
                if norm_key not in unique_evidence:
                    unique_evidence[norm_key] = ev
                all_sources.add(ev.source)

        if has_safety_ref and not unique_evidence:
            all_sources.add("text")

        # Distinct source corroboration check
        is_corroborated = len(all_sources) >= 2
        corroboration = CORROBORATION_MULTIPLIER if is_corroborated else 1.0

        # Presence calculation
        if has_safety_ref or any(ind.status == "detected" for ind in group_inds):
            presence = PRESENCE_MULTIPLIERS["detected"]
        elif any(ind.status == "uncertain" for ind in group_inds):
            presence = PRESENCE_MULTIPLIERS["uncertain"]
        else:
            presence = PRESENCE_MULTIPLIERS["not_detected"]

        # Confidence calculation
        if group_inds:
            conf_list = [ind.confidence for ind in group_inds if ind.status in ["detected", "uncertain"]]
            confidence = max(conf_list) if conf_list else 0.5
        elif has_safety_ref:
            confidence = 0.90
        else:
            confidence = 0.0

        # Evidence strength calculation
        if unique_evidence:
            base_strength = min(1.0, 0.85 + (0.08 * max(0, len(unique_evidence) - 1)))
        elif has_safety_ref:
            base_strength = 0.90
        else:
            base_strength = 0.50

        evidence_strength = min(1.0, round(base_strength * corroboration, 3))

        # Mathematical factor contribution
        raw_contrib = base_weight * presence * confidence * evidence_strength
        contribution = round(raw_contrib, 2)

        factors.append(SVIFactor(
            factor_id=factor_id,
            name=meta["name"],
            group=meta["group"],
            weight=base_weight,
            presence=presence,
            confidence=round(confidence, 3),
            evidence_strength=evidence_strength,
            contribution=contribution,
            corroborated=is_corroborated,
            evidence_sources=sorted(list(all_sources))
        ))

    # Calculate raw sum
    raw_sum = sum(f.contribution for f in factors)

    # Normalize to 0-100 bounded scale
    normalized_score = min(100.0, max(0.0, round(raw_sum, 1)))

    # Map to risk band
    risk_category = RiskCategory.LOW
    for band in RISK_BANDS:
        if band["min_score"] <= normalized_score <= band["max_score"]:
            risk_category = RiskCategory(band["category"])
            break

    # Determine key contributing drivers (top positive contributors)
    positive_factors = [f for f in factors if f.contribution > 0.0]
    positive_factors.sort(key=lambda x: x.contribution, reverse=True)
    key_drivers = [f"{f.name} (+{f.contribution} pts)" for f in positive_factors[:3]]

    return factors, normalized_score, risk_category, key_drivers
