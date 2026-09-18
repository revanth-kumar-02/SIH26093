from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, get_uuid_column, get_foreign_uuid_column, get_uuid_str_column, get_json_type, utc_now

if TYPE_CHECKING:
    from app.db.models.case import Case
    from app.db.models.recommendation_review import RecommendationReview

class RecommendationModel(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = get_uuid_column()
    case_id: Mapped[str] = get_foreign_uuid_column("cases.id")
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_indicators: Mapped[List[str]] = mapped_column(get_json_type(), default=list, nullable=False)
    evidence_sources: Mapped[List[str]] = mapped_column(get_json_type(), default=list, nullable=False)
    responder_action: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    responder_decision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    responder_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="recommendations")
    reviews: Mapped[List["RecommendationReview"]] = relationship("RecommendationReview", back_populates="recommendation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_recommendations_case_status_created", "case_id", "status", "created_at"),
        Index("ix_recommendations_session_created", "session_id", "created_at"),
    )
