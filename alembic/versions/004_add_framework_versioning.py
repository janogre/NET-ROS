"""Add framework versioning fields

Revision ID: 004
Revises: 003
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add versioning fields to NSM principles
    op.add_column('nsm_principles', sa.Column('version', sa.String(length=20), nullable=False, server_default='2.0'))
    op.add_column('nsm_principles', sa.Column('effective_date', sa.Date(), nullable=True))
    op.add_column('nsm_principles', sa.Column('deprecated_date', sa.Date(), nullable=True))

    # Add versioning fields to Ekomforskriften principles
    op.add_column('ekom_principles', sa.Column('version', sa.String(length=20), nullable=False, server_default='2024'))
    op.add_column('ekom_principles', sa.Column('effective_date', sa.Date(), nullable=True))
    op.add_column('ekom_principles', sa.Column('deprecated_date', sa.Date(), nullable=True))


def downgrade() -> None:
    # Remove versioning fields from Ekomforskriften principles
    op.drop_column('ekom_principles', 'deprecated_date')
    op.drop_column('ekom_principles', 'effective_date')
    op.drop_column('ekom_principles', 'version')

    # Remove versioning fields from NSM principles
    op.drop_column('nsm_principles', 'deprecated_date')
    op.drop_column('nsm_principles', 'effective_date')
    op.drop_column('nsm_principles', 'version')
