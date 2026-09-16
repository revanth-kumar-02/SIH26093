"""rbac_two_roles_people_admin

Revision ID: e7f8a9b0c1d2
Revises: dbe85f4987b4
Create Date: 2026-09-16 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, Sequence[str], None] = 'dbe85f4987b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Migrate any legacy role entries to ADMIN before constraining
    op.execute("UPDATE responders SET role = 'ADMIN' WHERE role IN ('RESPONDER', 'SUPERVISOR');")
    op.execute("UPDATE audit_events SET actor_type = 'ADMIN' WHERE actor_type IN ('RESPONDER', 'SUPERVISOR');")

def downgrade() -> None:
    # Revert if needed
    op.execute("UPDATE responders SET role = 'RESPONDER' WHERE role = 'PEOPLE';")
