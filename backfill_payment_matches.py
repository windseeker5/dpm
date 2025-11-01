#!/usr/bin/env python3
"""
Backfill script to fix historical payment matching data.

This script:
1. Finds NO_MATCH records where bot actually found a match (passport already paid)
2. Converts them to MATCHED records with proper passport linkage
3. Updates passport.marked_paid_by = "gmail-bot@system" for audit trail
4. Does NOT send any emails - just fixes the database records

Run this ONCE to clean up historical data from the buggy bot runs.
"""

import sys
import re
from rapidfuzz import fuzz

# Import the Flask app directly (it's already initialized)
from app import app, db
from models import EbankPayment, Passport

with app.app_context():
    print("="*80)
    print("BACKFILL PAYMENT MATCHES - Historical Data Cleanup")
    print("="*80)
    print()

    # Find all NO_MATCH records
    no_match_records = EbankPayment.query.filter_by(result="NO_MATCH").all()
    print(f"📊 Found {len(no_match_records)} NO_MATCH records")
    print()

    # Pattern to extract passport ID from notes like:
    # "MATCH FOUND: Jean Bélanger ($50.00, Passport #90) - Already marked PAID..."
    pattern = r"MATCH FOUND: (.+?) \(\$(.+?), Passport #(\d+)\)"

    converted_count = 0
    skipped_count = 0
    updated_passports = []

    for record in no_match_records:
        if not record.note:
            skipped_count += 1
            continue

        match = re.search(pattern, record.note)
        if match:
            matched_name = match.group(1)
            matched_amt = float(match.group(2))
            passport_id = int(match.group(3))

            # Verify the passport exists
            passport = Passport.query.get(passport_id)
            if not passport:
                print(f"⚠️ Passport #{passport_id} not found, skipping record #{record.id}")
                skipped_count += 1
                continue

            # Verify the passport is actually paid
            if not passport.paid:
                print(f"⚠️ Passport #{passport_id} not marked as paid, skipping record #{record.id}")
                skipped_count += 1
                continue

            print(f"✅ Converting record #{record.id}: {record.bank_info_name} → {matched_name} (Passport #{passport_id})")

            # Convert NO_MATCH to MATCHED
            record.result = "MATCHED"
            record.matched_pass_id = passport_id
            record.matched_name = matched_name
            record.matched_amt = matched_amt
            record.mark_as_paid = True

            # Calculate name score (approximate)
            record.name_score = fuzz.ratio(
                record.bank_info_name.lower().strip(),
                matched_name.lower().strip()
            )

            # Update note to reflect conversion
            record.note = f"Converted from NO_MATCH to MATCHED by backfill script. " \
                         f"Original match: {matched_name} ($%.2f, Passport #%d). " \
                         f"Bot found match but passport was already paid." % (matched_amt, passport_id)

            # Fix passport.marked_paid_by if it's NULL
            if not passport.marked_paid_by:
                passport.marked_paid_by = "gmail-bot@system"
                updated_passports.append(passport_id)
                print(f"   📝 Set passport.marked_paid_by = 'gmail-bot@system'")

            converted_count += 1
        else:
            # This is a genuine NO_MATCH (no match was found)
            skipped_count += 1

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Converted: {converted_count} records from NO_MATCH to MATCHED")
    print(f"⏭️  Skipped: {skipped_count} records (genuine NO_MATCH)")
    print(f"📝 Updated marked_paid_by for {len(updated_passports)} passports")
    print()

    if converted_count > 0:
        print("Updated passports:", sorted(updated_passports))
        print()
        print("💾 Committing changes to database...")
        db.session.commit()
        print("✅ Database updated successfully!")
    else:
        print("ℹ️ No changes needed - database already correct")

    print()
    print("="*80)
    print("VERIFICATION")
    print("="*80)

    # Count final stats
    total_payments = EbankPayment.query.count()
    matched_count = EbankPayment.query.filter_by(result="MATCHED").count()
    no_match_count = EbankPayment.query.filter_by(result="NO_MATCH").count()

    print(f"Total EbankPayment records: {total_payments}")
    print(f"MATCHED: {matched_count}")
    print(f"NO_MATCH: {no_match_count}")
    print()

    # Count passports with/without marked_paid_by
    paid_passports = Passport.query.filter_by(paid=True).count()
    with_marked_by = Passport.query.filter(
        Passport.paid == True,
        Passport.marked_paid_by.isnot(None)
    ).count()
    without_marked_by = Passport.query.filter(
        Passport.paid == True,
        Passport.marked_paid_by.is_(None)
    ).count()

    print(f"Total paid passports: {paid_passports}")
    print(f"With marked_paid_by: {with_marked_by}")
    print(f"Without marked_paid_by: {without_marked_by}")

    if without_marked_by > 0:
        print()
        print(f"⚠️ {without_marked_by} passports still have NULL marked_paid_by")
        print("   These were likely marked paid manually by admin, not by bot")

    print()
    print("="*80)
    print("✅ BACKFILL COMPLETE")
    print("="*80)
