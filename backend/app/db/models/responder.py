import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, get_uuid_column, utc_now

if TYPE_CHECKING:
    from app.db.models.case import Case

class UserRole(str, enum.Enum):
    PEOPLE = "PEOPLE"
    ADMIN = "ADMIN"

class Responder(Base):
    __tablename__ = "responders"

    id: Mapped[str] = get_uuid_column()
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=False),
        default=UserRole.PEOPLE,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=utc_now, 
        onupdate=utc_now, 
        nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    assigned_cases: Mapped[List["Case"]] = relationship(
        "Case", 
        foreign_keys="Case.assigned_responder_id",
        back_populates="assigned_responder"
    )
    owned_cases: Mapped[List["Case"]] = relationship(
        "Case",
        foreign_keys="Case.user_id",
        back_populates="user"
    )

# Alias User to Responder for logical entity requirements
User = Responder
