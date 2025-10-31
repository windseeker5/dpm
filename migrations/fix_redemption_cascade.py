#!/usr/bin/env python3
"""
Migration script to add CASCADE DELETE to redemption.passport_id foreign key.

Since SQLite doesn't support ALTER TABLE to modify foreign keys, we need to:
1. Create a new table with CASCADE
2. Copy data from old table
3. Drop old table
4. Rename new table
"""

import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'minipass.db')

print(f"🔧 Updating redemption table to add CASCADE DELETE...")
print(f"📁 Database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = OFF")

    # Start transaction
    cursor.execute("BEGIN TRANSACTION")

    # Create new table with CASCADE DELETE
    cursor.execute("""
        CREATE TABLE redemption_new (
            id INTEGER NOT NULL,
            passport_id INTEGER NOT NULL,
            date_used DATETIME,
            redeemed_by VARCHAR(100),
            PRIMARY KEY (id),
            FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE CASCADE
        )
    """)

    # Copy data from old table
    cursor.execute("""
        INSERT INTO redemption_new (id, passport_id, date_used, redeemed_by)
        SELECT id, passport_id, date_used, redeemed_by
        FROM redemption
    """)

    # Drop old table
    cursor.execute("DROP TABLE redemption")

    # Rename new table
    cursor.execute("ALTER TABLE redemption_new RENAME TO redemption")

    # Commit transaction
    conn.commit()

    # Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Verify the change
    cursor.execute("PRAGMA foreign_key_list(redemption)")
    fk_info = cursor.fetchall()

    print("✅ Migration successful!")
    print(f"📊 Foreign key constraint: {fk_info}")

    # Check row count
    cursor.execute("SELECT COUNT(*) FROM redemption")
    count = cursor.fetchone()[0]
    print(f"✅ Verified {count} redemption records migrated successfully")

except Exception as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
    raise
finally:
    conn.close()

print("🎉 Migration complete!")
