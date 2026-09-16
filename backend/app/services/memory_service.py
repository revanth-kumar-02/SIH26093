from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.db.models.case import Case
from app.db.models.conversation import Conversation
from app.db.models.assessment import AssessmentModel
from app.db.models.svi import SVIResultModel
from app.db.models.recommendation import RecommendationModel
from app.db.models.recommendation_review import RecommendationReview
from app.core.config import settings

logger = logging.getLogger(__name__)

class MemoryService:
    """Dedicated Application Memory and Context Service.
    
    Retrieves bounded, structured historical context across prior sessions for a case
    to inform current AI assessment without prompt bloat or authorization leakage.
    """

    async def get_case_for_session(self, db: AsyncSession, session_id: str) -> Optional[Case]:
        """Find the parent case associated with a given session_id."""
        stmt = (
            select(Case)
            .join(Conversation, Conversation.case_id == Case.id)
            .where(Conversation.session_id == session_id)
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def retrieve_bounded_context(
        self,
        db: AsyncSession,
        session_id: str,
        max_words: Optional[int] = None
    ) -> str:
        """Retrieve bounded, structured historical context for the current session.
        
        Extracts:
        - Prior session summaries
        - Prior SVI risk tiers and key drivers
        - Persistent distress/threat indicators
        - Prior human responder reviews & actions
        
        Strictly limits output to max_words (default from settings) to prevent prompt injection or LLM context saturation.
        """
        limit_words = max_words or settings.MEMORY_MAX_CONTEXT_WORDS
        
        # 1. Resolve current conversation & case
        stmt_curr = select(Conversation).where(Conversation.session_id == session_id)
        res_curr = await db.execute(stmt_curr)
        curr_conv = res_curr.scalars().first()
        if not curr_conv:
            return ""

        case_id = curr_conv.case_id

        # 2. Retrieve parent case
        case_stmt = select(Case).where(Case.id == case_id)
        case_res = await db.execute(case_stmt)
        case = case_res.scalars().first()
        if not case:
            return ""

        # 3. Retrieve prior sessions for this case (excluding current)
        prior_sessions_stmt = (
            select(Conversation)
            .where(Conversation.case_id == case_id, Conversation.session_id != session_id)
            .order_by(desc(Conversation.started_at))
            .limit(settings.MEMORY_MAX_PREVIOUS_SESSIONS)
        )
        prior_sessions_res = await db.execute(prior_sessions_stmt)
        prior_sessions = prior_sessions_res.scalars().all()

        if not prior_sessions:
            return ""

        prior_session_ids = [s.session_id for s in prior_sessions]

        # 4. Fetch prior SVI assessments
        svi_stmt = (
            select(SVIResultModel)
            .where(SVIResultModel.case_id == case_id)
            .order_by(desc(SVIResultModel.created_at))
            .limit(settings.MEMORY_MAX_PREVIOUS_SESSIONS)
        )
        svi_res = await db.execute(svi_stmt)
        prior_svi = svi_res.scalars().all()

        # 5. Fetch prior AI assessments (structured indicators)
        assess_stmt = (
            select(AssessmentModel)
            .where(AssessmentModel.case_id == case_id)
            .order_by(desc(AssessmentModel.created_at))
            .limit(settings.MEMORY_MAX_PREVIOUS_SESSIONS)
        )
        assess_res = await db.execute(assess_stmt)
        prior_assess = assess_res.scalars().all()

        # 6. Fetch prior Recommendations & Human Reviews
        rec_stmt = (
            select(RecommendationModel)
            .options(selectinload(RecommendationModel.reviews))
            .where(RecommendationModel.case_id == case_id)
            .order_by(desc(RecommendationModel.created_at))
            .limit(5)
        )
        rec_res = await db.execute(rec_stmt)
        prior_recs = rec_res.scalars().all()

        # Build structured memory summary
        lines: List[str] = [
            f"HISTORICAL CASE MEMORY (PRIOR SESSIONS CONTEXT):",
            f"Case Reference: {case.external_case_reference}",
            f"Prior Sessions Recorded: {len(prior_sessions)}",
        ]

        if prior_svi:
            latest_svi = prior_svi[0]
            lines.append(
                f"- Previous Risk Assessment: Risk Tier={latest_svi.risk_category}, "
                f"SVI Score={latest_svi.score:.1f}, "
                f"Urgent Review={'YES' if latest_svi.urgent_human_review else 'NO'}"
            )
            if latest_svi.key_drivers:
                drivers_str = ", ".join(latest_svi.key_drivers[:3])
                lines.append(f"  Key Vulnerability Drivers: {drivers_str}")

        if prior_assess:
            for pa in prior_assess[:2]:
                payload = pa.assessment_payload or {}
                indicators = payload.get("indicators", [])
                detected = [
                    ind.get("indicator") for ind in indicators 
                    if ind.get("status") == "detected" and ind.get("indicator")
                ]
                if detected:
                    lines.append(f"- Previously Detected Indicators: {', '.join(detected[:4])}")
                
                safety = payload.get("safety_concerns", [])
                if safety:
                    lines.append(f"  Prior Safety Concerns: {'; '.join(safety[:2])}")
                break

        if prior_recs:
            rec_summaries = []
            for r in prior_recs:
                decision = r.responder_decision or r.status
                note = f" (Note: {r.responder_note})" if r.responder_note else ""
                rec_summaries.append(f"{r.category}: {decision}{note}")
            lines.append(f"- Prior Human Reviews: {'; '.join(rec_summaries[:3])}")

        memory_text = "\n".join(lines)
        
        # Check and enforce word bounding
        words = memory_text.split()
        if len(words) > limit_words:
            memory_text = " ".join(words[:limit_words]) + "... [historical memory bounded]"

        return memory_text

memory_service = MemoryService()
