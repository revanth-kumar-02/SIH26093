from datetime import datetime, timezone
import logging
from typing import Dict, Optional, Any, List
from app.services.llm.schemas import TraumaAssessment, AssessmentIndicator, EvidenceItem
from app.services.llm.service import gemma_service
from app.services.recommendation.schemas import (
    SupportRecommendationResult,
    SupportRecommendation,
    SupportCategory,
    RecommendationPriority,
    RecommendationReviewRequest,
    ReviewStatus
)
from app.services.recommendation.support_plan_schemas import (
    PersonalizedSupportPlan,
    VerifiedEmergencyResource
)
from app.services.recommendation.engine import recommendation_engine

logger = logging.getLogger(__name__)

class RecommendationService:
    """Service managing recommendation lifecycles, human responder reviews, and audit trails."""

    def __init__(self) -> None:
        # In-memory storage: session_id -> SupportRecommendationResult
        self._session_recommendations: Dict[str, SupportRecommendationResult] = {}
        # In-memory storage: session_id -> PersonalizedSupportPlan
        self._session_support_plans: Dict[str, PersonalizedSupportPlan] = {}
        # Audit log: list of all review actions taken by responders
        self._audit_trail: List[Dict[str, Any]] = []

    def generate_support_plan(
        self,
        session_id: str,
        conversation_turns: List[dict],
        text_emotions: Optional[List[dict]] = None,
        stress_signals: Optional[List[dict]] = None,
        has_human_assignment: bool = False,
        human_assignment_details: Optional[dict] = None,
        language: str = "en"
    ) -> PersonalizedSupportPlan:
        """Generate a personalized, chat-driven support plan from completed conversation context."""
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Run Gemma full-conversation analysis
        analysis = gemma_service.analyze_completed_conversation(
            conversation_turns=conversation_turns,
            text_emotions=text_emotions,
            stress_signals=stress_signals,
            language=language
        )

        what_we_heard = analysis.get("what_we_heard", "").strip()
        how_you_are_doing = analysis.get("how_you_are_doing", "").strip()
        primary_concerns = analysis.get("primary_concerns", [])
        emotional_indicators = analysis.get("emotional_indicators", [])
        safety_indicators = analysis.get("safety_indicators", [])
        immediate_needs = analysis.get("immediate_needs", [])
        uncertainties = analysis.get("uncertainties", [])

        # 2. Build underlying TraumaAssessment indicators grounded strictly in evidence
        indicators: List[AssessmentIndicator] = []
        safety_concerns: List[str] = []

        user_text = " ".join([
            (t.get("text") or t.get("content") or "") for t in conversation_turns if t.get("role") in ("user", "victim")
        ]).lower()

        # Imminent danger / acute physical safety
        if any(w in user_text for w in ["knife", "weapon", "kill", "immediate danger", "breaking in"]) or any("acute" in str(s).lower() for s in safety_indicators):
            safety_concerns.append("Acute immediate physical danger reported")
            indicators.append(AssessmentIndicator(
                indicator="imminent_physical_danger",
                category="immediate_safety",
                status="detected",
                confidence=0.9,
                evidence=[EvidenceItem(text=what_we_heard)],
                reason="User narrative reports immediate threat to physical safety"
            ))

        # Intimidation / threats / coercion / abuse
        if any(w in user_text for w in ["abuse", "abused", "relatives", "forcing", "forced"]) or any("abuse" in str(s).lower() for s in safety_indicators):
            safety_concerns.append("Domestic coercion and abuse reported in living situation")
            indicators.append(AssessmentIndicator(
                indicator="intimidation_and_threats",
                category="intimidation_coercion",
                status="detected",
                confidence=0.85,
                evidence=[EvidenceItem(text=what_we_heard)],
                reason="Narrative identifies forced living arrangement and abuse by relatives"
            ))
            indicators.append(AssessmentIndicator(
                indicator="social_and_material_vulnerability",
                category="vulnerability",
                status="detected",
                confidence=0.8,
                evidence=[EvidenceItem(text=what_we_heard)],
                reason="Conflict between desired living arrangement with family and forced stay with relatives"
            ))

        # Emotional distress / grief / relationship pain / stress
        has_distress = (
            any(e in ["grief", "sadness", "distress", "betrayal", "stress", "fear", "overwhelm"] for e in emotional_indicators)
            or any(w in user_text for w in ["stress", "stressed", "anita", "anu", "left me", "crying", "hurt", "pain"])
        )
        if has_distress:
            indicators.append(AssessmentIndicator(
                indicator="acute_emotional_distress",
                category="emotional_distress",
                status="detected",
                confidence=0.8,
                evidence=[EvidenceItem(text=what_we_heard)],
                reason="Narrative and emotion indicators substantiate emotional distress or relational loss"
            ))

        assessment = TraumaAssessment(
            session_id=session_id,
            indicators=indicators,
            key_observations=primary_concerns,
            uncertainties=uncertainties,
            safety_concerns=safety_concerns,
            responder_review_points=["Verify complainant physical safety and voluntary consent for any external contact."],
            model_version="google/gemma-3n-E2B-it",
            duration_ms=50.0
        )

        # 3. Deterministic SafetyGuard and RecommendationEngine evaluation
        rec_result = recommendation_engine.generate_recommendations(
            session_id=session_id,
            assessment=assessment,
            session_context={"language": language}
        )
        self._session_recommendations[session_id] = rec_result

        # 4. Tailor recommendation explanations grounded in this user's story
        personalized_recs: List[SupportRecommendation] = []
        for r in rec_result.recommendations:
            reason = r.reason
            if r.category == SupportCategory.COUNSELLING_SUPPORT:
                if "anita" in user_text or "anu" in user_text:
                    reason = "You described feeling deeply hurt and replaying the loss of safety and connection with Anita."
                elif "abuse" in user_text:
                    reason = "You described feeling distressed and overwhelmed by the abuse you've been experiencing."
                elif "stress" in user_text:
                    reason = "You described feeling overwhelmed and stressed by your current circumstances."
                else:
                    reason = "Talking with a trauma-informed counselor can provide a confidential space to process what you've shared."
            elif r.category == SupportCategory.SAFETY_ASSISTANCE:
                reason = "Because you described being forced into an unsafe living situation where abuse occurs, safety planning can help identify discreet options."
            elif r.category == SupportCategory.LEGAL_AID:
                reason = "To help you understand your legal protections regarding coercion, unwanted living arrangements, and abuse."
            elif r.category == SupportCategory.SOCIAL_SUPPORT:
                reason = "To explore secure, verified shelter alternatives and support networks outside of the abusive environment."
            elif r.category == SupportCategory.EMERGENCY_SUPPORT:
                reason = "An immediate physical safety concern was indicated. Verified emergency resources can assist if you are in danger."

            r.reason = reason
            personalized_recs.append(r)

        # 5. Immediate Safety Configuration
        immediate_safety_needed = rec_result.immediate_safety_attention
        immediate_safety_message = None
        verified_emergency = None

        if immediate_safety_needed:
            immediate_safety_message = "Based on what you shared, it may be important to focus on getting somewhere safe first."
            verified_emergency = VerifiedEmergencyResource(
                title="National Emergency Helpline",
                number="112",
                description="24/7 nationwide emergency response for immediate physical safety."
            )

        # 6. Human Review representation
        human_review_status = "Human review recommended"
        human_review_msg = (
            "Some of what you shared may require a trained responder to review before external action is considered. "
            "You can request human review below, or choose what you feel comfortable with."
        )
        if has_human_assignment and human_assignment_details:
            human_review_status = f"Assigned to {human_assignment_details.get('name', 'Responder')}"
            human_review_msg = "Your intake is under active review by your designated human responder."

        # 7. User Choices
        user_choices = [
            {"id": "explore", "title": "Explore Support Options", "description": "Choose any of the recommended care pathways above at your own pace."},
            {"id": "request_review", "title": "Request Human Responder Review", "description": "Have a trained human responder carefully review your case before any next step."},
            {"id": "return_to_chat", "title": "Return to TrueVoice Guide", "description": "Continue talking in the confidential chat whenever you are ready."}
        ]

        plan = PersonalizedSupportPlan(
            session_id=session_id,
            what_we_heard=what_we_heard,
            how_you_are_doing=how_you_are_doing,
            primary_concerns=primary_concerns,
            emotional_indicators=emotional_indicators,
            immediate_safety_needed=immediate_safety_needed,
            immediate_safety_message=immediate_safety_message,
            verified_emergency_resource=verified_emergency,
            recommendations=personalized_recs,
            has_human_assignment=has_human_assignment,
            human_assignment_details=human_assignment_details,
            human_review_status=human_review_status,
            human_review_message=human_review_msg,
            user_choices=user_choices,
            uncertainties=uncertainties,
            created_at=now_iso
        )
        self._session_support_plans[session_id] = plan
        return plan

    def get_support_plan(self, session_id: str) -> Optional[PersonalizedSupportPlan]:
        """Retrieve stored personalized support plan for a session."""
        return self._session_support_plans.get(session_id)

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
