#!/usr/bin/env python3
"""
Migration: Fix organization_id to allow NULL values with foreign key constraints enabled

Problem: With PRAGMA foreign_keys = ON, the activity table's organization_id foreign key
is rejecting NULL values even though it should be nullable.

Solution: Recreate the foreign key constraint to properly handle NULL values.
"""

import sqlite3
import sys
import os
from datetime import datetime, timezone

DB_PATH = "instance/minipass.db"

def run_migration():
    """Fix organization_id foreign key to allow NULL values"""

    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Step 1: Disable foreign keys temporarily
        print("📋 Step 1: Disabling foreign keys...")
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Step 2: Begin transaction
        cursor.execute("BEGIN TRANSACTION")

        # Step 3: Get current table schema
        print("📋 Step 2: Reading activity table schema...")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='activity'")
        original_schema = cursor.fetchone()[0]
        print(f"Current schema:\n{original_schema}\n")

        # Step 4: Create new table with corrected foreign key
        print("📋 Step 3: Creating new activity table with nullable foreign key...")
        cursor.execute("""
            CREATE TABLE activity_new (
                id INTEGER NOT NULL,
                name VARCHAR(150) NOT NULL,
                type VARCHAR(50),
                description TEXT,
                sessions_included INTEGER,
                price_per_user FLOAT,
                goal_users INTEGER,
                goal_revenue FLOAT,
                cost_to_run FLOAT,
                created_by INTEGER,
                created_dt DATETIME,
                status VARCHAR(50),
                payment_instructions TEXT,
                start_date DATETIME,
                end_date DATETIME,
                image_filename VARCHAR(255),
                organization_id INTEGER,
                email_templates TEXT,
                logo_filename VARCHAR(255),
                location_address_raw TEXT,
                location_address_formatted TEXT,
                location_coordinates TEXT,
                PRIMARY KEY (id),
                FOREIGN KEY(created_by) REFERENCES admin (id),
                FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE SET NULL
            )
        """)

        # Step 5: Copy all data from old table to new table
        print("📋 Step 4: Copying all activity records...")
        cursor.execute("""
            INSERT INTO activity_new
            SELECT id, name, type, description, sessions_included, price_per_user,
                   goal_users, goal_revenue, cost_to_run, created_by, created_dt,
                   status, payment_instructions, start_date, end_date, image_filename,
                   organization_id, email_templates, logo_filename, location_address_raw,
                   location_address_formatted, location_coordinates
            FROM activity
        """)
        rows_copied = cursor.rowcount
        print(f"✅ Copied {rows_copied} activity records")

        # Step 6: Drop old table
        print("📋 Step 5: Dropping old activity table...")
        cursor.execute("DROP TABLE activity")

        # Step 7: Rename new table
        print("📋 Step 6: Renaming new table to 'activity'...")
        cursor.execute("ALTER TABLE activity_new RENAME TO activity")

        # Step 8: Commit transaction
        print("📋 Step 7: Committing changes...")
        conn.commit()

        # Step 9: Re-enable foreign keys
        print("📋 Step 8: Re-enabling foreign keys...")
        cursor.execute("PRAGMA foreign_keys = ON")

        # Step 10: Verify foreign key integrity
        print("📋 Step 9: Verifying foreign key integrity...")
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()

        if violations:
            print(f"⚠️  Warning: Found {len(violations)} foreign key violations:")
            for v in violations:
                print(f"   {v}")
        else:
            print("✅ All foreign key constraints are valid")

        # Verify new schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='activity'")
        new_schema = cursor.fetchone()[0]
        print(f"\nNew schema:\n{new_schema}\n")

        print("✅ Migration completed successfully!")
        print(f"✅ Activity table now properly allows NULL values for organization_id")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Fixing organization_id foreign key constraint...")
    print(f"Database: {DB_PATH}")
    print("-" * 60)
    run_migration()
