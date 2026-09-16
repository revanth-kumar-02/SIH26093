import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, get_uuid_column, utc_now

if TYPE_CHECKING:
    from app.db.models.responder import Responder
    from app.db.models.conversation import Conversation
    from app.db.models.assessment import AssessmentModel
    from app.db.models.svi import SVIResultModel
    from app.db.models.recommendation import RecommendationModel
    from app.db.models.audit import AuditEvent

class CaseStatus(str, enum.Enum):
    NEW = "NEW"
    IN_REVIEW = "IN_REVIEW"
    AWAITING_RESPONDER_ACTION = "AWAITING_RESPONDER_ACTION"
    ACTION_RECORDED = "ACTION_RECORDED"
    CLOSED = "CLOSED"

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = get_uuid_column()
    external_case_reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        SAEnum(CaseStatus, name="case_status", native_enum=False),
        default=CaseStatus.NEW,
        nullable=False,
        index=True
    )
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    consent_status: Mapped[str] = mapped_column(String(50), default="CONSENT_GIVEN", nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("responders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    assigned_responder_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("responders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional["Responder"]] = relationship(
        "Responder",
        foreign_keys=[user_id],
        back_populates="owned_cases"
    )
    assigned_responder: Mapped[Optional["Responder"]] = relationship(
        "Responder",
        foreign_keys=[assigned_responder_id],
        back_populates="assigned_cases"
    )
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="case", cascade="all, delete-orphan")
    assessments: Mapped[List["AssessmentModel"]] = relationship("AssessmentModel", back_populates="case", cascade="all, delete-orphan")
    svi_results: Mapped[List["SVIResultModel"]] = relationship("SVIResultModel", back_populates="case", cascade="all, delete-orphan")
    recommendations: Mapped[List["RecommendationModel"]] = relationship("RecommendationModel", back_populates="case", cascade="all, delete-orphan")
    audit_events: Mapped[List["AuditEvent"]] = relationship("AuditEvent", back_populates="case", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_cases_status_created_at", "status", "created_at"),
        Index("ix_cases_user_status", "user_id", "status"),
    )
