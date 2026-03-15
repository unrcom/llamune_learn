"""add training params to training_jobs

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('training_jobs', sa.Column('iters', sa.Integer(), nullable=False, server_default=sa.text('1000')), schema='learn')
    op.add_column('training_jobs', sa.Column('batch_size', sa.Integer(), nullable=False, server_default=sa.text('4')), schema='learn')
    op.add_column('training_jobs', sa.Column('learning_rate', sa.Float(), nullable=False, server_default=sa.text('0.00001')), schema='learn')
    op.add_column('training_jobs', sa.Column('num_layers', sa.Integer(), nullable=False, server_default=sa.text('16')), schema='learn')
    op.add_column('training_jobs', sa.Column('max_seq_length', sa.Integer(), nullable=False, server_default=sa.text('2048')), schema='learn')


def downgrade() -> None:
    op.drop_column('training_jobs', 'max_seq_length', schema='learn')
    op.drop_column('training_jobs', 'num_layers', schema='learn')
    op.drop_column('training_jobs', 'learning_rate', schema='learn')
    op.drop_column('training_jobs', 'batch_size', schema='learn')
    op.drop_column('training_jobs', 'iters', schema='learn')
