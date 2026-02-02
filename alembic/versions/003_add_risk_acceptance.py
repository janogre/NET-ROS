"""Add risk acceptance fields

Revision ID: 003
Revises: 002
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add risk acceptance fields
    # Note: SQLite doesn't support adding FK constraints after table creation,
    # so we skip the FK constraint. The model will still enforce referential integrity.
    op.add_column('risks', sa.Column('accepted_by_id', sa.Integer(), nullable=True))
    op.add_column('risks', sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('risks', sa.Column('acceptance_rationale', sa.Text(), nullable=True))
    op.add_column('risks', sa.Column('acceptance_valid_until', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('risks', 'acceptance_valid_until')
    op.drop_column('risks', 'acceptance_rationale')
    op.drop_column('risks', 'accepted_at')
    op.drop_column('risks', 'accepted_by_id')
