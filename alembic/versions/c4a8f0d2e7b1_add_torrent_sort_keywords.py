"""add torrent_sort_keywords to config

Revision ID: c4a8f0d2e7b1
Revises: 920906cdff50
Create Date: 2026-04-25 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4a8f0d2e7b1'
down_revision: Union[str, Sequence[str], None] = '920906cdff50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('config', schema=None) as batch_op:
        batch_op.add_column(sa.Column('torrent_sort_keywords', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('config', schema=None) as batch_op:
        batch_op.drop_column('torrent_sort_keywords')
