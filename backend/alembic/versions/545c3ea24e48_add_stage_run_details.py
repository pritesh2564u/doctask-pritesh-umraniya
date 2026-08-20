from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "545c3ea24e48"
down_revision: Union[str, Sequence[str], None] = "26ce4a4b15fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "stage_runs",
        sa.Column("message", sa.Text(), nullable=True),
    )

    op.add_column(
        "stage_runs",
        sa.Column("details", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("stage_runs", "details")
    op.drop_column("stage_runs", "message")
