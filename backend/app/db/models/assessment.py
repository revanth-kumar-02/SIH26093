from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, get_uuid_column, get_foreign_uuid_column, get_uuid_str_column, get_json_type, utc_now

if TYPE_CHECKING:
    from app.db.models.case import Case

class AssessmentModel(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = get_uuid_column()
    case_id: Mapped[str] = get_foreign_uuid_column("cases.id")
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    assessment_version: Mapped[str] = mapped_column(String(50), default="gemma-3n-e2b-v1.0", nullable=False)
    assessment_payload: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="assessments")

    __table_args__ = (
        Index("ix_assessments_case_created", "case_id", "created_at"),
        Index("ix_assessments_session_created", "session_id", "created_at"),
    )
