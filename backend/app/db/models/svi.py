from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, get_uuid_column, get_foreign_uuid_column, get_uuid_str_column, get_json_type, utc_now

if TYPE_CHECKING:
    from app.db.models.case import Case

class SVIResultModel(Base):
    __tablename__ = "svi_results"

    id: Mapped[str] = get_uuid_column()
    case_id: Mapped[str] = get_foreign_uuid_column("cases.id")
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    svi_version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    factor_contributions: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), nullable=False)
    key_drivers: Mapped[List[str]] = mapped_column(get_json_type(), nullable=False)
    uncertainties: Mapped[List[str]] = mapped_column(get_json_type(), nullable=False)
    immediate_safety_attention: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    urgent_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="svi_results")

    __table_args__ = (
        Index("ix_svi_case_created_risk", "case_id", "created_at", "risk_category"),
        Index("ix_svi_session_created", "session_id", "created_at"),
    )
