from datetime import datetime, timezone
import logging
from typing import List, Tuple, Set
from app.services.llm.schemas import TraumaAssessment, AssessmentIndicator
from app.services.recommendation.schemas import (
    SupportCategory,
    RecommendationPriority,
    SupportRecommendation
)
from app.core.security import generate_message_id

logger = logging.getLogger(__name__)

class SafetyGuard:
    """Deterministic, rule-based safety layer enforcing policy guardrails around recommendations.
    
    Principles:
    1. ZERO AUTONOMOUS DISPATCH: Never automatically contacts police, emergency, or family.
    2. CONTEXTUAL INDICATORS: Does NOT map isolated emotions to risk (fear != police).
    3. MANDATORY HUMAN REVIEW: Sets requires_human_review=True on every pathway.
    """

    @classmethod
    def evaluate_safety_and_recommendations(
        cls,
        session_id: str,
        assessment: TraumaAssessment
    ) -> Tuple[List[SupportRecommendation], bool]:
        """Evaluate assessment indicators and return (recommendations, immediate_safety_attention)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        recommendations: List[SupportRecommendation] = []
        immediate_safety_attention = False

        # Gather detected indicators
        detected_map = {ind.indicator: ind for ind in assessment.indicators if ind.status == "detected"}
        safety_concerns = [sc.lower() for sc in assessment.safety_concerns]
        observations = [obs.lower() for obs in assessment.key_observations]

        # ---------------------------------------------------------
        # 1. Immediate Physical Danger / Active Lethal Threat
        # ---------------------------------------------------------
        has_imminent_danger = (
            "imminent_physical_danger" in detected_map or
            any("knife" in sc or "weapon" in sc or "kill" in sc or "immediate" in sc for sc in safety_concerns)
        )

        if has_imminent_danger:
            immediate_safety_attention = True
            danger_ind = detected_map.get("imminent_physical_danger")
            sources: List[str] = list({ev.source for ev in danger_ind.evidence}) if danger_ind else ["text"]

            # Emergency Support Pathway
            recommendations.append(SupportRecommendation(
                recommendation_id=generate_message_id(),
                session_id=session_id,
                category=SupportCategory.EMERGENCY_SUPPORT,
                recommended=True,
                priority=RecommendationPriority.URGENT,
                reason="The assessment identifies acute threats to immediate physical safety requiring live responder triage.",
                supporting_indicators=["imminent_physical_danger"],
                evidence_sources=sources,
                responder_action="Initiate urgent responder escalation; verify safe immediate physical environment without automating external dispatch.",
                requires_human_review=True,
                created_at=now_iso
            ))

            # Safety Assistance Pathway
            recommendations.append(SupportRecommendation(
                recommendation_id=generate_message_id(),
                session_id=session_id,
                category=SupportCategory.SAFETY_ASSISTANCE,
                recommended=True,
                priority=RecommendationPriority.URGENT,
                reason="Active safety threat necessitates immediate personalized safety planning and secure location coordination.",
                supporting_indicators=["imminent_physical_danger"],
                evidence_sources=sources,
                responder_action="Review immediate exit options and verify discreet emergency contacts with complainant consent.",
                requires_human_review=True,
                created_at=now_iso
            ))

        # ---------------------------------------------------------
        # 2. Self-Harm / Suicidal Ideation Check
        # ---------------------------------------------------------
        has_self_harm = any("suicid" in sc or "self-harm" in sc for sc in safety_concerns + observations)
        if has_self_harm:
            immediate_safety_attention = True
            recommendations.append(SupportRecommendation(
                recommendation_id=generate_message_id(),
                session_id=session_id,
                category=SupportCategory.EMERGENCY_SUPPORT,
                recommended=True,
                priority=RecommendationPriority.URGENT,
                reason="Indications of potential self-harm or acute psychological crisis detected in narrative context.",
                supporting_indicators=["acute_emotional_distress", "self_harm_indications"],
                evidence_sources=["text"],
                responder_action="Connect complainant immediately with a certified crisis/suicide prevention specialist under human responder supervision.",
                requires_human_review=True,
                created_at=now_iso
            ))

        # ---------------------------------------------------------
        # 3. Medical Attention Assistance
        # ---------------------------------------------------------
        has_medical = any(
            any(w in text for w in ["injury", "bleeding", "wound", "hospital", "doctor", "physical assault", "concussion", "poison"])
            for text in observations + safety_concerns
        )
        if has_medical:
            recommendations.append(SupportRecommendation(
                recommendation_id=generate_message_id(),
                session_id=session_id,
                category=SupportCategory.MEDICAL_ASSISTANCE,
                recommended=True,
                priority=RecommendationPriority.IMPORTANT if not immediate_safety_attention else RecommendationPriority.URGENT,
                reason="Complainant narrative indicates physical trauma or injury requiring professional medical evaluation.",
                supporting_indicators=["physical_injury_markers"],
                evidence_sources=["text"],
                responder_action="Offer voluntary referral to accredited forensic medical and trauma care facilities.",
                requires_human_review=True,
                created_at=now_iso
            ))

        # ---------------------------------------------------------
        # 4. Intimidation, Threats & Legal Aid
        # ---------------------------------------------------------
        if "intimidation_and_threats" in detected_map:
            coercion_ind = detected_map["intimidation_and_threats"]
            sources = list({ev.source for ev in coercion_ind.evidence})

            recommendations.append(SupportRecommendation(
                recommendation_id=generate_message_id(),
                session_id=session_id,
                category=SupportCategory.LEGAL_AID,
                recommended=True,
                priority=RecommendationPriority.IMPORTANT,
                reason="Evidence demonstrates coercive control, surveillance, or threats warranting legal rights advisement under NHAA.",
                supporting_indicators=["intimidation_and_threats"],
                evidence_sources=sources,
                responder_action="Provide confidential overview of rights, protection orders, and free legal aid options through NHAA panel lawyers.",
                requires_human_review=True,
                created_at=now_iso
            ))

            # Suggest Police Assistance Review (Strictly Human In The Loop)
            recommendations.append(SupportRecommendation(
                recommendation_id=generate_message_id(),
                session_id=session_id,
                category=SupportCategory.POLICE_ASSISTANCE,
                recommended=True,
                priority=RecommendationPriority.IMPORTANT,
                reason="Pattern of criminal intimidation or harassment documented. Formal police liaison may be considered.",
                supporting_indicators=["intimidation_and_threats"],
                evidence_sources=sources,
                responder_action="Consult complainant on whether they wish to engage special women's police desk; NEVER report without explicit consent.",
                requires_human_review=True,
                created_at=now_iso
            ))

        # ---------------------------------------------------------
        # 5. Social Support & Safe Shelter
        # ---------------------------------------------------------
        if "social_and_material_vulnerability" in detected_map:
            vuln_ind = detected_map["social_and_material_vulnerability"]
            sources = list({ev.source for ev in vuln_ind.evidence})

            recommendations.append(SupportRecommendation(
                recommendation_id=generate_message_id(),
                session_id=session_id,
                category=SupportCategory.SOCIAL_SUPPORT,
                recommended=True,
                priority=RecommendationPriority.IMPORTANT,
                reason="Complainant lacks safe shelter or personal support infrastructure.",
                supporting_indicators=["social_and_material_vulnerability"],
                evidence_sources=sources,
                responder_action="Facilitate connection with verified emergency women's short-stay homes and government social welfare schemes.",
                requires_human_review=True,
                created_at=now_iso
            ))

        # ---------------------------------------------------------
        # 6. Counselling & Emotional Support
        # ---------------------------------------------------------
        if "acute_emotional_distress" in detected_map or "prolonged_sadness" in detected_map:
            distress_ind = detected_map.get("acute_emotional_distress") or detected_map.get("prolonged_sadness")
            sources = list({ev.source for ev in distress_ind.evidence})

            recommendations.append(SupportRecommendation(
                recommendation_id=generate_message_id(),
                session_id=session_id,
                category=SupportCategory.COUNSELLING_SUPPORT,
                recommended=True,
                priority=RecommendationPriority.IMPORTANT if not immediate_safety_attention else RecommendationPriority.ROUTINE,
                reason="Assessment documents substantiated indicators of acute fear or emotional overwhelm requiring trauma-informed psychological first aid.",
                supporting_indicators=[distress_ind.indicator],
                evidence_sources=sources,
                responder_action="Offer voluntary, confidential sessions with a trauma-informed psychologist or helpline counselor.",
                requires_human_review=True,
                created_at=now_iso
            ))

        # De-duplicate categories (keep highest priority if duplicates occur)
        seen_cats: Set[SupportCategory] = set()
        deduped: List[SupportRecommendation] = []
        for r in recommendations:
            if r.category not in seen_cats:
                seen_cats.add(r.category)
                deduped.append(r)

        return deduped, immediate_safety_attention
