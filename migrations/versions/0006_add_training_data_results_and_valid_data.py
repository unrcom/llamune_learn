"""add training data results and valid_data table

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('training_data',
        sa.Column('final_loss', sa.Float(), nullable=True),
        schema='learn'
    )
    op.add_column('training_data',
        sa.Column('iterations', sa.Integer(), nullable=True),
        schema='learn'
    )

    op.create_table(
        'valid_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.Integer(), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['log_id'], ['conversation_logs.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        schema='learn',
    )


def downgrade() -> None:
    op.drop_table('valid_data', schema='learn')
    op.drop_column('training_data', 'iterations', schema='learn')
    op.drop_column('training_data', 'final_loss', schema='learn')
