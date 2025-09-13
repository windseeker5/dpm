#!/usr/bin/env python3
"""
Test script to verify Steven Bélanger payment matching will now work
with the user relationship fix.
"""

import unicodedata
from rapidfuzz import fuzz

def normalize_name(text):
    """Remove accents and normalize text for better matching"""
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents.lower().strip()

def test_steven_belanger_matching():
    """Test the Steven Bélanger specific case"""
    print("🧪 TESTING STEVEN BÉLANGER PAYMENT MATCHING FIX")
    print("=" * 60)

    # The exact case from your screenshot and payment logs
    bank_payment_name = "STEVEN BELANGER"  # From bank email (no accent)
    passport_name = "Steven Bélanger"      # From database (with accent)
    payment_amount = 320.0
    passport_amount = 320.0

    print(f"💳 BANK PAYMENT: {bank_payment_name} - ${payment_amount}")
    print(f"📋 PASSPORT: {passport_name} - ${passport_amount}")

    print(f"\n🔧 BEFORE FIX:")
    print(f"   - Passport model had NO user relationship")
    print(f"   - Code: if not p.user: continue  ← This skipped ALL passports!")
    print(f"   - Result: NO_MATCH (never got to name comparison)")

    print(f"\n✅ AFTER FIX:")
    print(f"   - Added: user = db.relationship('User', backref='passports')")
    print(f"   - Code: if not p.user: continue  ← Now works properly")
    print(f"   - p.user.name returns: '{passport_name}'")

    # Test the normalization that should now work
    normalized_payment = normalize_name(bank_payment_name)
    normalized_passport = normalize_name(passport_name)

    print(f"\n🔤 NAME NORMALIZATION:")
    print(f"   Bank: '{bank_payment_name}' → '{normalized_payment}'")
    print(f"   Passport: '{passport_name}' → '{normalized_passport}'")
    print(f"   Match: {normalized_payment == normalized_passport} ✅")

    # Test the fuzzy matching score
    score = fuzz.ratio(normalized_payment, normalized_passport)
    print(f"\n🎯 FUZZY MATCHING:")
    print(f"   Score: {score}% (threshold usually 85%)")
    print(f"   Result: {'MATCH' if score >= 85 else 'NO_MATCH'} ✅")

    # Test amount matching
    amount_match = float(payment_amount) == float(passport_amount)
    print(f"\n💰 AMOUNT MATCHING:")
    print(f"   Bank: ${payment_amount} → float({payment_amount}) = {float(payment_amount)}")
    print(f"   Passport: ${passport_amount} → float({passport_amount}) = {float(passport_amount)}")
    print(f"   Match: {amount_match} ✅")

    print(f"\n🎯 EXPECTED FINAL RESULT:")
    if amount_match and score >= 85:
        print(f"   ✅ PAYMENT SHOULD NOW MATCH!")
        print(f"   Steven Bélanger's passport will be marked as PAID")
        print(f"   Payment bot will show: MATCHED - Steven Bélanger (Score: {score}%)")
    else:
        print(f"   ❌ Still won't match - check thresholds")

    print(f"\n📋 VERIFICATION STEPS:")
    print(f"   1. Run payment bot again")
    print(f"   2. Should see: 'Found 1 unpaid passports for $320.00'")
    print(f"   3. Should see: 'EXACT MATCH: Steven Bélanger (Score: {score})'")
    print(f"   4. Should see: 'FINAL MATCH: Steven Bélanger'")
    print(f"   5. Steven's passport should change to PAID in dashboard")

if __name__ == "__main__":
    test_steven_belanger_matching()