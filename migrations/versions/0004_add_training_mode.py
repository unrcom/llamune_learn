"""add training_mode to training_jobs

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('training_jobs',
        sa.Column('training_mode', sa.SmallInteger(), nullable=False, server_default=sa.text('1')),
        schema='learn'
    )
    op.add_column('training_jobs',
        sa.Column('loss_threshold', sa.Float(), nullable=True),
        schema='learn'
    )


def downgrade() -> None:
    op.drop_column('training_jobs', 'loss_threshold', schema='learn')
    op.drop_column('training_jobs', 'training_mode', schema='learn')
