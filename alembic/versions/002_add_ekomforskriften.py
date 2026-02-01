"""Add Ekomforskriften tables

Revision ID: 002
Revises: 001
Create Date: 2026-02-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ekomforskriften Principles
    op.create_table(
        'ekom_principles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('paragraph', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('legal_text', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ekom_principles_code'), 'ekom_principles', ['code'], unique=True)
    op.create_index(op.f('ix_ekom_principles_paragraph'), 'ekom_principles', ['paragraph'], unique=False)

    # Ekomforskriften Risk Mappings
    op.create_table(
        'ekom_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('risk_id', sa.Integer(), nullable=False),
        sa.Column('ekom_principle_id', sa.Integer(), nullable=False),
        sa.Column('compliance_status', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['risk_id'], ['risks.id'], ),
        sa.ForeignKeyConstraint(['ekom_principle_id'], ['ekom_principles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ekom_mappings_risk_id'), 'ekom_mappings', ['risk_id'], unique=False)
    op.create_index(op.f('ix_ekom_mappings_ekom_principle_id'), 'ekom_mappings', ['ekom_principle_id'], unique=False)

    # Ekomforskriften Action Mappings
    op.create_table(
        'ekom_action_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=False),
        sa.Column('ekom_principle_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['action_id'], ['actions.id'], ),
        sa.ForeignKeyConstraint(['ekom_principle_id'], ['ekom_principles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ekom_action_mappings_action_id'), 'ekom_action_mappings', ['action_id'], unique=False)
    op.create_index(op.f('ix_ekom_action_mappings_ekom_principle_id'), 'ekom_action_mappings', ['ekom_principle_id'], unique=False)


def downgrade() -> None:
    op.drop_table('ekom_action_mappings')
    op.drop_table('ekom_mappings')
    op.drop_table('ekom_principles')
