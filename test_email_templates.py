#!/usr/bin/env python3
"""
Email Template Testing Script
============================

This script sends all 6 email templates for Activity #4 (Surf Sess) to a test email address.
Used for debugging email template customization without creating new activities/passports.

Templates tested:
1. signup - New signup confirmation
2. paymentReceived - Payment confirmation
3. newPass - New passport created
4. redeemPass - Passport redemption
5. latePayment - Late payment reminder
6. email_survey_invitation - Survey invitation

Usage: python test_email_templates.py
"""

import sys
import os
from datetime import datetime, timezone
import json

# Add the current directory to Python path
sys.path.append('.')

from app import app
from models import Activity, User, Passport, PassportType, Signup
from utils import send_email_async, get_email_context, render_and_send_email

def create_test_user():
    """Create or get a test user for email testing."""
    with app.app_context():
        # Try to find existing test user first
        test_user = User.query.filter_by(email='cadresdale@test.com').first()

        if not test_user:
            # Create new test user
            test_user = User(
                name='Test User for Email Templates',
                email='cadresdale@test.com',
                phone_number='555-0123'
            )
            from models import db
            db.session.add(test_user)
            db.session.commit()
            print(f"✅ Created test user: {test_user.name} ({test_user.email})")
        else:
            print(f"✅ Using existing test user: {test_user.name} ({test_user.email})")

        return test_user

def create_test_passport_and_signup(activity, user):
    """Create test passport and signup data for email templates."""
    with app.app_context():
        from models import db

        # Get or create a passport type for the activity
        passport_type = PassportType.query.filter_by(activity_id=activity.id).first()

        if not passport_type:
            passport_type = PassportType(
                activity_id=activity.id,
                name='Test Regular Pass',
                type='permanent',
                price_per_user=25.0,
                sessions_included=10,
                target_revenue=500.0,
                payment_instructions='Send e-transfer to test@minipass.me',
                status='active'
            )
            db.session.add(passport_type)
            db.session.commit()
            print(f"✅ Created test passport type: {passport_type.name}")
        else:
            print(f"✅ Using existing passport type: {passport_type.name}")

        # Create a test signup
        test_signup = Signup.query.filter_by(
            activity_id=activity.id,
            user_id=user.id
        ).first()

        if not test_signup:
            test_signup = Signup(
                activity_id=activity.id,
                user_id=user.id,
                passport_type_id=passport_type.id,
                subject='Test Signup for Email Templates',
                description='Test signup for email template debugging',
                signed_up_at=datetime.now(timezone.utc),
                paid=True,
                paid_at=datetime.now(timezone.utc),
                status='completed'
            )
            db.session.add(test_signup)
            db.session.commit()
            print(f"✅ Created test signup for user {user.name}")
        else:
            print(f"✅ Using existing test signup for user {user.name}")

        # Create a test passport
        test_passport = Passport.query.filter_by(
            activity_id=activity.id,
            user_id=user.id
        ).first()

        if not test_passport:
            import uuid
            test_passport = Passport(
                activity_id=activity.id,
                user_id=user.id,
                passport_type_id=passport_type.id,
                pass_code=str(uuid.uuid4())[:8].upper(),
                sold_amt=passport_type.price_per_user,
                uses_remaining=passport_type.sessions_included,
                created_dt=datetime.now(timezone.utc),
                paid=True,
                paid_date=datetime.now(timezone.utc),
                notes='Test passport for email template debugging'
            )
            db.session.add(test_passport)
            db.session.commit()
            print(f"✅ Created test passport: {test_passport.pass_code}")
        else:
            print(f"✅ Using existing test passport: {test_passport.pass_code}")

        return passport_type, test_signup, test_passport

def send_test_emails():
    """Send all 6 email templates to the test email address."""

    # Override the email address to send to cadresdale
    test_email = 'cadresdale@gmail.com'

    with app.app_context():
        # Get Activity #4
        activity = Activity.query.get(4)
        if not activity:
            print("❌ Activity #4 not found")
            return

        print(f"📧 Testing email templates for Activity #{activity.id}: {activity.name}")
        print(f"📧 All emails will be sent to: {test_email}")
        print("=" * 60)

        # Create test user and related data
        test_user = create_test_user()
        passport_type, signup, passport = create_test_passport_and_signup(activity, test_user)

        # Pre-extract values to avoid session issues
        user_name = test_user.name
        activity_name = activity.name
        passport_code = passport.pass_code
        passport_price = passport_type.price_per_user
        passport_type_name = passport_type.name
        payment_instructions = passport_type.payment_instructions or "Send e-transfer to admin@example.com"
        signup_date = signup.signed_up_at.strftime('%B %d, %Y')
        uses_remaining = passport.uses_remaining

        # 1. SIGNUP EMAIL
        print("\n1️⃣ Sending SIGNUP email...")
        try:
            send_email_async(
                app=app,
                user=test_user,
                activity=activity,
                subject=f"Welcome to {activity_name}!",
                to_email=test_email,
                template_name='signup',
                context={
                    'user_name': user_name,
                    'activity_name': activity_name,
                    'signup_date': signup_date,
                    'payment_amount': f"${passport_price:.2f}",
                    'passport_type': passport_type_name
                }
            )
            print("   ✅ SIGNUP email queued successfully")
        except Exception as e:
            print(f"   ❌ SIGNUP email failed: {e}")

        # 2. PAYMENT RECEIVED EMAIL
        print("\n2️⃣ Sending PAYMENT RECEIVED email...")
        try:
            send_email_async(
                app=app,
                user=test_user,
                activity=activity,
                subject=f"Payment Confirmed - {activity_name}",
                to_email=test_email,
                template_name='paymentReceived',
                context={
                    'user_name': user_name,
                    'activity_name': activity_name,
                    'payment_amount': f"${passport_price:.2f}",
                    'payment_date': datetime.now(timezone.utc).strftime('%B %d, %Y'),
                    'passport_type': passport_type_name
                }
            )
            print("   ✅ PAYMENT RECEIVED email queued successfully")
        except Exception as e:
            print(f"   ❌ PAYMENT RECEIVED email failed: {e}")

        # 3. NEW PASS EMAIL
        print("\n3️⃣ Sending NEW PASS email...")
        try:
            send_email_async(
                app=app,
                user=test_user,
                activity=activity,
                subject=f"Your {activity_name} Pass is Ready!",
                to_email=test_email,
                template_name='newPass',
                context={
                    'user_name': user_name,
                    'activity_name': activity_name,
                    'pass_code': passport_code,
                    'sessions_remaining': uses_remaining,
                    'passport_type': passport_type_name,
                    'qr_code_url': f'https://minipass.me/pass/{passport_code}'
                }
            )
            print("   ✅ NEW PASS email queued successfully")
        except Exception as e:
            print(f"   ❌ NEW PASS email failed: {e}")

        # 4. REDEEM PASS EMAIL
        print("\n4️⃣ Sending REDEEM PASS email...")
        try:
            # Simulate a redemption
            redeemed_sessions = 1
            remaining_sessions = uses_remaining - redeemed_sessions

            send_email_async(
                app=app,
                user=test_user,
                activity=activity,
                subject=f"Pass Used - {activity_name}",
                to_email=test_email,
                template_name='redeemPass',
                context={
                    'user_name': user_name,
                    'activity_name': activity_name,
                    'pass_code': passport_code,
                    'sessions_used': redeemed_sessions,
                    'sessions_remaining': remaining_sessions,
                    'redemption_date': datetime.now(timezone.utc).strftime('%B %d, %Y at %I:%M %p'),
                    'passport_type': passport_type_name
                }
            )
            print("   ✅ REDEEM PASS email queued successfully")
        except Exception as e:
            print(f"   ❌ REDEEM PASS email failed: {e}")

        # 5. LATE PAYMENT EMAIL
        print("\n5️⃣ Sending LATE PAYMENT email...")
        try:
            # Create a scenario for late payment
            days_overdue = 7

            send_email_async(
                app=app,
                user=test_user,
                activity=activity,
                subject=f"Payment Reminder - {activity_name}",
                to_email=test_email,
                template_name='latePayment',
                context={
                    'user_name': user_name,
                    'activity_name': activity_name,
                    'payment_amount': f"${passport_price:.2f}",
                    'days_overdue': days_overdue,
                    'due_date': (datetime.now(timezone.utc)).strftime('%B %d, %Y'),
                    'payment_instructions': payment_instructions,
                    'passport_type': passport_type_name
                }
            )
            print("   ✅ LATE PAYMENT email queued successfully")
        except Exception as e:
            print(f"   ❌ LATE PAYMENT email failed: {e}")

        # 6. SURVEY INVITATION EMAIL
        print("\n6️⃣ Sending SURVEY INVITATION email...")
        try:
            # Create survey invitation context
            survey_url = f"https://minipass.me/survey/test-survey-{activity.id}"

            send_email_async(
                app=app,
                user=test_user,
                activity=activity,
                subject=f"How was your {activity_name} experience?",
                to_email=test_email,
                template_name='email_survey_invitation',
                context={
                    'user_name': user_name,
                    'activity_name': activity_name,
                    'survey_url': survey_url,
                    'activity_type': activity.type,
                    'completion_estimate': '3 minutes'
                }
            )
            print("   ✅ SURVEY INVITATION email queued successfully")
        except Exception as e:
            print(f"   ❌ SURVEY INVITATION email failed: {e}")

        print("\n" + "=" * 60)
        print("📧 Email Template Testing Complete!")
        print(f"📬 All 6 templates have been queued for delivery to: {test_email}")
        print("📝 Check your email inbox (including spam folder) for the test emails.")
        print("🔧 Use these emails to debug and verify template customizations.")

def main():
    """Main function to run the email template tests."""
    print("🔧 Email Template Testing Script")
    print("================================")
    print("This script will send all 6 email templates for Activity #4")
    print("to cadresdale@gmail.com for debugging purposes.")

    try:
        send_test_emails()
    except Exception as e:
        print(f"❌ Script failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()