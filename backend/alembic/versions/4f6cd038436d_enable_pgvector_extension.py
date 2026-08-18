"""enable pgvector extension

Revision ID: 4f6cd038436d
Revises: 06337ce5b6d3
Create Date: 2026-08-18 23:08:47.963177
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4f6cd038436d"
down_revision: Union[str, Sequence[str], None] = "06337ce5b6d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable PostgreSQL pgvector extension."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Disable PostgreSQL pgvector extension."""
    op.execute("DROP EXTENSION IF EXISTS vector")