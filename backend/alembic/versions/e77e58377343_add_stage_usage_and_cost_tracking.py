"""add stage usage and cost tracking

Revision ID: e77e58377343
Revises: 545c3ea24e48
Create Date: 2026-08-20 21:01:05.601058
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e77e58377343"
down_revision: Union[str, Sequence[str], None] = "545c3ea24e48"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Existing stage_runs rows require nullable columns initially.
    op.add_column(
        "stage_runs",
        sa.Column(
            "duration_ms",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "stage_runs",
        sa.Column(
            "input_tokens",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "stage_runs",
        sa.Column(
            "output_tokens",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "stage_runs",
        sa.Column(
            "total_tokens",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "stage_runs",
        sa.Column(
            "estimated_cost_usd",
            sa.Numeric(
                precision=12,
                scale=8,
            ),
            nullable=True,
        ),
    )

    # Backfill existing rows.
    op.execute(
        """
        UPDATE stage_runs
        SET
            input_tokens = 0,
            output_tokens = 0,
            total_tokens = 0,
            estimated_cost_usd = 0
        """
    )

    # Enforce NOT NULL after backfilling existing records.
    op.alter_column(
        "stage_runs",
        "input_tokens",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "stage_runs",
        "output_tokens",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "stage_runs",
        "total_tokens",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "stage_runs",
        "estimated_cost_usd",
        existing_type=sa.Numeric(
            precision=12,
            scale=8,
        ),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "stage_runs",
        "estimated_cost_usd",
    )

    op.drop_column(
        "stage_runs",
        "total_tokens",
    )

    op.drop_column(
        "stage_runs",
        "output_tokens",
    )

    op.drop_column(
        "stage_runs",
        "input_tokens",
    )

    op.drop_column(
        "stage_runs",
        "duration_ms",
    )