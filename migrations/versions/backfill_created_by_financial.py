"""Backfill created_by for existing income and expense entries

Revision ID: backfill_created_by_financial
Revises: add_location_fields_to_activity
Create Date: 2025-10-26 12:35:00.000000

This migration backfills NULL or empty created_by values in Income and Expense
tables with 'System' to ensure all financial transactions have a creator.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'backfill_created_by_financial'
down_revision = 'add_location_fields_to_activity'
branch_labels = None
depends_on = None


def upgrade():
    """Backfill NULL/empty created_by values with 'System'"""
    try:
        # Backfill NULL or empty created_by values in Income table
        op.execute("UPDATE income SET created_by = 'System' WHERE created_by IS NULL OR created_by = ''")
        print("✅ Backfilled created_by in income table")

        # Backfill NULL or empty created_by values in Expense table
        op.execute("UPDATE expense SET created_by = 'System' WHERE created_by IS NULL OR created_by = ''")
        print("✅ Backfilled created_by in expense table")

        print("✅ Created_by backfill migration completed successfully")
        print("ℹ️  All existing income and expense entries now have 'System' as creator")

    except Exception as e:
        print(f"❌ Error in created_by backfill migration: {str(e)}")
        raise


def downgrade():
    """Optional: revert to NULL if needed (not recommended)"""
    # We generally don't revert data migrations, but if needed:
    # op.execute("UPDATE income SET created_by = NULL WHERE created_by = 'System'")
    # op.execute("UPDATE expense SET created_by = NULL WHERE created_by = 'System'")
    print("ℹ️  Data migration downgrade skipped (not reversible)")
    pass
