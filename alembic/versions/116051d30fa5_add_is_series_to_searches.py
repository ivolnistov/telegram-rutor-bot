"""add is_series to searches

Revision ID: 116051d30fa5
Revises: 9de4f0e20117
Create Date: 2026-02-25 19:57:26.955955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '116051d30fa5'
down_revision: Union[str, Sequence[str], None] = '9de4f0e20117'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('searches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_series', sa.Boolean(), server_default='False', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('searches', schema=None) as batch_op:
        batch_op.drop_column('is_series')
