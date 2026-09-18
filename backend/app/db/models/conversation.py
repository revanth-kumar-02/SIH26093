from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from app.db.base import Base, get_uuid_column, get_foreign_uuid_column, utc_now

if TYPE_CHECKING:
    from app.db.models.case import Case
    from app.db.models.message import Message
    from app.db.models.ai_signal import AISignal

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = get_uuid_column()
    case_id: Mapped[str] = get_foreign_uuid_column("cases.id")
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    input_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    consent_status: Mapped[str] = mapped_column(String(50), default="CONSENT_GIVEN", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    ai_signals: Mapped[List["AISignal"]] = relationship(
        "AISignal",
        back_populates="conversation",
        cascade="all, delete-orphan",
        primaryjoin="Conversation.session_id == foreign(AISignal.session_id)"
    )

    __table_args__ = (
        Index("ix_conversations_case_session", "case_id", "session_id"),
            )

# Alias Session to Conversation
Session = Conversation
