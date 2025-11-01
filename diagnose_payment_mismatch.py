#!/usr/bin/env python3
"""
COMPREHENSIVE PAYMENT MATCHING DIAGNOSTIC
This script will show you exactly why payments aren't matching
"""

from app import app
from models import db, Passport, EbankPayment, User
from rapidfuzz import fuzz

# List of payment names from your email inbox
PAYMENT_NAMES = [
    ("YANNICK DRAPEAU", 50.00),
    ("DAVID CASTONGUAY", 50.00),
    ("PAUL-AIME LEBLANC", 50.00),
    ("STEPHANE D'ASTOUS", 100.00),
    ("DOMINIC THERIAULT", 50.00),
    ("Jean Martin Morin", 80.00),
    ("GREG TECH 2010", 160.00),
    ("JORDI NADAL", 50.00),
    ("DOMINIC BLANCHET", 50.00),
    ("STEVEN BELANGER", 99.00),
    ("SAMUEL TURBIDE", 50.00),
    ("PATRICK BELAND", 15.00),
    ("JEAN BELANGER", 50.00),
    ("STEVEN BELANGER", 94.00),
]

with app.app_context():
    print("="*100)
    print("PAYMENT MATCHING DIAGNOSTIC REPORT")
    print("="*100)

    # First, show all passports (paid and unpaid) to understand what exists
    print("\n1. ALL PASSPORTS IN DATABASE (Paid & Unpaid):")
    print("-"*100)
    all_passports = Passport.query.join(User).all()
    passport_by_amount = {}

    for p in all_passports:
        amount = float(p.sold_amt)
        if amount not in passport_by_amount:
            passport_by_amount[amount] = {'paid': [], 'unpaid': []}

        if p.paid:
            passport_by_amount[amount]['paid'].append(p)
        else:
            passport_by_amount[amount]['unpaid'].append(p)

    for amount in sorted(passport_by_amount.keys()):
        print(f"\n   ${amount:.2f} Passports:")
        unpaid = passport_by_amount[amount]['unpaid']
        paid = passport_by_amount[amount]['paid']

        print(f"      UNPAID ({len(unpaid)}):")
        for p in unpaid:
            print(f"         - {p.user.name}")

        print(f"      PAID ({len(paid)}):")
        for p in paid[:10]:  # Show first 10 paid
            paid_date = p.paid_date.strftime("%Y-%m-%d") if p.paid_date else "Unknown"
            marked_by = p.marked_paid_by or "Unknown"
            print(f"         - {p.user.name} (Paid: {paid_date} by {marked_by})")
        if len(paid) > 10:
            print(f"         ... and {len(paid) - 10} more")

    # Now analyze each payment from the inbox
    print("\n\n2. ANALYZING EACH PAYMENT FROM YOUR INBOX:")
    print("-"*100)

    for payment_name, payment_amount in PAYMENT_NAMES:
        print(f"\n{'='*100}")
        print(f"Payment: {payment_name} - ${payment_amount:.2f}")
        print(f"{'='*100}")

        # Check for unpaid passports with this amount
        all_unpaid = Passport.query.filter_by(paid=False).all()
        unpaid_for_amount = [p for p in all_unpaid if float(p.sold_amt) == payment_amount]

        print(f"\n   Step 1: Unpaid passports for ${payment_amount:.2f}:")
        if not unpaid_for_amount:
            print(f"      ❌ NONE FOUND - This is why it can't match!")
        else:
            print(f"      ✅ Found {len(unpaid_for_amount)} unpaid passports:")
            for p in unpaid_for_amount:
                print(f"         - {p.user.name}")

        # Check for paid passports with similar name
        all_paid = Passport.query.filter_by(paid=True).all()
        paid_for_amount = [p for p in all_paid if float(p.sold_amt) == payment_amount]

        print(f"\n   Step 2: Checking if PAID passport exists with similar name:")
        if paid_for_amount:
            best_match = None
            best_score = 0
            for p in paid_for_amount:
                score = fuzz.ratio(payment_name.lower(), p.user.name.lower())
                if score > best_score:
                    best_score = score
                    best_match = p
                if score >= 70:  # Show high matches
                    paid_date = p.paid_date.strftime("%Y-%m-%d") if p.paid_date else "Unknown"
                    print(f"         - {p.user.name} (Match: {score}%, Paid: {paid_date})")

            if best_score >= 85:
                print(f"\n      ⚠️  LIKELY EXPLANATION: This passport was manually marked as PAID")
                print(f"         Best match: {best_match.user.name} ({best_score}%)")
                print(f"         Marked paid by: {best_match.marked_paid_by or 'Unknown'}")
                print(f"         Paid date: {best_match.paid_date.strftime('%Y-%m-%d') if best_match.paid_date else 'Unknown'}")

        # Check if unpaid exists with similar name (different amount)
        print(f"\n   Step 3: Checking if unpaid passport exists with DIFFERENT amount:")
        all_unpaid_any_amount = Passport.query.filter_by(paid=False).all()
        similar_unpaid = []
        for p in all_unpaid_any_amount:
            score = fuzz.ratio(payment_name.lower(), p.user.name.lower())
            if score >= 70:
                similar_unpaid.append((p, score))

        if similar_unpaid:
            print(f"      ⚠️  Found {len(similar_unpaid)} unpaid passports with similar names:")
            for p, score in sorted(similar_unpaid, key=lambda x: x[1], reverse=True):
                print(f"         - {p.user.name} (Match: {score}%, Amount: ${p.sold_amt:.2f})")
                if score >= 85:
                    print(f"           ⚠️  This might be a price mismatch issue!")
        else:
            print(f"      ❌ No unpaid passports found with similar names")

        # Final verdict
        print(f"\n   VERDICT:")
        if not unpaid_for_amount and not similar_unpaid:
            print(f"      🔴 NO MATCHING PASSPORT EXISTS (unpaid or similar name)")
            print(f"         → Either passport doesn't exist, or was manually marked as PAID")
        elif not unpaid_for_amount and similar_unpaid:
            print(f"      🟡 PASSPORT EXISTS but WRONG PRICE")
            print(f"         → Payment is ${payment_amount:.2f} but passport is ${similar_unpaid[0][0].sold_amt:.2f}")
        elif unpaid_for_amount:
            # Try fuzzy matching
            best_match_score = 0
            for p in unpaid_for_amount:
                score = fuzz.ratio(payment_name.lower(), p.user.name.lower())
                if score > best_match_score:
                    best_match_score = score

            if best_match_score >= 85:
                print(f"      🟢 SHOULD MATCH (Score: {best_match_score}%)")
                print(f"         → Bot should have matched this. Check fuzzy matching logic!")
            else:
                print(f"      🟡 UNPAID PASSPORT EXISTS but NAME TOO DIFFERENT")
                print(f"         → Best match score: {best_match_score}% (threshold: 85%)")
                print(f"         → This is a legitimate NO_MATCH - names are too different")

    print("\n\n3. SUMMARY:")
    print("-"*100)
    print(f"Total payments in inbox: {len(PAYMENT_NAMES)}")
    print(f"Total unpaid passports in database: {len(all_unpaid)}")
    print(f"\nThis report shows WHY each payment failed to match.")
    print("Look for 🔴 and 🟡 verdicts to understand the issues.")
    print("="*100)
