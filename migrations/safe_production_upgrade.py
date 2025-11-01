#!/usr/bin/env python3
"""
Safe Production Database Upgrade Script
Adds missing columns and data that production needs to match dev database.

This script is IDEMPOTENT - safe to run multiple times.
It checks if changes already exist before applying them.
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'minipass.db')

def log(emoji, message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{emoji} [{timestamp}] {message}")

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def add_location_fields(cursor):
    """Add location fields to Activity table"""
    log("📍", "Task 1: Adding location fields to Activity table")

    fields = [
        ('location_address_raw', 'TEXT'),
        ('location_address_formatted', 'TEXT'),
        ('location_coordinates', 'VARCHAR(100)')
    ]

    added = 0
    skipped = 0

    for field_name, field_type in fields:
        if check_column_exists(cursor, 'activity', field_name):
            log("⏭️ ", f"  Column '{field_name}' already exists, skipping")
            skipped += 1
        else:
            try:
                cursor.execute(f"ALTER TABLE activity ADD COLUMN {field_name} {field_type}")
                log("✅", f"  Added column '{field_name}' to activity table")
                added += 1
            except sqlite3.OperationalError as e:
                log("❌", f"  Error adding column '{field_name}': {e}")
                raise

    log("📊", f"  Summary: {added} columns added, {skipped} already existed")
    return True

def backfill_financial_records(cursor):
    """Backfill created_by for existing income and expense records"""
    log("💰", "Task 2: Backfilling created_by for financial records")

    try:
        # Check if created_by column exists in income table
        if not check_column_exists(cursor, 'income', 'created_by'):
            log("⚠️ ", "  'created_by' column doesn't exist in income table, skipping")
        else:
            # Update income records with NULL or empty created_by
            cursor.execute("UPDATE income SET created_by = 'legacy' WHERE created_by IS NULL OR created_by = ''")
            income_updated = cursor.rowcount
            log("✅", f"  Updated {income_updated} income record(s)")

        # Check if created_by column exists in expense table
        if not check_column_exists(cursor, 'expense', 'created_by'):
            log("⚠️ ", "  'created_by' column doesn't exist in expense table, skipping")
        else:
            # Update expense records with NULL or empty created_by
            cursor.execute("UPDATE expense SET created_by = 'legacy' WHERE created_by IS NULL OR created_by = ''")
            expense_updated = cursor.rowcount
            log("✅", f"  Updated {expense_updated} expense record(s)")

        return True

    except sqlite3.OperationalError as e:
        log("❌", f"  Error backfilling financial records: {e}")
        raise

def verify_schema(cursor):
    """Verify that all expected columns exist"""
    log("🔍", "Task 3: Verifying database schema")

    checks = [
        ('admin', 'first_name', 'Admin names'),
        ('admin', 'last_name', 'Admin names'),
        ('admin', 'avatar_filename', 'Admin avatar'),
        ('activity', 'location_address_raw', 'Location fields'),
        ('activity', 'location_address_formatted', 'Location fields'),
        ('activity', 'location_coordinates', 'Location fields'),
        ('activity', 'organization_id', 'Organization support'),
    ]

    all_good = True
    for table, column, description in checks:
        if check_column_exists(cursor, table, column):
            log("✅", f"  {description}: '{column}' exists in {table}")
        else:
            log("❌", f"  {description}: '{column}' MISSING from {table}")
            all_good = False

    return all_good

def main():
    """Run the migration"""
    log("🚀", "=" * 60)
    log("🚀", "SAFE PRODUCTION DATABASE UPGRADE")
    log("🚀", "=" * 60)
    log("📁", f"Database: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        log("❌", f"Database not found at {DB_PATH}")
        sys.exit(1)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        log("🔄", "Transaction started")

        # Task 1: Add location fields
        add_location_fields(cursor)

        # Task 2: Backfill financial records
        backfill_financial_records(cursor)

        # Commit transaction
        conn.commit()
        log("✅", "Transaction committed successfully")

        # Task 3: Verify schema
        if verify_schema(cursor):
            log("🎉", "=" * 60)
            log("🎉", "DATABASE UPGRADE COMPLETED SUCCESSFULLY!")
            log("🎉", "=" * 60)
            log("📝", "Next steps:")
            log("📝", "  1. Run: flask db stamp head")
            log("📝", "  2. Run: python migrations/fix_redemption_cascade.py")
            log("📝", "  3. Run: python migrations/add_french_survey_and_fix_email_templates.py")
            return True
        else:
            log("⚠️ ", "Some schema checks failed - please review above")
            return False

    except Exception as e:
        # Rollback on error
        conn.rollback()
        log("❌", "=" * 60)
        log("❌", f"ERROR: {str(e)}")
        log("❌", "Transaction rolled back - database unchanged")
        log("❌", "=" * 60)
        return False

    finally:
        conn.close()
        log("🔒", "Database connection closed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
