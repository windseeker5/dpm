"""Add use_custom_payment_instructions to PassportType

Revision ID: af5045ed1c22
Revises: 0307966a5581
Create Date: 2025-11-18 17:45:56.983486

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'af5045ed1c22'
down_revision = '0307966a5581'
branch_labels = None
depends_on = None


def upgrade():
    # Add use_custom_payment_instructions column to passport_type table
    with op.batch_alter_table('passport_type', schema=None) as batch_op:
        batch_op.add_column(sa.Column('use_custom_payment_instructions', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    # Remove use_custom_payment_instructions column from passport_type table
    with op.batch_alter_table('passport_type', schema=None) as batch_op:
        batch_op.drop_column('use_custom_payment_instructions')
