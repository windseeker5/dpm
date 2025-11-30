#!/usr/bin/env python3
"""
Generate EbankPayment records for demo database
Shows the automated Canadian e-transfer matching feature
"""

import random
from datetime import datetime, timedelta, timezone
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Passport, User, EbankPayment


def name_to_bank_format(name):
    """Convert name to bank format (UPPERCASE, no accents)"""
    # Remove common accents
    replacements = {
        'é': 'E', 'è': 'E', 'ê': 'E', 'ë': 'E',
        'à': 'A', 'â': 'A', 'ä': 'A',
        'î': 'I', 'ï': 'I',
        'ô': 'O', 'ö': 'O',
        'ù': 'U', 'û': 'U', 'ü': 'U',
        'ç': 'C',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'À': 'A', 'Â': 'A', 'Ä': 'A',
        'Î': 'I', 'Ï': 'I',
        'Ô': 'O', 'Ö': 'O',
        'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C'
    }
    result = name.upper()
    for old, new in replacements.items():
        result = result.replace(old, new)
    # Sometimes banks drop hyphens
    if random.random() < 0.3:
        result = result.replace('-', ' ')
    return result


def generate_ebank_payments():
    """Generate e-bank payment records based on existing demo passports"""

    print("Generating EbankPayment records...")

    # Get paid passports to create matching records
    paid_passports = Passport.query.filter_by(paid=True).all()
    random.shuffle(paid_passports)

    matched_count = 0
    no_match_count = 0
    manual_count = 0

    # Take a sample of paid passports for e-transfer records
    sample_size = min(120, len(paid_passports))
    sampled_passports = paid_passports[:sample_size]

    for passport in sampled_passports:
        user = db.session.get(User, passport.user_id)
        bank_name = name_to_bank_format(user.name)

        # Determine result type based on distribution
        rand = random.random()

        if rand < 0.55:  # 55% MATCHED
            result = "MATCHED"
            name_score = random.uniform(94, 100)
            matched_name = user.name
            matched_amt = passport.sold_amt
            matched_pass_id = passport.id
            mark_as_paid = True
            matched_count += 1
        elif rand < 0.95:  # 40% MANUAL_PROCESSED
            result = "MANUAL_PROCESSED"
            name_score = 0
            matched_name = None
            matched_amt = None
            matched_pass_id = None
            mark_as_paid = False
            manual_count += 1
        else:  # 5% NO_MATCH
            result = "NO_MATCH"
            name_score = 0
            matched_name = None
            matched_amt = None
            matched_pass_id = None
            mark_as_paid = False
            no_match_count += 1

        # Create timestamp around when passport was paid
        if passport.paid_date:
            timestamp = passport.paid_date - timedelta(hours=random.randint(1, 48))
        else:
            timestamp = passport.created_dt + timedelta(days=random.randint(1, 5))

        payment = EbankPayment(
            timestamp=timestamp,
            from_email="notify@payments.interac.ca",
            subject=f"INTERAC e-Transfer: {bank_name} sent you money",
            bank_info_name=bank_name,
            bank_info_amt=passport.sold_amt,
            matched_pass_id=matched_pass_id,
            matched_name=matched_name,
            matched_amt=matched_amt,
            name_score=name_score,
            result=result,
            mark_as_paid=mark_as_paid,
            email_received_date=timestamp - timedelta(minutes=random.randint(1, 30))
        )
        db.session.add(payment)

    # Add a few extra NO_MATCH records with fake names (payments that don't exist in system)
    fake_names = [
        "JEAN TREMBLAY", "MARIE GAGNON", "PIERRE COTE",
        "SYLVIE ROY", "MICHEL BOUCHARD"
    ]
    for fake_name in fake_names:
        payment = EbankPayment(
            timestamp=datetime.now(timezone.utc) - timedelta(days=random.randint(5, 30)),
            from_email="notify@payments.interac.ca",
            subject=f"INTERAC e-Transfer: {fake_name} sent you money",
            bank_info_name=fake_name,
            bank_info_amt=random.choice([15.0, 25.0, 50.0, 100.0]),
            matched_pass_id=None,
            matched_name=None,
            matched_amt=None,
            name_score=0,
            result="NO_MATCH",
            mark_as_paid=False,
            email_received_date=datetime.now(timezone.utc) - timedelta(days=random.randint(5, 30))
        )
        db.session.add(payment)
        no_match_count += 1

    db.session.commit()

    return {
        'matched': matched_count,
        'manual': manual_count,
        'no_match': no_match_count
    }


def main():
    """Main function"""
    print("=" * 50)
    print("EBANK PAYMENT GENERATOR")
    print("=" * 50)
    print()

    with app.app_context():
        # Check if there are already records
        existing = EbankPayment.query.count()
        if existing > 0:
            print(f"Warning: {existing} existing ebank payments found. Clearing them first...")
            EbankPayment.query.delete()
            db.session.commit()

        # Generate records
        counts = generate_ebank_payments()

        # Summary
        total = EbankPayment.query.count()

        print()
        print("=" * 50)
        print("GENERATION COMPLETE")
        print("=" * 50)
        print(f"\nEbankPayment records by result:")
        print(f"  ✅ MATCHED:          {counts['matched']}")
        print(f"  🔧 MANUAL_PROCESSED: {counts['manual']}")
        print(f"  ❌ NO_MATCH:         {counts['no_match']}")
        print(f"\n  TOTAL: {total} payment records")

        # Show recent samples
        print("\nRecent payment samples:")
        recent = EbankPayment.query.order_by(EbankPayment.timestamp.desc()).limit(10).all()
        for p in recent:
            status = "✅" if p.result == "MATCHED" else ("🔧" if p.result == "MANUAL_PROCESSED" else "❌")
            print(f"  {status} {p.bank_info_name[:25]:25} ${p.bank_info_amt:>6.2f} -> {p.result}")


if __name__ == "__main__":
    main()
