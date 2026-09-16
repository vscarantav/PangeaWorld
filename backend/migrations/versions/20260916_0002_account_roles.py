"""Add installation account roles and persistent session ownership.

Revision ID: 20260916_0002
Revises: 20260914_0001
"""

from alembic import op
import sqlalchemy as sa


revision = "20260916_0002"
down_revision = "20260914_0001"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if "account_type" not in _columns("users"):
        op.add_column("users", sa.Column("account_type", sa.String(), nullable=False, server_default="student"))
    if "managed_by_user_id" not in _columns("users"):
        op.add_column("users", sa.Column("managed_by_user_id", sa.Integer(), nullable=True))
    if "owner_user_id" not in _columns("game_sessions"):
        op.add_column("game_sessions", sa.Column("owner_user_id", sa.Integer(), nullable=True))

    op.execute("UPDATE users SET account_type = 'professor' WHERE is_instructor = 1 AND account_type = 'student'")
    op.execute("UPDATE users SET account_type = 'admin' WHERE id = (SELECT MIN(id) FROM users)")
    op.execute("UPDATE users SET is_instructor = 1 WHERE account_type IN ('admin', 'professor')")
    op.execute(
        "UPDATE game_sessions SET owner_user_id = ("
        "SELECT user_id FROM game_memberships WHERE game_memberships.session_id = game_sessions.id "
        "AND role = 'instructor' ORDER BY id LIMIT 1) WHERE owner_user_id IS NULL"
    )


def downgrade() -> None:
    if "owner_user_id" in _columns("game_sessions"):
        op.drop_column("game_sessions", "owner_user_id")
    if "account_type" in _columns("users"):
        op.drop_column("users", "account_type")
    if "managed_by_user_id" in _columns("users"):
        op.drop_column("users", "managed_by_user_id")
