#!/usr/bin/env python3
"""
Test to simulate the exact database filtering scenario that was failing.
"""

def test_database_float_filtering():
    """Test the database-like filtering scenario"""
    print("🧪 TESTING DATABASE FLOAT FILTERING SIMULATION")
    print("=" * 60)

    # Mock passport objects simulating database records
    class MockPassport:
        def __init__(self, id, user_name, sold_amt, paid=False):
            self.id = id
            self.user_name = user_name
            self.sold_amt = sold_amt  # This comes from SQLite as float
            self.paid = paid

    # Simulate Steven Belanger's database record
    passports = [
        MockPassport(1, "Steven Belanger", 320.00, False),    # From database
        MockPassport(2, "Steven Bélanger", 320.0, False),     # Alternative accent
        MockPassport(3, "John Smith", 50.0, False),
        MockPassport(4, "Marie Dubois", 100.0, False),
        MockPassport(5, "Robert Wilson", 320.0, True),        # Paid (should be filtered out)
    ]

    # Bank payment amount (from email)
    bank_amount = 320.0

    print(f"💳 BANK PAYMENT: ${bank_amount}")
    print(f"📋 AVAILABLE PASSPORTS:")
    for p in passports:
        status = "PAID" if p.paid else "UNPAID"
        print(f"   - {p.user_name}: ${p.sold_amt} ({status})")

    print(f"\n🔍 OLD APPROACH (SQL filter_by):")
    # Simulate what SQLAlchemy filter_by was doing
    old_matches = [p for p in passports if not p.paid and p.sold_amt == bank_amount]
    print(f"   SQL filter_by(paid=False, sold_amt={bank_amount}) found: {len(old_matches)} passports")
    for p in old_matches:
        print(f"   - {p.user_name}: ${p.sold_amt}")

    print(f"\n✅ NEW APPROACH (Python float comparison):")
    # Our new approach
    payment_amount = float(bank_amount)
    all_unpaid = [p for p in passports if not p.paid]
    new_matches = [p for p in all_unpaid if float(p.sold_amt) == payment_amount]
    print(f"   1. Get all unpaid: {len(all_unpaid)} passports")
    print(f"   2. Filter by float({bank_amount}) == float(passport.sold_amt): {len(new_matches)} matches")
    for p in new_matches:
        print(f"   - {p.user_name}: ${p.sold_amt}")

    print(f"\n🎯 RESULT:")
    if len(new_matches) > len(old_matches):
        print(f"   ✅ NEW APPROACH FINDS MORE MATCHES!")
        print(f"   This should fix Steven Belanger's issue")
    elif len(new_matches) == len(old_matches) and len(new_matches) > 0:
        print(f"   ✅ BOTH APPROACHES WORK - Issue was elsewhere")
    else:
        print(f"   ❌ Still no matches found - Different issue")

    # Test exact comparison that was failing
    print(f"\n🔬 PRECISION TEST:")
    database_value = 320.00  # Typical database storage
    email_value = 320.0      # From email parsing

    print(f"   Database: {database_value} (type: {type(database_value)})")
    print(f"   Email: {email_value} (type: {type(email_value)})")
    print(f"   Direct comparison: {email_value} == {database_value} → {email_value == database_value}")
    print(f"   Float comparison: float({email_value}) == float({database_value}) → {float(email_value) == float(database_value)}")

if __name__ == "__main__":
    test_database_float_filtering()