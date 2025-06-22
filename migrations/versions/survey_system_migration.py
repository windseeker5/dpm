"""Add survey system tables

Revision ID: survey_system_2025
Revises: 
Create Date: 2025-06-22 11:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'survey_system_2025'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create survey_template table
    op.create_table('survey_template',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('questions', sa.Text(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_dt', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['admin.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create survey table
    op.create_table('survey',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('template_id', sa.Integer(), nullable=False),
    sa.Column('passport_type_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('survey_token', sa.String(length=32), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_dt', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('email_sent', sa.Boolean(), nullable=True),
    sa.Column('email_sent_dt', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['activity.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['admin.id'], ),
    sa.ForeignKeyConstraint(['passport_type_id'], ['passport_type.id'], ),
    sa.ForeignKeyConstraint(['template_id'], ['survey_template.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('survey_token')
    )
    
    # Create survey_response table
    op.create_table('survey_response',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('survey_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('passport_id', sa.Integer(), nullable=True),
    sa.Column('response_token', sa.String(length=32), nullable=False),
    sa.Column('responses', sa.Text(), nullable=True),
    sa.Column('completed', sa.Boolean(), nullable=True),
    sa.Column('completed_dt', sa.DateTime(), nullable=True),
    sa.Column('started_dt', sa.DateTime(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['passport_id'], ['passport.id'], ),
    sa.ForeignKeyConstraint(['survey_id'], ['survey.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('response_token')
    )
    
    # Create indexes
    op.create_index('ix_survey_token', 'survey', ['survey_token'], unique=False)
    op.create_index('ix_survey_response_token', 'survey_response', ['response_token'], unique=False)
    op.create_index('ix_survey_activity', 'survey', ['activity_id'], unique=False)
    op.create_index('ix_survey_response_survey', 'survey_response', ['survey_id'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('ix_survey_response_survey', table_name='survey_response')
    op.drop_index('ix_survey_activity', table_name='survey')
    op.drop_index('ix_survey_response_token', table_name='survey_response')
    op.drop_index('ix_survey_token', table_name='survey')
    
    # Drop tables
    op.drop_table('survey_response')
    op.drop_table('survey')
    op.drop_table('survey_template')