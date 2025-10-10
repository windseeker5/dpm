#!/usr/bin/env python3
"""
Reset payment status from MANUAL_PROCESSED back to NO_MATCH using direct SQLite
"""

import sqlite3
from datetime import datetime

db_path = "instance/minipass.db"

print("🔄 Resetting payment statuses for testing...\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Reset Jean-Martin Morin
print("1️⃣ Jean-Martin Morin:")
cursor.execute("""
    SELECT id, bank_info_name, bank_info_amt, result, timestamp, note
    FROM ebank_payment
    WHERE bank_info_name = 'Jean Martin Morin'
      AND bank_info_amt = 80.0
      AND result = 'MANUAL_PROCESSED'
    ORDER BY timestamp DESC
    LIMIT 1
""")

row = cursor.fetchone()
if row:
    payment_id, name, amount, old_status, timestamp, old_note = row
    new_note = (old_note or "") + " [Status reset from MANUAL_PROCESSED to NO_MATCH for testing]"

    cursor.execute("""
        UPDATE ebank_payment
        SET result = 'NO_MATCH',
            note = ?
        WHERE id = ?
    """, (new_note, payment_id))

    print(f"✅ Reset payment ID {payment_id}")
    print(f"   Name: {name}")
    print(f"   Amount: ${amount}")
    print(f"   Old Status: {old_status}")
    print(f"   New Status: NO_MATCH")
    print(f"   Timestamp: {timestamp}")
    print()
else:
    print("❌ No MANUAL_PROCESSED payment found")
    # Check if exists with different status
    cursor.execute("""
        SELECT id, result FROM ebank_payment
        WHERE bank_info_name = 'Jean Martin Morin'
          AND bank_info_amt = 80.0
        ORDER BY timestamp DESC LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        print(f"   Found payment ID {row[0]} with status: {row[1]}")
    print()

# Reset Christian Tremblay
print("2️⃣ Christian Tremblay:")
cursor.execute("""
    SELECT id, bank_info_name, bank_info_amt, result, timestamp, note
    FROM ebank_payment
    WHERE bank_info_name = 'CHRISTIAN TREMBLAY'
      AND bank_info_amt = 160.0
      AND result = 'MANUAL_PROCESSED'
    ORDER BY timestamp DESC
    LIMIT 1
""")

row = cursor.fetchone()
if row:
    payment_id, name, amount, old_status, timestamp, old_note = row
    new_note = (old_note or "") + " [Status reset from MANUAL_PROCESSED to NO_MATCH for testing]"

    cursor.execute("""
        UPDATE ebank_payment
        SET result = 'NO_MATCH',
            note = ?
        WHERE id = ?
    """, (new_note, payment_id))

    print(f"✅ Reset payment ID {payment_id}")
    print(f"   Name: {name}")
    print(f"   Amount: ${amount}")
    print(f"   Old Status: {old_status}")
    print(f"   New Status: NO_MATCH")
    print(f"   Timestamp: {timestamp}")
    print()
else:
    print("❌ No MANUAL_PROCESSED payment found")
    # Check if exists with different status
    cursor.execute("""
        SELECT id, result FROM ebank_payment
        WHERE bank_info_name = 'CHRISTIAN TREMBLAY'
          AND bank_info_amt = 160.0
        ORDER BY timestamp DESC LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        print(f"   Found payment ID {row[0]} with status: {row[1]}")
    print()

conn.commit()
conn.close()

print("=" * 70)
print("✅ Done! Refresh the Payment Bot Matches page to see Archive buttons again.")
print("=" * 70)
