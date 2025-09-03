"""
Create a real signup with Ken's actual email to test email delivery
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Signup, User, Activity
from utils import notify_signup_event
from datetime import datetime, timezone

with app.app_context():
    # Get Activity 4
    activity = Activity.query.get(4)
    print(f"✅ Activity: {activity.name}")
    
    # Create or get user with Ken's real email
    user = User.query.filter_by(email="kdresdell@gmail.com").first()
    if not user:
        user = User(
            name="Ken Dresdell Real Test",
            email="kdresdell@gmail.com",
            phone="+1(514)555-0001"
        )
        db.session.add(user)
        db.session.commit()
        print(f"✅ Created new user: {user.name}")
    else:
        print(f"✅ Found existing user: {user.name}")
    
    # Create a new signup
    signup = Signup(
        user_id=user.id,
        activity_id=activity.id,
        subject=f"Test Signup for {activity.name}",
        description="Testing email with real email address to verify hero image fix",
        signed_up_at=datetime.now(timezone.utc),
        paid=False
    )
    db.session.add(signup)
    db.session.commit()
    print(f"✅ Created signup ID: {signup.id}")
    
    # Send the notification email
    print("\n" + "="*60)
    print(f"SENDING EMAIL TO YOUR REAL ADDRESS: {user.email}")
    print("="*60)
    
    # Use test request context for URL generation
    with app.test_request_context():
        result = notify_signup_event(
            app,
            signup=signup,
            activity=activity
        )
    
    if result:
        print(f"\n✅ EMAIL SENT SUCCESSFULLY TO {user.email}!")
        print("CHECK YOUR INBOX NOW!")
        print("\nExpected email details:")
        print(f"- To: {user.email}")
        print("- Subject: ✍️ Votre inscription est confirmée")
        print("- Should contain Activity 4's hero image (964 bytes)")
        print("\n⚠️ IMPORTANT: Check your SPAM folder if not in inbox!")
    else:
        print(f"\n❌ Failed to send email")
    
    print("\n" + "="*60)
    print("TEST COMPLETE - CHECK YOUR EMAIL NOW!")
    print("="*60)