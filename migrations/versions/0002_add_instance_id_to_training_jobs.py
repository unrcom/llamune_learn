"""add instance_id to training_jobs

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('training_jobs',
        sa.Column('instance_id', sa.String(100), nullable=True),
        schema='learn'
    )


def downgrade() -> None:
    op.drop_column('training_jobs', 'instance_id', schema='learn')
