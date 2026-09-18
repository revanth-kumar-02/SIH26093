from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from app.db.base import Base, get_uuid_column, get_foreign_uuid_column, get_uuid_str_column, get_json_type, utc_now

if TYPE_CHECKING:
    from app.db.models.conversation import Conversation
    from app.db.models.message import Message

class AISignal(Base):
    __tablename__ = "ai_signals"

    id: Mapped[str] = get_uuid_column()
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message_id: Mapped[Optional[str]] = get_foreign_uuid_column("messages.id", nullable=True, ondelete="SET NULL")
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    result: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="ai_signals",
        primaryjoin="foreign(AISignal.session_id) == Conversation.session_id"
    )
    message: Mapped[Optional["Message"]] = relationship("Message", back_populates="ai_signals")

    __table_args__ = (
        Index("ix_ai_signals_session_type", "session_id", "signal_type"),
            )
