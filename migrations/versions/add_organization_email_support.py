"""Add Organization model for multi-tenant email support

Revision ID: add_organization_email_support
Revises: 
Create Date: 2025-01-19

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers
revision = 'add_organization_email_support'
down_revision = '717386dae2a5'
branch_labels = None
depends_on = None

def upgrade():
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=100), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=True, default=False),
        sa.Column('mail_server', sa.String(length=255), nullable=True),
        sa.Column('mail_port', sa.Integer(), nullable=True, default=587),
        sa.Column('mail_use_tls', sa.Boolean(), nullable=True, default=True),
        sa.Column('mail_use_ssl', sa.Boolean(), nullable=True, default=False),
        sa.Column('mail_username', sa.String(length=255), nullable=True),
        sa.Column('mail_password', sa.String(length=500), nullable=True),
        sa.Column('mail_sender_name', sa.String(length=255), nullable=True),
        sa.Column('mail_sender_email', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('fallback_to_system_email', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain')
    )
    
    # Add organization_id foreign key to activities table
    with op.batch_alter_table('activity', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_activity_organization', 'organizations', ['organization_id'], ['id'])
    
    # Add organization_id foreign key to users table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_user_organization', 'organizations', ['organization_id'], ['id'])

def downgrade():
    # Remove organization_id from user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_organization', type_='foreignkey')
        batch_op.drop_column('organization_id')
    
    # Remove organization_id from activity table  
    with op.batch_alter_table('activity', schema=None) as batch_op:
        batch_op.drop_constraint('fk_activity_organization', type_='foreignkey')
        batch_op.drop_column('organization_id')
    
    # Drop organizations table
    op.drop_table('organizations')