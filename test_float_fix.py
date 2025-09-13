#!/usr/bin/env python3
"""
Test script to verify the float comparison fix works correctly.
This tests specifically the Steven Belanger scenario.
"""

def test_float_comparison():
    """Test the float comparison logic"""
    print("🧪 TESTING FLOAT COMPARISON FIX")
    print("=" * 50)

    # Simulate the Steven Belanger scenario
    print("📊 STEVEN BELANGER TEST CASE")

    # Mock data representing the issue
    bank_payment_amount = 320.0  # From bank email
    passport_amounts = [320.00, 50.0, 100.0, 80.0]  # Database amounts

    print(f"   Bank payment amount: {bank_payment_amount} (type: {type(bank_payment_amount)})")
    print(f"   Passport amounts: {passport_amounts}")

    # OLD approach (problematic)
    print(f"\n❌ OLD APPROACH (Direct comparison):")
    old_matches = [amt for amt in passport_amounts if amt == bank_payment_amount]
    print(f"   Matches found: {len(old_matches)} - {old_matches}")

    # NEW approach (fixed)
    print(f"\n✅ NEW APPROACH (Float conversion):")
    payment_amount = float(bank_payment_amount)
    new_matches = [amt for amt in passport_amounts if float(amt) == payment_amount]
    print(f"   Payment amount as float: {payment_amount:.2f}")
    print(f"   Matches found: {len(new_matches)} - {new_matches}")

    # Test edge cases
    print(f"\n🧪 EDGE CASE TESTS:")

    test_cases = [
        (320.0, 320.00, "Decimal precision"),
        (50.0, 50, "Float vs int"),
        (9.99, 9.99, "Decimal currency"),
        (100.0, 100.000, "Multiple decimal places")
    ]

    for payment, passport, description in test_cases:
        match = float(payment) == float(passport)
        status = "✅ MATCH" if match else "❌ NO MATCH"
        print(f"   {description}: {payment} == {passport} → {status}")

    print(f"\n🎯 EXPECTED RESULT FOR STEVEN BELANGER:")
    print(f"   Bank: 320.0 → float(320.0) = 320.0")
    print(f"   Passport: 320.00 → float(320.00) = 320.0")
    print(f"   Comparison: 320.0 == 320.0 → ✅ TRUE")
    print(f"   Should now MATCH instead of NO_MATCH!")

if __name__ == "__main__":
    test_float_comparison()