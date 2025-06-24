#!/usr/bin/env python3
"""
Database Migration Runner
========================

This script safely adds the new columns to your existing database.
Run this script BEFORE starting your Flask application.

Usage:
    python migrate_database.py

"""

import sqlite3
import os
import sys
from datetime import datetime

def get_database_path():
    """Get the path to the database file"""
    # Check common database locations
    possible_paths = [
        'instance/dev_database.db',
        'instance/database.db',
        'dev_database.db',
        'database.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    print("❌ Could not find database file. Please check the following locations:")
    for path in possible_paths:
        print(f"   - {path}")
    return None

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_database():
    """Run the database migration"""
    
    print("🚀 Database Migration for Passport Type Management")
    print("=" * 55)
    
    # Find database file
    db_path = get_database_path()
    if not db_path:
        return False
    
    print(f"📁 Using database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 Checking current database structure...")
        
        # Check existing columns
        passport_type_columns = []
        cursor.execute("PRAGMA table_info(passport_type)")
        for row in cursor.fetchall():
            passport_type_columns.append(row[1])
        
        passport_columns = []
        cursor.execute("PRAGMA table_info(passport)")
        for row in cursor.fetchall():
            passport_columns.append(row[1])
        
        print(f"   PassportType columns: {', '.join(passport_type_columns)}")
        print(f"   Passport columns: {', '.join(passport_columns)}")
        
        migration_needed = False
        
        # Check what needs to be added
        passport_type_new_columns = [
            ('status', 'VARCHAR(50) DEFAULT "active"'),
            ('archived_at', 'DATETIME'),
            ('archived_by', 'VARCHAR(120)')
        ]
        
        passport_new_columns = [
            ('passport_type_name', 'VARCHAR(100)')
        ]
        
        print("\n🔧 Applying migrations...")
        
        # Add columns to passport_type table
        for column_name, column_def in passport_type_new_columns:
            if column_name not in passport_type_columns:
                print(f"   ➕ Adding {column_name} to passport_type table...")
                cursor.execute(f"ALTER TABLE passport_type ADD COLUMN {column_name} {column_def}")
                migration_needed = True
            else:
                print(f"   ✅ Column {column_name} already exists in passport_type")
        
        # Add columns to passport table
        for column_name, column_def in passport_new_columns:
            if column_name not in passport_columns:
                print(f"   ➕ Adding {column_name} to passport table...")
                cursor.execute(f"ALTER TABLE passport ADD COLUMN {column_name} {column_def}")
                migration_needed = True
            else:
                print(f"   ✅ Column {column_name} already exists in passport")
        
        # Update existing records
        print("\n📊 Updating existing data...")
        
        # Set status to 'active' for existing passport types
        cursor.execute("UPDATE passport_type SET status = 'active' WHERE status IS NULL")
        updated_types = cursor.rowcount
        print(f"   ✅ Updated {updated_types} passport types to 'active' status")
        
        # Backfill passport_type_name for existing passports
        cursor.execute("""
            UPDATE passport 
            SET passport_type_name = (
                SELECT pt.name 
                FROM passport_type pt 
                WHERE pt.id = passport.passport_type_id
            )
            WHERE passport.passport_type_id IS NOT NULL 
            AND passport.passport_type_name IS NULL
        """)
        updated_passports = cursor.rowcount
        print(f"   ✅ Backfilled passport type names for {updated_passports} passports")
        
        # Commit changes
        conn.commit()
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        
        # Check for orphaned passport type references
        cursor.execute("""
            SELECT COUNT(*) FROM passport p
            LEFT JOIN passport_type pt ON p.passport_type_id = pt.id
            WHERE p.passport_type_id IS NOT NULL AND pt.id IS NULL
        """)
        orphaned_count = cursor.fetchone()[0]
        
        if orphaned_count > 0:
            print(f"   ⚠️  Found {orphaned_count} passports with missing passport types")
            print("   🔧 Fixing orphaned passport references...")
            
            cursor.execute("""
                UPDATE passport 
                SET passport_type_name = 'Deleted Type',
                    passport_type_id = NULL
                WHERE passport_type_id IS NOT NULL 
                AND passport_type_id NOT IN (SELECT id FROM passport_type)
            """)
            fixed_count = cursor.rowcount
            print(f"   ✅ Fixed {fixed_count} orphaned passport references")
            conn.commit()
        
        # Final verification
        cursor.execute("SELECT COUNT(*) FROM passport_type")
        total_passport_types = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM passport")
        total_passports = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM passport WHERE passport_type_name IS NOT NULL")
        passports_with_names = cursor.fetchone()[0]
        
        print("\n" + "=" * 55)
        print("📈 Migration Summary:")
        print(f"   • Total passport types: {total_passport_types}")
        print(f"   • Total passports: {total_passports}")
        print(f"   • Passports with type names: {passports_with_names}")
        
        if migration_needed:
            print("✅ Database migration completed successfully!")
        else:
            print("✅ Database was already up to date!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function"""
    print("Starting database migration...\n")
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nYou can now start your Flask application.")
        print("The passport type management features are ready to use.")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        print("Make sure your database file exists and is accessible.")
        sys.exit(1)

if __name__ == "__main__":
    main()