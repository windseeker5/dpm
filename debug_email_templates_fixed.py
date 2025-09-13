#!/usr/bin/env python3
"""
Email Template Debug Script - FIXED VERSION
===========================================

Uses your EXISTING notification functions to send all 6 email templates
for Activity #4 to cadresdale@gmail.com for debugging purposes.

This script leverages your compiled templates and real business logic.
"""

import sys
sys.path.append('.')

from app import app
from models import Activity, User, Passport, PassportType, Signup, db
from utils import notify_signup_event, notify_pass_event, send_email_async
from datetime import datetime, timezone

def main():
    """Main function that runs everything in app context"""

    print("🔧 Email Template Debug Script - FIXED")
    print("=====================================")
    print("Using your EXISTING notification functions")
    print("Target: kdresdell@gmail.com")
    print()

    with app.app_context():
        # Get Activity #4
        activity = Activity.query.get(4)
        if not activity:
            print("❌ Activity #4 not found")
            return

        # Get or create test user with your email
        test_user = User.query.filter_by(email='kdresdell@gmail.com').first()
        if not test_user:
            test_user = User(
                name='Debug Test User',
                email='kdresdell@gmail.com'
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"✅ Created test user: {test_user.name}")

        # Get passport type for activity
        passport_type = PassportType.query.filter_by(activity_id=activity.id).first()
        if not passport_type:
            print("❌ No passport type found for Activity #4")
            return

        # Get or create test signup
        signup = Signup.query.filter_by(activity_id=activity.id, user_id=test_user.id).first()
        if not signup:
            signup = Signup(
                activity_id=activity.id,
                user_id=test_user.id,
                passport_type_id=passport_type.id,
                subject=f'Debug test for {activity.name}',
                signed_up_at=datetime.now(timezone.utc),
                paid=True,
                status='completed'
            )
            db.session.add(signup)
            db.session.commit()
            print(f"✅ Created test signup")

        # Get or create test passport
        passport = Passport.query.filter_by(activity_id=activity.id, user_id=test_user.id).first()
        if not passport:
            import uuid
            passport = Passport(
                activity_id=activity.id,
                user_id=test_user.id,
                passport_type_id=passport_type.id,
                pass_code=str(uuid.uuid4())[:8].upper(),
                sold_amt=passport_type.price_per_user,
                uses_remaining=passport_type.sessions_included,
                paid=True
            )
            db.session.add(passport)
            db.session.commit()
            print(f"✅ Created/using test passport: {passport.pass_code}")

        print(f"\n📧 Testing templates for Activity #{activity.id}: {activity.name}")
        print(f"📧 User: {test_user.name} ({test_user.email})")
        print("=" * 60)

        success_count = 0

        # 1. SIGNUP EMAIL using notify_signup_event
        print("\n1️⃣ Testing SIGNUP template...")
        try:
            notify_signup_event(
                app=app,
                signup=signup,
                activity=activity
            )
            print("   ✅ SIGNUP template sent successfully")
            success_count += 1
        except Exception as e:
            print(f"   ❌ SIGNUP template failed: {e}")

        # 2. PAYMENT RECEIVED EMAIL using notify_pass_event
        print("\n2️⃣ Testing PAYMENT RECEIVED template...")
        try:
            notify_pass_event(
                app=app,
                event_type='payment_received',
                pass_data=passport,
                activity=activity
            )
            print("   ✅ PAYMENT RECEIVED template sent successfully")
            success_count += 1
        except Exception as e:
            print(f"   ❌ PAYMENT RECEIVED template failed: {e}")

        # 3. NEW PASS EMAIL using notify_pass_event
        print("\n3️⃣ Testing NEW PASS template...")
        try:
            notify_pass_event(
                app=app,
                event_type='pass_created',
                pass_data=passport,
                activity=activity
            )
            print("   ✅ NEW PASS template sent successfully")
            success_count += 1
        except Exception as e:
            print(f"   ❌ NEW PASS template failed: {e}")

        # 4. REDEEM PASS EMAIL using notify_pass_event
        print("\n4️⃣ Testing REDEEM PASS template...")
        try:
            notify_pass_event(
                app=app,
                event_type='pass_redeemed',
                pass_data=passport,
                activity=activity
            )
            print("   ✅ REDEEM PASS template sent successfully")
            success_count += 1
        except Exception as e:
            print(f"   ❌ REDEEM PASS template failed: {e}")

        # 5. LATE PAYMENT EMAIL using notify_pass_event
        print("\n5️⃣ Testing LATE PAYMENT template...")
        try:
            notify_pass_event(
                app=app,
                event_type='payment_late',
                pass_data=passport,
                activity=activity
            )
            print("   ✅ LATE PAYMENT template sent successfully")
            success_count += 1
        except Exception as e:
            print(f"   ❌ LATE PAYMENT template failed: {e}")

        # 6. SURVEY INVITATION using send_email_async
        print("\n6️⃣ Testing SURVEY INVITATION template...")
        try:
            survey_url = f"https://minipass.me/survey/debug-test-{activity.id}"

            send_email_async(
                app=app,
                user=test_user,
                activity=activity,
                subject=f"How was your {activity.name} experience?",
                to_email='kdresdell@gmail.com',
                template_name='email_survey_invitation',
                context={
                    'user_name': test_user.name,
                    'activity_name': activity.name,
                    'survey_url': survey_url,
                    'activity_type': activity.type or 'activity'
                }
            )
            print("   ✅ SURVEY INVITATION template sent successfully")
            success_count += 1
        except Exception as e:
            print(f"   ❌ SURVEY INVITATION template failed: {e}")

        # Summary
        total_templates = 6
        print("\n" + "=" * 60)
        print("📊 EMAIL TEMPLATE DEBUG SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully sent: {success_count}/{total_templates} templates")
        print(f"📬 Check your email: kdresdell@gmail.com")
        print(f"📝 Activity tested: #{activity.id} - {activity.name}")
        print("🔧 Uses your existing compiled templates and notification functions")

        if success_count == total_templates:
            print("\n🎉 All templates sent! Check kdresdell@gmail.com for debugging.")
        else:
            print(f"\n⚠️  {total_templates - success_count} templates failed. Check errors above.")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()