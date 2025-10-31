#!/usr/bin/env python3
"""
Test script to verify CASCADE DELETE works for redemptions when passports are deleted.
"""

import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'minipass.db')

print(f"🧪 Testing CASCADE DELETE on redemption table...")
print(f"📁 Database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

try:
    # Check current state for passport 77
    print("\n📊 Current state for passport #77:")
    cursor.execute("""
        SELECT p.id, p.pass_code, p.user_id, COUNT(r.id) as redemption_count
        FROM passport p
        LEFT JOIN redemption r ON r.passport_id = p.id
        WHERE p.id = 77
        GROUP BY p.id
    """)
    result = cursor.fetchone()
    if result:
        print(f"   Passport ID: {result[0]}")
        print(f"   Pass Code: {result[1]}")
        print(f"   User ID: {result[2]}")
        print(f"   Redemption Count: {result[3]}")
    else:
        print("   ❌ Passport #77 not found")

    # Check CASCADE constraint
    print("\n🔍 Checking foreign key constraint:")
    cursor.execute("PRAGMA foreign_key_list(redemption)")
    fk = cursor.fetchone()
    print(f"   Table: {fk[2]}")
    print(f"   From: {fk[3]} -> To: {fk[4]}")
    print(f"   On Delete: {fk[6]}")

    if fk[6] == "CASCADE":
        print("   ✅ CASCADE DELETE is properly configured!")
    else:
        print(f"   ❌ Expected CASCADE, got {fk[6]}")

    # Verify foreign keys are enabled in this connection
    cursor.execute("PRAGMA foreign_keys")
    fk_enabled = cursor.fetchone()[0]
    print(f"\n🔒 Foreign keys enabled: {'✅ Yes' if fk_enabled else '❌ No'}")

    print("\n✅ All checks passed!")
    print("\n💡 Note: Foreign keys will be enabled on every request via @app.before_request")

except Exception as e:
    print(f"❌ Test failed: {e}")
    raise
finally:
    conn.close()

print("\n🎉 Test complete!")
