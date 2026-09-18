"""persistent_memory_schema

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-09-16 17:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def get_json_type():
    return sa.JSON().with_variant(postgresql.JSONB, "postgresql")

def upgrade() -> None:
    # 1. Update cases table
    with op.batch_alter_table("cases", schema=None) as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(length=36).with_variant(sa.UUID(), "postgresql"), nullable=True))
        batch_op.add_column(sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key("fk_cases_user_id_responders", "responders", ["user_id"], ["id"], ondelete="SET NULL")
        batch_op.create_index("ix_cases_user_status", ["user_id", "status"])

    # 2. Update conversations table
    with op.batch_alter_table("conversations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("consent_status", sa.String(length=50), nullable=False, server_default="CONSENT_GIVEN"))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
        batch_op.create_index("ix_conversations_created_at", ["created_at"])

    # 3. Update messages table
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("language", sa.String(length=10), nullable=False, server_default="en"))
        batch_op.add_column(sa.Column("message_metadata", get_json_type(), nullable=False, server_default="{}"))
        batch_op.create_index("ix_messages_session_timestamp", ["session_id", "timestamp"])

    # 4. Update assessments table
    with op.batch_alter_table("assessments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.String(length=64), nullable=True))
        batch_op.create_index("ix_assessments_session_created", ["session_id", "created_at"])

    # 5. Update svi_results table
    with op.batch_alter_table("svi_results", schema=None) as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.String(length=64), nullable=True))
        batch_op.create_index("ix_svi_session_created", ["session_id", "created_at"])

    # 6. Update recommendations table
    with op.batch_alter_table("recommendations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.String(length=64), nullable=True))
        batch_op.create_index("ix_recommendations_session_created", ["session_id", "created_at"])

    # 7. Create ai_signals table
    op.create_table(
        "ai_signals",
        sa.Column("id", sa.String(length=36).with_variant(sa.UUID(), "postgresql"), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("message_id", sa.String(length=36).with_variant(sa.UUID(), "postgresql"), nullable=True),
        sa.Column("signal_type", sa.String(length=50), nullable=False),
        sa.Column("result", get_json_type(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("model_name", sa.String(length=150), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["conversations.session_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_ai_signals_session_type", "ai_signals", ["session_id", "signal_type"])
    op.create_index("ix_ai_signals_created_at", "ai_signals", ["created_at"])

    # 8. Create recommendation_reviews table
    op.create_table(
        "recommendation_reviews",
        sa.Column("id", sa.String(length=36).with_variant(sa.UUID(), "postgresql"), nullable=False),
        sa.Column("recommendation_id", sa.String(length=36).with_variant(sa.UUID(), "postgresql"), nullable=False),
        sa.Column("admin_id", sa.String(length=36).with_variant(sa.UUID(), "postgresql"), nullable=True),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("modified_recommendation", get_json_type(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admin_id"], ["responders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_rec_reviews_rec_decision", "recommendation_reviews", ["recommendation_id", "decision"])

def downgrade() -> None:
    op.drop_table("recommendation_reviews")
    op.drop_table("ai_signals")

    with op.batch_alter_table("recommendations", schema=None) as batch_op:
        batch_op.drop_index("ix_recommendations_session_created")
        batch_op.drop_column("session_id")

    with op.batch_alter_table("svi_results", schema=None) as batch_op:
        batch_op.drop_index("ix_svi_session_created")
        batch_op.drop_column("session_id")

    with op.batch_alter_table("assessments", schema=None) as batch_op:
        batch_op.drop_index("ix_assessments_session_created")
        batch_op.drop_column("session_id")

    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.drop_index("ix_messages_session_timestamp")
        batch_op.drop_column("message_metadata")
        batch_op.drop_column("language")
        batch_op.drop_column("session_id")

    with op.batch_alter_table("conversations", schema=None) as batch_op:
        batch_op.drop_index("ix_conversations_created_at")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("consent_status")

    with op.batch_alter_table("cases", schema=None) as batch_op:
        batch_op.drop_index("ix_cases_user_status")
        batch_op.drop_constraint("fk_cases_user_id_responders", type_="foreignkey")
        batch_op.drop_column("closed_at")
        batch_op.drop_column("user_id")
