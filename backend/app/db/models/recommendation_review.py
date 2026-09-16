from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, get_uuid_column, get_json_type, utc_now

if TYPE_CHECKING:
    from app.db.models.recommendation import RecommendationModel
    from app.db.models.responder import Responder

class RecommendationReview(Base):
    __tablename__ = "recommendation_reviews"

    id: Mapped[str] = get_uuid_column()
    recommendation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    admin_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("responders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    modified_recommendation: Mapped[Optional[Dict[str, Any]]] = mapped_column(get_json_type(), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    recommendation: Mapped["RecommendationModel"] = relationship("RecommendationModel", back_populates="reviews")
    admin: Mapped[Optional["Responder"]] = relationship("Responder")

    __table_args__ = (
        Index("ix_rec_reviews_rec_decision", "recommendation_id", "decision"),
    )
