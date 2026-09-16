from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.db.seed import seed_database

router = APIRouter(prefix="/demo", tags=["Demo & Presentation"])

DEMO_CASES_MANIFEST = [
    {
        "case_id_tag": "Case A",
        "external_case_reference": "NHAA-2026-SYN-0825",
        "category": "LOW_VULNERABILITY",
        "language": "English (en)",
        "narrative": "Procedural inquiry regarding victim compensation documentation prerequisites.",
        "svi_score": 18.0,
        "risk_category": "LOW",
        "immediate_safety_attention": False,
        "urgent_human_review": False,
        "primary_recommendation": "Informational brochure dissemination.",
        "demonstration_focus": "Baseline query handling with low SVI and minimal intervention.",
        "disclaimer": "DEMO / SYNTHETIC DATA"
    },
    {
        "case_id_tag": "Case B",
        "external_case_reference": "NHAA-2026-SYN-0820",
        "category": "MODERATE_VULNERABILITY",
        "language": "Hindi (hi)",
        "narrative": "Relocation-associated friction and social isolation in an unfamiliar neighborhood.",
        "svi_score": 45.0,
        "risk_category": "MODERATE",
        "immediate_safety_attention": False,
        "urgent_human_review": False,
        "primary_recommendation": "Community navigation and local counselor callback.",
        "demonstration_focus": "Multilingual IndicConformer transcription and community welfare triage.",
        "disclaimer": "DEMO / SYNTHETIC DATA"
    },
    {
        "case_id_tag": "Case C",
        "external_case_reference": "NHAA-2026-SYN-0815",
        "category": "HIGH_VULNERABILITY",
        "language": "English (en)",
        "narrative": "Workplace retaliatory intimidation, economic coercion, and sleep disruption.",
        "svi_score": 72.0,
        "risk_category": "HIGH",
        "immediate_safety_attention": False,
        "urgent_human_review": False,
        "primary_recommendation": "District Legal Services Authority (DLSA) panel advocate referral.",
        "demonstration_focus": "Multi-signal stress/distress correlation and legal pathway recommendation.",
        "disclaimer": "DEMO / SYNTHETIC DATA"
    },
    {
        "case_id_tag": "Case D",
        "external_case_reference": "NHAA-2026-SYN-0812",
        "category": "URGENT_SAFETY_REVIEW",
        "language": "English (en)",
        "narrative": "Active intruder banging on door, forced entry threats, victim hiding in bathroom.",
        "svi_score": 88.5,
        "risk_category": "CRITICAL",
        "immediate_safety_attention": True,
        "urgent_human_review": True,
        "primary_recommendation": "Immediate human emergency desk escalation for local police PCR dispatch.",
        "demonstration_focus": "Immediate safety flag isolation from SVI and urgent human escalation protocol.",
        "disclaimer": "DEMO / SYNTHETIC DATA"
    },
    {
        "case_id_tag": "Case E",
        "external_case_reference": "NHAA-2026-SYN-0830",
        "category": "MULTIPLE_RECOMMENDATIONS",
        "language": "Tamil (ta)",
        "narrative": "In-law harassment and threatened eviction with two dependent minor children.",
        "svi_score": 71.0,
        "risk_category": "HIGH",
        "immediate_safety_attention": False,
        "urgent_human_review": True,
        "primary_recommendation": "Multi-Pathway: Psychological First Aid + Legal Aid + Shelter Coordination.",
        "demonstration_focus": "Complex multi-recommendation triage, review, and modification in Tamil.",
        "disclaimer": "DEMO / SYNTHETIC DATA"
    }
]

@router.get("/cases", response_model=List[Dict[str, Any]])
def get_demo_cases_manifest():
    """Retrieve catalog of 5 synthetic SIH demonstration cases."""
    return DEMO_CASES_MANIFEST

@router.post("/reset")
async def reset_demo_database():
    """Reset and reseed database with the 5 approved synthetic demonstration cases."""
    try:
        await seed_database(force_reset=True)
        return {
            "success": True,
            "message": "Demo database successfully reset with 5 synthetic demonstration cases (Cases A-E).",
            "cases_count": 5,
            "notice": "DEMO / SYNTHETIC DATA - Fictional scenarios only. No real victim data."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset demo database: {str(e)}"
        )
