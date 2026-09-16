"""
Factor definitions and mapping logic from Assessment Indicators to SVI Vulnerability Factors.
"""

from typing import Dict, List, Set, Tuple
from app.services.llm.schemas import AssessmentIndicator
from app.services.svi.config import FACTOR_WEIGHTS

FACTOR_METADATA = {
    "emotional_distress": {
        "name": "Emotional Distress & Fear",
        "group": "A: Emotional Distress",
        "indicator_keys": ["acute_emotional_distress", "prolonged_sadness", "severe_fear", "hopelessness", "emotional_overwhelm"],
    },
    "threats_intimidation": {
        "name": "Threats, Coercion & Intimidation",
        "group": "B: Threat / Intimidation",
        "indicator_keys": ["intimidation_and_threats", "coercion", "stalking", "fear_of_retaliation", "controlled_communication"],
    },
    "immediate_physical_danger": {
        "name": "Immediate Physical Safety",
        "group": "C: Immediate Safety",
        "indicator_keys": ["imminent_physical_danger", "inability_to_remain_safe", "acute_safety_concern"],
    },
    "self_harm_crisis": {
        "name": "Self-Harm & Acute Psychological Crisis",
        "group": "D: Self-Harm / Crisis",
        "indicator_keys": ["self_harm_indications", "suicidal_ideation_indicators", "severe_crisis_indicators"],
    },
    "social_vulnerability": {
        "name": "Social Isolation & Shelter Deprivation",
        "group": "E: Social Vulnerability",
        "indicator_keys": ["social_and_material_vulnerability", "shelter_deprivation", "social_isolation", "lack_of_support", "dependency"],
    },
    "communication_vulnerability": {
        "name": "Communication Hesitation / Fragmentation",
        "group": "F: Communication Vulnerability",
        "indicator_keys": ["fragmented_or_hesitant_communication", "severe_communication_difficulty", "inability_to_communicate_safely"],
    }
}

def map_indicators_to_factors(indicators: List[AssessmentIndicator]) -> Dict[str, List[AssessmentIndicator]]:
    """Group incoming indicators under their corresponding SVI factor."""
    grouped: Dict[str, List[AssessmentIndicator]] = {f_id: [] for f_id in FACTOR_METADATA}

    for ind in indicators:
        matched = False
        for f_id, meta in FACTOR_METADATA.items():
            if ind.indicator in meta["indicator_keys"]:
                grouped[f_id].append(ind)
                matched = True
                break
        if not matched:
            # Fallback mapping based on indicator category
            if ind.category == "emotional_distress":
                grouped["emotional_distress"].append(ind)
            elif ind.category == "intimidation_coercion":
                grouped["threats_intimidation"].append(ind)
            elif ind.category == "immediate_safety":
                grouped["immediate_physical_danger"].append(ind)
            elif ind.category == "vulnerability":
                grouped["social_vulnerability"].append(ind)
            elif ind.category == "communication_difficulty":
                grouped["communication_vulnerability"].append(ind)

    return grouped
