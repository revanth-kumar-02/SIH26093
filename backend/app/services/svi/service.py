import logging
from typing import Dict, Optional
from app.services.svi.schemas import SVIInput, SVIResult
from app.services.svi.engine import svi_engine

logger = logging.getLogger(__name__)

class SVIService:
    """Service managing SVI calculations and session-level storage."""

    def __init__(self) -> None:
        self._session_svi_records: Dict[str, SVIResult] = {}

    def calculate_and_store_svi(self, input_data: SVIInput) -> SVIResult:
        """Calculate SVI result and store in session state for responder review."""
        result = svi_engine.calculate_svi(input_data)
        self._session_svi_records[input_data.session_id] = result
        logger.info(
            f"Calculated SVI for session {input_data.session_id}: "
            f"score={result.score}, risk={result.risk_category.value}, "
            f"immediate_safety={result.immediate_safety_attention}"
        )
        return result

    def get_svi(self, session_id: str) -> Optional[SVIResult]:
        """Retrieve latest SVI result for a session."""
        return self._session_svi_records.get(session_id)

svi_service = SVIService()
