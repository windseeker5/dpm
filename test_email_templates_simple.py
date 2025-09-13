#!/usr/bin/env python3
"""
Simple Email Template Testing Script
===================================

Uses the existing email notification functions to send all 6 templates
for Activity #4 to cadresdale@gmail.com for debugging.

This leverages the compiled templates and existing business logic.
"""

import sys
sys.path.append('.')

from app import app
from models import Activity, User, Passport, PassportType, Signup
from utils import notify_signup_event, notify_pass_event

def send_all_templates():
    """Send all 6 email templates using existing notification functions."""

    with app.app_context():
        # Get Activity #4
        activity = Activity.query.get(4)
        if not activity:
            print("❌ Activity #4 not found")
            return

        # Get or create test user
        test_user = User.query.filter_by(email='cadresdale@gmail.com').first()
        if not test_user:
            test_user = User(
                name='Test User for Templates',
                email='cadresdale@gmail.com'
            )
            from models import db
            db.session.add(test_user)
            db.session.commit()

        # Get existing passport and signup data
        passport = Passport.query.filter_by(activity_id=4, user_id=test_user.id).first()
        signup = Signup.query.filter_by(activity_id=4, user_id=test_user.id).first()

        if not passport or not signup:
            print("❌ No existing test data found. Run the other script first to create test data.")
            return

        print(f"📧 Testing all templates for Activity #{activity.id}: {activity.name}")
        print(f"📧 Sending to: cadresdale@gmail.com")
        print("=" * 60)

        # 1. SIGNUP EMAIL
        print("1️⃣ Sending SIGNUP email...")
        try:
            notify_signup_event(
                app=app,
                signup=signup,
                activity=activity
            )
            print("   ✅ SIGNUP email sent")
        except Exception as e:
            print(f"   ❌ SIGNUP email failed: {e}")

        # 2. PAYMENT RECEIVED EMAIL
        print("\n2️⃣ Sending PAYMENT RECEIVED email...")
        try:
            notify_pass_event(
                app=app,
                event_type='payment_received',
                pass_data=passport,
                activity=activity
            )
            print("   ✅ PAYMENT RECEIVED email sent")
        except Exception as e:
            print(f"   ❌ PAYMENT RECEIVED email failed: {e}")

        # 3. NEW PASS EMAIL
        print("\n3️⃣ Sending NEW PASS email...")
        try:
            notify_pass_event(
                app=app,
                event_type='pass_created',
                pass_data=passport,
                activity=activity
            )
            print("   ✅ NEW PASS email sent")
        except Exception as e:
            print(f"   ❌ NEW PASS email failed: {e}")

        # 4. REDEEM PASS EMAIL
        print("\n4️⃣ Sending REDEEM PASS email...")
        try:
            notify_pass_event(
                app=app,
                event_type='pass_redeemed',
                pass_data=passport,
                activity=activity
            )
            print("   ✅ REDEEM PASS email sent")
        except Exception as e:
            print(f"   ❌ REDEEM PASS email failed: {e}")

        # 5. LATE PAYMENT EMAIL
        print("\n5️⃣ Sending LATE PAYMENT email...")
        try:
            notify_pass_event(
                app=app,
                event_type='payment_late',
                pass_data=passport,
                activity=activity
            )
            print("   ✅ LATE PAYMENT email sent")
        except Exception as e:
            print(f"   ❌ LATE PAYMENT email failed: {e}")

        # 6. SURVEY INVITATION EMAIL - this one needs special handling
        print("\n6️⃣ SURVEY INVITATION email...")
        print("   ℹ️  Survey invitations are sent through the survey system")
        print("   ℹ️  Use the web interface to test this template")

        print("\n" + "=" * 60)
        print("📧 Template testing complete!")
        print("📬 Check cadresdale@gmail.com for the emails")

if __name__ == '__main__':
    print("🔧 Simple Email Template Testing")
    print("Uses existing notification functions")
    print("=" * 40)
    send_all_templates()