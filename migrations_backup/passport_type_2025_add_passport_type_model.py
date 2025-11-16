"""Add PassportType model and update Activity/Passport models

Revision ID: passport_type_2025
Revises: 88979faca0ce
Create Date: 2025-06-18 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = 'passport_type_2025_add_passport_type_model'
down_revision = 'add_organization_email_support'
branch_labels = None
depends_on = None


def upgrade():
    # Create passport_type table
    op.create_table('passport_type',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('activity_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('price_per_user', sa.Float(), nullable=True),
        sa.Column('sessions_included', sa.Integer(), nullable=True),
        sa.Column('target_revenue', sa.Float(), nullable=True),
        sa.Column('payment_instructions', sa.Text(), nullable=True),
        sa.Column('created_dt', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['activity_id'], ['activity.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add passport_type_id to passport table
    with op.batch_alter_table('passport', schema=None) as batch_op:
        batch_op.add_column(sa.Column('passport_type_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_passport_passport_type', 'passport_type', ['passport_type_id'], ['id'])
    
    # Remove pricing fields from activity table (these moved to passport_type)
    with op.batch_alter_table('activity', schema=None) as batch_op:
        batch_op.drop_column('sessions_included')
        batch_op.drop_column('price_per_user') 
        batch_op.drop_column('goal_users')
        batch_op.drop_column('goal_revenue')
        batch_op.drop_column('cost_to_run')
        batch_op.drop_column('payment_instructions')


def downgrade():
    # Add back pricing fields to activity table
    with op.batch_alter_table('activity', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sessions_included', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('price_per_user', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('goal_users', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('goal_revenue', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('cost_to_run', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('payment_instructions', sa.Text(), nullable=True))
    
    # Remove passport_type_id from passport table
    with op.batch_alter_table('passport', schema=None) as batch_op:
        batch_op.drop_constraint('fk_passport_passport_type', type_='foreignkey')
        batch_op.drop_column('passport_type_id')
    
    # Drop passport_type table
    op.drop_table('passport_type')