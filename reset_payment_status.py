#!/usr/bin/env python3
"""
Reset payment status from MANUAL_PROCESSED back to NO_MATCH
This allows testing the Archive button functionality again
"""

from app import app
from models import EbankPayment, db

def reset_payment_status(name, amount):
    """Reset a payment from MANUAL_PROCESSED back to NO_MATCH"""
    with app.app_context():
        # Find the payment
        payment = EbankPayment.query.filter(
            EbankPayment.bank_info_name == name,
            EbankPayment.bank_info_amt == float(amount),
            EbankPayment.result == "MANUAL_PROCESSED"
        ).order_by(EbankPayment.timestamp.desc()).first()

        if payment:
            old_status = payment.result
            old_note = payment.note

            # Reset status
            payment.result = "NO_MATCH"
            payment.note = (payment.note or "") + " [Status reset from MANUAL_PROCESSED to NO_MATCH for testing]"

            db.session.commit()

            print(f"✅ Reset payment ID {payment.id}")
            print(f"   Name: {payment.bank_info_name}")
            print(f"   Amount: ${payment.bank_info_amt}")
            print(f"   Old Status: {old_status}")
            print(f"   New Status: {payment.result}")
            print(f"   Timestamp: {payment.timestamp}")
            print(f"   Old Note: {old_note}")
            print(f"   New Note: {payment.note}")
            print()
            return True
        else:
            print(f"❌ No MANUAL_PROCESSED payment found for {name} ${amount}")

            # Check if exists with different status
            any_payment = EbankPayment.query.filter(
                EbankPayment.bank_info_name == name,
                EbankPayment.bank_info_amt == float(amount)
            ).order_by(EbankPayment.timestamp.desc()).first()

            if any_payment:
                print(f"   Found payment with status: {any_payment.result}")
            return False

if __name__ == "__main__":
    print("🔄 Resetting payment statuses for testing...\n")

    # Reset Jean-Martin Morin
    print("1️⃣ Jean-Martin Morin:")
    reset_payment_status("Jean Martin Morin", 80)

    # Reset Christian Tremblay
    print("2️⃣ Christian Tremblay:")
    reset_payment_status("CHRISTIAN TREMBLAY", 160)

    print("=" * 70)
    print("✅ Done! Refresh the Payment Bot Matches page to see Archive buttons again.")
    print("=" * 70)
