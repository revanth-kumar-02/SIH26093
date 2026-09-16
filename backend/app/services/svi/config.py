"""
Versioned Scoring Configuration for Stress Vulnerability Index (SVI).

CRITICAL DOMAIN DISCLAIMER:
    The SVI scoring model and risk triage thresholds defined herein are prototype
    engineering rubrics designed to assist human helpline responders in prioritizing
    review workflows.
    They are NOT clinically, medically, psychiatrically, or forensically validated.
    They must NEVER be used to make autonomous legal, medical, or emergency decisions.
"""

from typing import Dict, Any, List

SVI_CONFIG_VERSION = "v1.0"

# Factor baseline weights across 6 vulnerability groups (calibrated to 0-100 triage scale)
FACTOR_WEIGHTS: Dict[str, float] = {
    # Group A: Emotional Distress
    "emotional_distress": 20.0,
    # Group B: Threat / Intimidation / Coercion
    "threats_intimidation": 35.0,
    # Group C: Immediate Physical Safety
    "immediate_physical_danger": 35.0,
    # Group D: Self-Harm / Acute Crisis
    "self_harm_crisis": 25.0,
    # Group E: Social Vulnerability & Isolation
    "social_vulnerability": 20.0,
    # Group F: Communication Vulnerability (strictly capped; never proof of trauma)
    "communication_vulnerability": 5.0,
}

# Presence multipliers based on indicator status
PRESENCE_MULTIPLIERS: Dict[str, float] = {
    "detected": 1.0,
    "uncertain": 0.35,
    "not_detected": 0.0,
}

# Cross-modal corroboration bonus (e.g. text + speech or text + stress)
CORROBORATION_MULTIPLIER = 1.15

# Risk Category Bands
RISK_BANDS: List[Dict[str, Any]] = [
    {
        "category": "LOW",
        "min_score": 0.0,
        "max_score": 29.9,
        "description": "Routine vulnerability indicators. Standard empathetic support and informational resources appropriate."
    },
    {
        "category": "MODERATE",
        "min_score": 30.0,
        "max_score": 59.9,
        "description": "Noticeable emotional distress, material vulnerability, or recurring conflict. Scheduled responder follow-up recommended."
    },
    {
        "category": "HIGH",
        "min_score": 60.0,
        "max_score": 84.9,
        "description": "Substantial coercion, threats, acute emotional overwhelm, or acute isolation. Prioritized human responder review required."
    },
    {
        "category": "CRITICAL",
        "min_score": 85.0,
        "max_score": 100.0,
        "description": "Acute compound threats, imminent physical danger, or acute crisis indicators. Immediate live responder triage required."
    }
]

def get_svi_configuration() -> Dict[str, Any]:
    """Retrieve full versioned scoring configuration dictionary for audit logs."""
    return {
        "version": SVI_CONFIG_VERSION,
        "weights": FACTOR_WEIGHTS,
        "presence_multipliers": PRESENCE_MULTIPLIERS,
        "corroboration_multiplier": CORROBORATION_MULTIPLIER,
        "bands": RISK_BANDS,
        "clinical_validation": False,
        "classification_type": "prototype_engineering_triage"
    }
