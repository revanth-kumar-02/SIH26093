import enum
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, get_uuid_column, get_foreign_uuid_column, get_uuid_str_column, get_json_type, utc_now

if TYPE_CHECKING:
    from app.db.models.conversation import Conversation
    from app.db.models.ai_signal import AISignal

class MessageSenderType(str, enum.Enum):
    VICTIM = "VICTIM"
    PEOPLE = "PEOPLE"
    RESPONDER = "RESPONDER"
    ADMIN = "ADMIN"
    AI = "AI"
    SYSTEM = "SYSTEM"

class MessageInputSource(str, enum.Enum):
    TEXT = "TEXT"
    VOICE = "VOICE"
    SYSTEM = "SYSTEM"
    AI = "AI"

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = get_uuid_column()
    conversation_id: Mapped[Optional[str]] = get_foreign_uuid_column("conversations.id", nullable=True)
    session_id: Mapped[Optional[str]] = get_uuid_str_column(nullable=True, index=True)
    sender_type: Mapped[MessageSenderType] = mapped_column(
        SAEnum(MessageSenderType, name="message_sender_type", native_enum=False),
        nullable=False
    )
    input_source: Mapped[MessageInputSource] = mapped_column(
        SAEnum(MessageInputSource, name="message_input_source", native_enum=False),
        default=MessageInputSource.TEXT,
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    message_metadata: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    ai_signals: Mapped[List["AISignal"]] = relationship("AISignal", back_populates="message")

    __table_args__ = (
        Index("ix_messages_conv_timestamp", "conversation_id", "timestamp"),
        Index("ix_messages_session_timestamp", "session_id", "timestamp"),
    )
