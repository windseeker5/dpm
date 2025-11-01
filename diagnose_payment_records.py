#!/usr/bin/env python3
"""
Diagnostic script to analyze payment records and identify issues
"""

from app import app
from models import Passport, EbankPayment, db
from datetime import datetime

with app.app_context():
    print("="*80)
    print("PAYMENT RECORDS DIAGNOSTIC REPORT")
    print("="*80)

    # Check paid passports
    all_paid = Passport.query.filter_by(paid=True).all()
    with_marked_by = [p for p in all_paid if p.marked_paid_by]
    without_marked_by = [p for p in all_paid if not p.marked_paid_by]

    print(f"\n📊 PASSPORT STATISTICS:")
    print(f"   Total paid passports: {len(all_paid)}")
    print(f"   With marked_paid_by set: {len(with_marked_by)}")
    print(f"   Without marked_paid_by (NULL): {len(without_marked_by)}")
    print(f"   Missing audit trail: {len(without_marked_by)/len(all_paid)*100:.1f}%")

    # Check who marked them
    if with_marked_by:
        marked_by_counts = {}
        for p in with_marked_by:
            marked_by_counts[p.marked_paid_by] = marked_by_counts.get(p.marked_paid_by, 0) + 1

        print(f"\n📝 WHO MARKED PASSPORTS AS PAID:")
        for who, count in sorted(marked_by_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {who}: {count} passport(s)")

    # Check EbankPayment records
    all_ebank = EbankPayment.query.all()
    matched = [e for e in all_ebank if e.result == "MATCHED"]
    no_match = [e for e in all_ebank if e.result == "NO_MATCH"]

    print(f"\n📊 EBANKPAYMENT STATISTICS:")
    print(f"   Total records: {len(all_ebank)}")
    print(f"   MATCHED: {len(matched)}")
    print(f"   NO_MATCH: {len(no_match)}")

    # Find recent NO_MATCH records
    recent_no_match = EbankPayment.query.filter_by(result="NO_MATCH").order_by(EbankPayment.timestamp.desc()).limit(5).all()

    if recent_no_match:
        print(f"\n❌ RECENT NO_MATCH RECORDS:")
        for e in recent_no_match:
            print(f"   {e.timestamp}: {e.bank_info_name} - ${e.bank_info_amt}")
            print(f"      Note: {e.note[:100]}...")

    # Find passports paid without marked_paid_by in last 30 days
    from datetime import timedelta, timezone
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_null = []
    for p in without_marked_by:
        if p.paid_date:
            # Ensure paid_date is timezone-aware
            pd = p.paid_date if p.paid_date.tzinfo else p.paid_date.replace(tzinfo=timezone.utc)
            if pd > thirty_days_ago:
                recent_null.append(p)

    if recent_null:
        print(f"\n⚠️ RECENTLY PAID PASSPORTS WITHOUT marked_paid_by:")
        for p in recent_null[:10]:
            print(f"   Passport #{p.id} ({p.pass_code})")
            print(f"      User: {p.user.name if p.user else 'NO USER'}")
            print(f"      Amount: ${p.sold_amt}")
            print(f"      Paid date: {p.paid_date}")
            print(f"      marked_paid_by: {repr(p.marked_paid_by)}")

    # Check for the specific three cases user mentioned
    print(f"\n🔍 CHECKING SPECIFIC CASES (Jean Bélanger, Patrick Beland, Samuel Turbide):")

    for name_pattern in ['Jean Bélanger', 'Patrick Beland', 'Samuel Turbide']:
        passports = Passport.query.join(Passport.user).filter(
            db.func.lower(db.text("user.name")).like(f"%{name_pattern.lower()}%")
        ).filter_by(paid=True).all()

        if passports:
            for p in passports:
                print(f"\n   {p.user.name}:")
                print(f"      Passport ID: {p.id}")
                print(f"      Paid: {p.paid}")
                print(f"      Paid date: {p.paid_date}")
                print(f"      marked_paid_by: {repr(p.marked_paid_by)}")

                # Check for matching EbankPayment
                ebank = EbankPayment.query.filter_by(matched_pass_id=p.id).first()
                if ebank:
                    print(f"      EbankPayment: {ebank.result} on {ebank.timestamp}")
                else:
                    print(f"      EbankPayment: NO RECORD FOUND")

    print("\n" + "="*80)
    print("END OF DIAGNOSTIC REPORT")
    print("="*80)
