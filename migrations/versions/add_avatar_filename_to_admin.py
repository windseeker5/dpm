"""Add avatar_filename field to Admin model

Revision ID: add_avatar_filename_to_admin
Revises: add_admin_names_fields
Create Date: 2025-08-21 01:30:00.000000

This migration adds avatar_filename field to the Admin model
for custom avatar uploads when Gravatar is not available.

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_avatar_filename_to_admin'
down_revision = 'add_admin_names_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Add avatar_filename column to admin table"""
    try:
        # Add avatar_filename column
        op.add_column('admin', sa.Column('avatar_filename', sa.String(length=255), nullable=True))
        print("✅ Added avatar_filename column to admin table")
        
        print("✅ Avatar filename migration completed successfully")
        
    except Exception as e:
        print(f"❌ Error in avatar filename migration: {str(e)}")
        raise


def downgrade():
    """Remove avatar_filename column from admin table"""
    try:
        # Remove the added column
        op.drop_column('admin', 'avatar_filename')
        print("✅ Removed avatar_filename column during rollback")
        
    except Exception as e:
        print(f"❌ Error in avatar filename rollback: {str(e)}")
        raise