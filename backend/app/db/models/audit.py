from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, get_uuid_column, get_foreign_uuid_column, get_uuid_str_column, get_json_type, utc_now

if TYPE_CHECKING:
    from app.db.models.case import Case

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = get_uuid_column()
    case_id: Mapped[Optional[str]] = get_foreign_uuid_column("cases.id", nullable=True)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    case: Mapped[Optional["Case"]] = relationship("Case", back_populates="audit_events")

    __table_args__ = (
        Index("ix_audit_events_case_actor_created", "case_id", "actor_id", "created_at"),
    )
