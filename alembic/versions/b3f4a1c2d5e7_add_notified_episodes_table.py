"""add notified_episodes table

Revision ID: b3f4a1c2d5e7
Revises: 920906cdff50
Create Date: 2026-03-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f4a1c2d5e7'
down_revision: Union[str, Sequence[str], None] = '920906cdff50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'notified_episodes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('search_id', sa.Integer(), nullable=False),
        sa.Column('film_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('episode', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['film_id'], ['films.id']),
        sa.ForeignKeyConstraint(['search_id'], ['searches.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('search_id', 'film_id', 'season', 'episode', name='uq_notified_episode'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('notified_episodes')
