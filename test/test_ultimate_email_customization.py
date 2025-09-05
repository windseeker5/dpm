"""
CRITICAL: All tests MUST send real emails to kdresdell@gmail.com
This is the ONLY way to verify attachments are fixed
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Activity, Signup, Passport, PassportType, User, Income
from utils import notify_signup_event, notify_pass_event
from datetime import datetime, timezone
import json

# Test configuration
TEST_EMAIL = "kdresdell@gmail.com"  # Ken's personal email - REQUIRED
TEST_USER_NAME = "Test User - Ultimate Email Test"

def test_all_email_templates():
    """
    Test ALL 4 email templates with real email delivery
    MUST verify NO ATTACHMENTS in any email
    """
    
    with app.app_context():
        print("\n" + "="*60)
        print("ULTIMATE EMAIL TEMPLATE TEST")
        print("Sending to: " + TEST_EMAIL)
        print("="*60)
        
        # Get test activities (Hockey=1, Golf=3, Poker=4)
        activities = Activity.query.filter(Activity.id.in_([1, 3, 4])).all()
        
        if not activities:
            print("❌ ERROR: No test activities found. Expected IDs 1, 3, 4")
            return
        
        for activity in activities:
            print(f"\n📧 Testing Activity {activity.id}: {activity.name}")
            
            # Test 1: SIGNUP EMAIL
            print("  1️⃣ Testing Signup Email...")
            test_signup_email(activity)
            
            # Test 2: NEW PASS EMAIL  
            print("  2️⃣ Testing New Pass Email...")
            test_new_pass_email(activity)
            
            # Test 3: PAYMENT RECEIVED EMAIL
            print("  3️⃣ Testing Payment Received Email...")
            test_payment_email(activity)
            
            # Test 4: LATE PAYMENT EMAIL
            print("  4️⃣ Testing Late Payment Email...")
            test_late_payment_email(activity)
            
        print("\n" + "="*60)
        print("✅ ALL EMAILS SENT TO: " + TEST_EMAIL)
        print("CHECK FOR:")
        print("  - NO attachments (all images inline)")
        print("  - Activity images as heroes (except signup)")
        print("  - Professional circular styling")
        print("="*60)

def test_signup_email(activity):
    """Test signup email with celebration hero (not activity image)"""
    try:
        user = get_or_create_test_user()
        signup = Signup(
            user_id=user.id,
            activity_id=activity.id,
            subject=f"Ultimate Test - Signup - {activity.name}",
            signed_up_at=datetime.now(timezone.utc)
        )
        db.session.add(signup)
        db.session.commit()
        
        # Send email
        with app.test_request_context():
            notify_signup_event(app, signup=signup, activity=activity)
        print(f"    ✅ Signup email sent for {activity.name}")
        
    except Exception as e:
        print(f"    ❌ Signup email failed for {activity.name}: {e}")

def test_new_pass_email(activity):
    """Test new pass email with activity hero"""
    try:
        user = get_or_create_test_user()
        passport_data = create_test_passport(user, activity)
        
        # Send new pass email within request context
        with app.test_request_context('/', base_url='http://localhost:5000'):
            notify_pass_event(
                app,
                event_type='pass_created',
                pass_data=passport_data,
                activity=activity,
                admin_email=app.config.get('ADMIN_EMAIL', 'admin@minipass.com')
            )
        print(f"    ✅ New Pass email sent for {activity.name}")
        
    except Exception as e:
        print(f"    ❌ New Pass email failed for {activity.name}: {e}")

def test_payment_email(activity):
    """Test payment received email with activity hero"""
    try:
        user = get_or_create_test_user()
        passport_data = create_test_passport(user, activity, paid=True)
        
        # Send payment received email within request context
        with app.test_request_context('/', base_url='http://localhost:5000'):
            notify_pass_event(
                app,
                event_type='payment_received',
                pass_data=passport_data,
                activity=activity,
                admin_email=app.config.get('ADMIN_EMAIL', 'admin@minipass.com')
            )
        print(f"    ✅ Payment Received email sent for {activity.name}")
        
    except Exception as e:
        print(f"    ❌ Payment email failed for {activity.name}: {e}")

def test_late_payment_email(activity):
    """Test late payment email with activity hero"""
    try:
        user = get_or_create_test_user()
        passport_data = create_test_passport(user, activity, paid=False)
        
        # Send late payment email within request context
        with app.test_request_context('/', base_url='http://localhost:5000'):
            notify_pass_event(
                app,
                event_type='payment_late',
                pass_data=passport_data,
                activity=activity,
                admin_email=app.config.get('ADMIN_EMAIL', 'admin@minipass.com')
            )
        print(f"    ✅ Late Payment email sent for {activity.name}")
        
    except Exception as e:
        print(f"    ❌ Late Payment email failed for {activity.name}: {e}")

def get_or_create_test_user():
    """Get or create test user for email testing"""
    user = User.query.filter_by(email=TEST_EMAIL).first()
    if not user:
        user = User(
            name=TEST_USER_NAME,
            email=TEST_EMAIL,
            phone_number="+1(514)555-0001"
        )
        db.session.add(user)
        db.session.commit()
        print(f"✅ Created test user: {TEST_EMAIL}")
    return user

def create_test_passport(user, activity, paid=False):
    """Create test passport for email testing"""
    # Get or create passport type
    passport_type = PassportType.query.filter_by(activity_id=activity.id).first()
    if not passport_type:
        passport_type = PassportType(
            activity_id=activity.id,
            name=f"Test Pass - {activity.name}",
            type="permanent",
            price_per_user=25.00,
            sessions_included=5,
            created_dt=datetime.now(timezone.utc)
        )
        db.session.add(passport_type)
        db.session.commit()
    
    # Generate unique pass code
    import random
    import string
    pass_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Create passport
    passport = Passport(
        pass_code=pass_code,
        user_id=user.id,
        passport_type_id=passport_type.id,
        activity_id=activity.id,
        passport_type_name=passport_type.name,
        sold_amt=passport_type.price_per_user,
        uses_remaining=passport_type.sessions_included,
        paid=paid,
        created_dt=datetime.now(timezone.utc)
    )
    if paid:
        passport.paid_date = datetime.now(timezone.utc)
        passport.marked_paid_by = "test_system"
    
    db.session.add(passport)
    db.session.commit()
    
    # Create income record if paid
    if paid:
        income = Income(
            activity_id=activity.id,
            amount=passport_type.price_per_user,
            category='passport_sale',
            note=f'Test payment for passport {passport.pass_code}',
            created_by='test_system',
            date=datetime.now(timezone.utc)
        )
        db.session.add(income)
        db.session.commit()
    
    return passport

if __name__ == "__main__":
    print("🚀 Starting Ultimate Email Template Customization Test")
    print(f"Target Email: {TEST_EMAIL}")
    print("Expected: 12 total emails (3 activities × 4 templates)")
    test_all_email_templates()
    print("🎯 Test Complete - Check email for NO ATTACHMENTS!")