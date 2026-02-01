"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Departments
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_departments_name'), 'departments', ['name'], unique=False)

    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='bruker'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Update departments manager_id foreign key
    op.create_foreign_key('fk_departments_manager', 'departments', 'users', ['manager_id'], ['id'])

    # Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.String(length=50), nullable=False, server_default='periodisk_ros'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planlagt'),
        sa.Column('scheduled_date', sa.Date(), nullable=True),
        sa.Column('completed_date', sa.Date(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('owner_department_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['owner_department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)

    # Assets
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_type', sa.String(length=50), nullable=False, server_default='fysisk'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='annet'),
        sa.Column('criticality', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('netbox_id', sa.Integer(), nullable=True),
        sa.Column('netbox_url', sa.String(length=500), nullable=True),
        sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('manufacturer', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('owner_department_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['owner_department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assets_name'), 'assets', ['name'], unique=False)
    op.create_index(op.f('ix_assets_netbox_id'), 'assets', ['netbox_id'], unique=False)

    # Suppliers
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('supplier_type', sa.String(length=50), nullable=False, server_default='tjenesteleverandør'),
        sa.Column('criticality', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('contact_info', sa.Text(), nullable=True),
        sa.Column('contract_reference', sa.String(length=100), nullable=True),
        sa.Column('contract_expiry', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suppliers_name'), 'suppliers', ['name'], unique=False)

    # Information Assets
    op.create_table(
        'information_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('classification', sa.String(length=50), nullable=False, server_default='intern'),
        sa.Column('data_types_str', sa.String(length=500), nullable=True),
        sa.Column('owner_department_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['owner_department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_information_assets_name'), 'information_assets', ['name'], unique=False)

    # NSM Principles
    op.create_table(
        'nsm_principles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nsm_principles_code'), 'nsm_principles', ['code'], unique=True)

    # Risks
    op.create_table(
        'risks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('risk_type', sa.String(length=50), nullable=False, server_default='teknisk'),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('likelihood', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('consequence', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('target_likelihood', sa.Integer(), nullable=True),
        sa.Column('target_consequence', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='identifisert'),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('owner_department_id', sa.Integer(), nullable=True),
        sa.Column('vulnerability_description', sa.Text(), nullable=True),
        sa.Column('threat_description', sa.Text(), nullable=True),
        sa.Column('existing_controls', sa.Text(), nullable=True),
        sa.Column('proposed_measures', sa.Text(), nullable=True),
        sa.Column('last_reviewed_at', sa.Date(), nullable=True),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['owner_department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risks_title'), 'risks', ['title'], unique=False)
    op.create_index(op.f('ix_risks_project_id'), 'risks', ['project_id'], unique=False)

    # Actions
    op.create_table(
        'actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='middels'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planlagt'),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('responsible_department_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['responsible_department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_actions_title'), 'actions', ['title'], unique=False)

    # Reviews
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('review_type', sa.String(length=50), nullable=False, server_default='periodisk'),
        sa.Column('scheduled_date', sa.Date(), nullable=True),
        sa.Column('conducted_date', sa.Date(), nullable=True),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.Column('conductor_id', sa.Integer(), nullable=True),
        sa.Column('findings', sa.Text(), nullable=True),
        sa.Column('conclusions', sa.Text(), nullable=True),
        sa.Column('incident_reference', sa.String(length=100), nullable=True),
        sa.Column('incident_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['conductor_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reviews_title'), 'reviews', ['title'], unique=False)

    # Documents
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)

    # Junction tables
    op.create_table(
        'asset_suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_suppliers_asset_id'), 'asset_suppliers', ['asset_id'], unique=False)
    op.create_index(op.f('ix_asset_suppliers_supplier_id'), 'asset_suppliers', ['supplier_id'], unique=False)

    op.create_table(
        'asset_risks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('risk_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['risk_id'], ['risks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_risks_asset_id'), 'asset_risks', ['asset_id'], unique=False)
    op.create_index(op.f('ix_asset_risks_risk_id'), 'asset_risks', ['risk_id'], unique=False)

    op.create_table(
        'nsm_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('risk_id', sa.Integer(), nullable=False),
        sa.Column('nsm_principle_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['risk_id'], ['risks.id'], ),
        sa.ForeignKeyConstraint(['nsm_principle_id'], ['nsm_principles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nsm_mappings_risk_id'), 'nsm_mappings', ['risk_id'], unique=False)
    op.create_index(op.f('ix_nsm_mappings_nsm_principle_id'), 'nsm_mappings', ['nsm_principle_id'], unique=False)

    op.create_table(
        'risk_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('risk_id', sa.Integer(), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['risk_id'], ['risks.id'], ),
        sa.ForeignKeyConstraint(['action_id'], ['actions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_actions_risk_id'), 'risk_actions', ['risk_id'], unique=False)
    op.create_index(op.f('ix_risk_actions_action_id'), 'risk_actions', ['action_id'], unique=False)

    op.create_table(
        'review_risks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('review_id', sa.Integer(), nullable=False),
        sa.Column('risk_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], ),
        sa.ForeignKeyConstraint(['risk_id'], ['risks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_review_risks_review_id'), 'review_risks', ['review_id'], unique=False)
    op.create_index(op.f('ix_review_risks_risk_id'), 'review_risks', ['risk_id'], unique=False)

    op.create_table(
        'information_asset_risks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('information_asset_id', sa.Integer(), nullable=False),
        sa.Column('risk_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['information_asset_id'], ['information_assets.id'], ),
        sa.ForeignKeyConstraint(['risk_id'], ['risks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_information_asset_risks_information_asset_id'), 'information_asset_risks', ['information_asset_id'], unique=False)
    op.create_index(op.f('ix_information_asset_risks_risk_id'), 'information_asset_risks', ['risk_id'], unique=False)

    op.create_table(
        'document_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_links_document_id'), 'document_links', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_links_entity_id'), 'document_links', ['entity_id'], unique=False)


def downgrade() -> None:
    op.drop_table('document_links')
    op.drop_table('information_asset_risks')
    op.drop_table('review_risks')
    op.drop_table('risk_actions')
    op.drop_table('nsm_mappings')
    op.drop_table('asset_risks')
    op.drop_table('asset_suppliers')
    op.drop_table('audit_logs')
    op.drop_table('documents')
    op.drop_table('reviews')
    op.drop_table('actions')
    op.drop_table('risks')
    op.drop_table('nsm_principles')
    op.drop_table('information_assets')
    op.drop_table('suppliers')
    op.drop_table('assets')
    op.drop_table('projects')
    op.drop_constraint('fk_departments_manager', 'departments', type_='foreignkey')
    op.drop_table('users')
    op.drop_table('departments')
