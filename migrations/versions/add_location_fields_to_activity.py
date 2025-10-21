"""Add location fields to Activity model

Revision ID: add_location_fields_to_activity
Revises: add_avatar_filename_to_admin, survey_system_2025
Create Date: 2025-10-21 12:00:00.000000

This migration adds location fields to the Activity model for geospatial
data capture and social sharing functionality.

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_location_fields_to_activity'
down_revision = ('add_avatar_filename_to_admin', 'survey_system_2025')  # Merge point
branch_labels = None
depends_on = None


def upgrade():
    """Add location columns to activity table"""
    try:
        # Add location_address_raw column (what user typed)
        op.add_column('activity', sa.Column('location_address_raw', sa.Text(), nullable=True))
        print("✅ Added location_address_raw column to activity table")

        # Add location_address_formatted column (Google's corrected address)
        op.add_column('activity', sa.Column('location_address_formatted', sa.Text(), nullable=True))
        print("✅ Added location_address_formatted column to activity table")

        # Add location_coordinates column (lat,lng for shareable links)
        op.add_column('activity', sa.Column('location_coordinates', sa.String(length=100), nullable=True))
        print("✅ Added location_coordinates column to activity table")

        print("✅ Location fields migration completed successfully")
        print("ℹ️  Existing activities will have NULL values for location fields")

    except Exception as e:
        print(f"❌ Error in location fields migration: {str(e)}")
        raise


def downgrade():
    """Remove location columns from activity table"""
    try:
        # Remove the added columns in reverse order
        op.drop_column('activity', 'location_coordinates')
        print("✅ Removed location_coordinates column during rollback")

        op.drop_column('activity', 'location_address_formatted')
        print("✅ Removed location_address_formatted column during rollback")

        op.drop_column('activity', 'location_address_raw')
        print("✅ Removed location_address_raw column during rollback")

        print("✅ Location fields rollback completed successfully")

    except Exception as e:
        print(f"❌ Error in location fields rollback: {str(e)}")
        raise
