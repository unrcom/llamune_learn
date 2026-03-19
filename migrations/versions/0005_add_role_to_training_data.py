"""add role to training_data

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0005'
down_revision: Union[str, Sequence[str], None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('training_data',
        sa.Column('role', sa.SmallInteger(), nullable=False, server_default=sa.text('1')),
        schema='learn'
    )


def downgrade() -> None:
    op.drop_column('training_data', 'role', schema='learn')
