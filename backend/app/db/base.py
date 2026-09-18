import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import DateTime, String, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Base declarative class for all SIH26093 database models."""
    pass

# Cross-dialect type helpers
# On PostgreSQL: uses native UUID(as_uuid=True) and JSONB
# On SQLite: uses VARCHAR(36) and JSON
def get_uuid_column():
    return mapped_column(
        String(36).with_variant(PG_UUID(as_uuid=False), "postgresql"),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

def get_foreign_uuid_column(target_table_col: str, nullable: bool = False, index: bool = True, ondelete: str = "CASCADE"):
    from sqlalchemy import ForeignKey
    return mapped_column(
        String(36).with_variant(PG_UUID(as_uuid=False), "postgresql"),
        ForeignKey(target_table_col, ondelete=ondelete),
        nullable=nullable,
        index=index
    )

def get_uuid_str_column(nullable: bool = False, index: bool = True):
    return mapped_column(
        String(64),
        nullable=nullable,
        index=index
    )

def get_json_type():
    return JSON().with_variant(PG_JSONB, "postgresql")

def utc_now() -> datetime:
    return datetime.now(timezone.utc)
