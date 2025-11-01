#!/usr/bin/env python3
"""Debug script to analyze payment matching issues"""

from app import app
from models import db, Passport, EbankPayment, User

with app.app_context():
    # Check unpaid passports for $50
    print('=' * 80)
    print('UNPAID PASSPORTS FOR $50.00:')
    print('=' * 80)
    unpaid_50 = Passport.query.join(User).filter(
        Passport.sold_amt == 50.00,
        Passport.paid == False
    ).all()

    for p in unpaid_50[:10]:  # Show first 10
        print(f'ID: {p.id} | Name: {p.user.name:30} | Paid: {p.paid} | Amount: ${p.sold_amt}')

    print(f'\nTotal unpaid $50 passports: {len(unpaid_50)}')

    # Check ebank_payment records
    print('\n' + '=' * 80)
    print('RECENT NO_MATCH PAYMENTS:')
    print('=' * 80)
    no_match = EbankPayment.query.filter_by(status='NO_MATCH').order_by(EbankPayment.timestamp.desc()).limit(15).all()

    for payment in no_match:
        reason_short = payment.reason[:80] if payment.reason else "No reason"
        print(f'Sender: {payment.sender_name:25} | Amount: ${payment.amount:6.2f} | Reason: {reason_short}')

    print(f'\nTotal NO_MATCH payments: {EbankPayment.query.filter_by(status="NO_MATCH").count()}')
    print(f'Total MATCHED payments: {EbankPayment.query.filter_by(status="MATCHED").count()}')

    # Check specific examples
    print('\n' + '=' * 80)
    print('CHECKING SPECIFIC PAYMENT EXAMPLES:')
    print('=' * 80)

    # Example: SAMUEL TURBIDE
    print('\n1. SAMUEL TURBIDE ($50):')
    samuel_passports = Passport.query.join(User).filter(
        Passport.sold_amt == 50.00,
        Passport.paid == False,
        db.or_(
            User.name.ilike('%samuel%'),
            User.name.ilike('%turbide%')
        )
    ).all()
    print(f'   Found {len(samuel_passports)} passports with "samuel" or "turbide" in name')
    for p in samuel_passports:
        print(f'   - {p.user.name} (${p.sold_amt})')

    # Example: YANNICK DRAPEAU
    print('\n2. YANNICK DRAPEAU ($50):')
    yannick_passports = Passport.query.join(User).filter(
        Passport.sold_amt == 50.00,
        Passport.paid == False,
        db.or_(
            User.name.ilike('%yannick%'),
            User.name.ilike('%drapeau%')
        )
    ).all()
    print(f'   Found {len(yannick_passports)} passports with "yannick" or "drapeau" in name')
    for p in yannick_passports:
        print(f'   - {p.user.name} (${p.sold_amt})')

    # Check ALL unpaid passport names
    print('\n' + '=' * 80)
    print('ALL UNPAID $50 PASSPORT HOLDER NAMES:')
    print('=' * 80)
    for p in unpaid_50:
        print(f'{p.user.name}')
