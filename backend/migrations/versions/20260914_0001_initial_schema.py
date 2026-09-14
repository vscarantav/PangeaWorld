"""Create the complete Phase 4 schema.

Revision ID: 20260914_0001
Revises: None
Create Date: 2026-09-14
"""

from alembic import op

from backend.database import Base
import backend.models  # noqa: F401 - registers every mapped table


revision = "20260914_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The baseline intentionally uses the canonical SQLAlchemy metadata. Future
    # revisions should contain explicit, generated-and-reviewed alterations.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

