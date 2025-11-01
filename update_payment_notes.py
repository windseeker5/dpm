#!/usr/bin/env python3
"""
Script to update existing NO_MATCH payment records with detailed, accurate notes.
This will retroactively fix all the "bullshit" generic notes with real diagnostic information.
"""

from app import app
from models import db, Passport, EbankPayment, User
import unicodedata
from rapidfuzz import fuzz
from datetime import datetime, timezone

def normalize_name(text):
    """Remove accents and normalize text for better matching"""
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents.lower().strip()

with app.app_context():
    print('=' * 80)
    print('UPDATING PAYMENT NOTES - RETROACTIVE FIX')
    print('=' * 80)

    # Get all NO_MATCH payments
    no_match_payments = EbankPayment.query.filter_by(result='NO_MATCH').all()

    print(f'\nFound {len(no_match_payments)} NO_MATCH payment records to analyze')

    updated_count = 0
    threshold = 85  # Default threshold

    for payment in no_match_payments:
        name = payment.bank_info_name
        amt = payment.bank_info_amt
        email_received_date = payment.email_received_date

        print(f'\nAnalyzing: {name} - ${amt}')

        # Convert to float for comparison
        payment_amount = float(amt)

        # Get all unpaid passports with this amount
        all_unpaid = Passport.query.filter_by(paid=False).all()
        unpaid_passports = [p for p in all_unpaid if float(p.sold_amt) == payment_amount]

        new_note = None

        if not unpaid_passports:
            # Check if there's a PAID passport with matching name/amount
            all_paid = Passport.query.filter_by(paid=True).all()
            paid_passports_same_amount = [p for p in all_paid if float(p.sold_amt) == payment_amount]

            normalized_payment_name = normalize_name(name)

            matching_paid_passport = None
            for p in paid_passports_same_amount:
                if not p.user:
                    continue
                normalized_passport_name = normalize_name(p.user.name)
                score = fuzz.ratio(normalized_payment_name, normalized_passport_name)
                if score >= 95:  # Very close match
                    matching_paid_passport = p
                    break

            if matching_paid_passport:
                # FOUND THE REAL REASON - Already paid!
                paid_by = matching_paid_passport.marked_paid_by or "unknown admin"
                paid_date_str = matching_paid_passport.paid_date.strftime("%Y-%m-%d %H:%M") if matching_paid_passport.paid_date else "unknown date"

                time_diff_info = ""
                if matching_paid_passport.paid_date and email_received_date:
                    diff_seconds = (email_received_date - matching_paid_passport.paid_date).total_seconds()
                    if diff_seconds > 0:
                        diff_minutes = int(diff_seconds / 60)
                        time_diff_info = f" ({diff_minutes} min after passport marked paid)"
                    else:
                        diff_minutes = int(abs(diff_seconds) / 60)
                        time_diff_info = f" ({diff_minutes} min before email received)"

                new_note = f"MATCH FOUND: {matching_paid_passport.user.name} (${payment_amount:.2f}, Passport #{matching_paid_passport.id}) - Already marked PAID by {paid_by} on {paid_date_str}{time_diff_info}"
                print(f'  ✅ Found matching PAID passport - marked by {paid_by}')
            else:
                # Genuinely no passport at this amount
                available_amounts = list(set(float(p.sold_amt) for p in all_unpaid))
                available_amounts.sort()
                amounts_summary = ", ".join([f"${a:.2f}({sum(1 for p in all_unpaid if float(p.sold_amt) == a)})" for a in available_amounts[:5]])

                new_note = f"No unpaid passports for ${payment_amount:.2f}. Payment may have arrived before passport creation. Available unpaid amounts: {amounts_summary}"
                print(f'  ❌ No unpaid passports for this amount')
        else:
            # There ARE unpaid passports - check name matching
            normalized_payment_name = normalize_name(name)

            all_candidates = []
            for p in unpaid_passports:
                if not p.user:
                    continue
                score = fuzz.ratio(normalized_payment_name, normalize_name(p.user.name))
                if score >= 50:
                    all_candidates.append((p.user.name, score))

            all_candidates.sort(key=lambda x: x[1], reverse=True)
            top_candidates = all_candidates[:3]

            # Build detailed note
            note_parts = [f"No match found for '{name}' (${amt})."]
            note_parts.append(f"Found {len(unpaid_passports)} unpaid passport(s) for ${amt}, but")

            if top_candidates:
                candidate_strs = [f"{cname} ({score:.0f}%)" for cname, score in top_candidates]
                note_parts.append(f"all names below {threshold}% threshold. Closest: {', '.join(candidate_strs)}.")
                print(f'  ❌ Name mismatch - closest: {top_candidates[0][0]} ({top_candidates[0][1]}%)')
            else:
                note_parts.append(f"no names above 50% similarity.")
                if unpaid_passports:
                    example_names = [p.user.name for p in unpaid_passports[:3] if p.user]
                    if example_names:
                        note_parts.append(f"Available names: {', '.join(example_names[:3])}")
                print(f'  ❌ No similar names at all')

            new_note = " ".join(note_parts)

        # Update the record if note changed
        if new_note and new_note != payment.note:
            old_note = payment.note[:80] + "..." if len(payment.note or "") > 80 else payment.note
            payment.note = new_note
            updated_count += 1
            print(f'  📝 Updated note')
            print(f'     Old: {old_note}')
            print(f'     New: {new_note[:80]}...' if len(new_note) > 80 else f'     New: {new_note}')

    # Commit all changes
    db.session.commit()

    print(f'\n' + '=' * 80)
    print(f'✅ UPDATE COMPLETE - Updated {updated_count} out of {len(no_match_payments)} records')
    print('=' * 80)
