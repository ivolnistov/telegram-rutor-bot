"""add discovery_max_results to config

Revision ID: d8e9f3a1b2c4
Revises: c4a8f0d2e7b1, b3f4a1c2d5e7
Create Date: 2026-04-29 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd8e9f3a1b2c4'
down_revision: str | Sequence[str] | None = ('c4a8f0d2e7b1', 'b3f4a1c2d5e7')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('config', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'discovery_max_results',
                sa.Integer(),
                nullable=False,
                server_default='10',
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('config', schema=None) as batch_op:
        batch_op.drop_column('discovery_max_results')
