"""Add first_name and last_name fields to Admin model

Revision ID: add_admin_names_fields
Revises: passport_type_2025_add_passport_type_model
Create Date: 2025-08-21 00:00:00.000000

This migration adds first_name and last_name fields to the Admin model
for better personalization and welcome messages.

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_admin_names_fields'
down_revision = 'passport_type_2025_add_passport_type_model'
branch_labels = None
depends_on = None


def upgrade():
    """Add first_name and last_name columns to admin table"""
    try:
        # Add first_name column
        op.add_column('admin', sa.Column('first_name', sa.String(length=50), nullable=True))
        print("✅ Added first_name column to admin table")
        
        # Add last_name column  
        op.add_column('admin', sa.Column('last_name', sa.String(length=50), nullable=True))
        print("✅ Added last_name column to admin table")
        
        print("✅ Admin names migration completed successfully")
        
    except Exception as e:
        print(f"❌ Error in admin names migration: {str(e)}")
        raise


def downgrade():
    """Remove first_name and last_name columns from admin table"""
    try:
        # Remove the added columns
        op.drop_column('admin', 'last_name')
        op.drop_column('admin', 'first_name')
        print("✅ Removed admin name columns during rollback")
        
    except Exception as e:
        print(f"❌ Error in admin names rollback: {str(e)}")
        raise


if __name__ == "__main__":
    # Direct execution for testing
    from sqlalchemy import create_engine, MetaData
    from models import db
    import os
    
    # Get database path
    db_path = "instance/minipass.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        exit(1)
        
    # Create engine and run migration
    engine = create_engine(f'sqlite:///{db_path}')
    
    # Check if columns already exist
    inspector = sa.inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('admin')]
    
    if 'first_name' in columns and 'last_name' in columns:
        print("✅ Admin name columns already exist, skipping migration")
    else:
        print("🔄 Running admin names migration...")
        
        with engine.connect() as conn:
            # Add first_name column if not exists
            if 'first_name' not in columns:
                conn.execute(text("ALTER TABLE admin ADD COLUMN first_name VARCHAR(50)"))
                print("✅ Added first_name column")
            
            # Add last_name column if not exists
            if 'last_name' not in columns:
                conn.execute(text("ALTER TABLE admin ADD COLUMN last_name VARCHAR(50)"))
                print("✅ Added last_name column")
            
            conn.commit()
        
        print("✅ Migration completed successfully")