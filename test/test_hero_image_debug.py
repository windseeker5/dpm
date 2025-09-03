"""
Debug test to verify hero image replacement in signup emails
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from models import db, Signup, Activity, Organization
from app import app
from utils import notify_signup_event

# Create test context
with app.app_context():
    # Get Activity 4
    activity = Activity.query.get(4)
    if not activity:
        print("❌ Activity 4 not found!")
        sys.exit(1)
    
    # Get the latest signup for this activity
    signup = Signup.query.filter_by(activity_id=4).order_by(Signup.id.desc()).first()
    if not signup:
        print("❌ No signup found for Activity 4!")
        sys.exit(1)
    
    # Get user info from the signup
    from models import User
    user = User.query.get(signup.user_id)
    
    print(f"✅ Found signup ID {signup.id}: {user.name} ({user.email})")
    print(f"✅ Activity: {activity.name}")
    
    # Check if hero image exists
    hero_path = os.path.join("static/uploads", f"{activity.id}_hero.png")
    if os.path.exists(hero_path):
        print(f"✅ Hero image exists: {hero_path}")
        print(f"   Size: {os.path.getsize(hero_path)} bytes")
    else:
        print(f"❌ Hero image NOT found: {hero_path}")
    
    # Test the notify_signup_event function with debug output
    print("\n" + "="*60)
    print("TESTING notify_signup_event with Activity 4")
    print("="*60)
    
    # Capture stdout to see debug messages
    import io
    import contextlib
    
    f = io.StringIO()
    with app.test_request_context():
        with contextlib.redirect_stdout(f):
            result = notify_signup_event(
                app,
                signup=signup,
                activity=activity
            )
    
    output = f.getvalue()
    
    # Check for our debug messages
    print("\n📋 Function output:")
    print("-"*40)
    print(output)
    print("-"*40)
    
    # Check for hero image replacement message
    if "Using activity-specific hero image: 4_hero.png" in output:
        print("\n✅ SUCCESS: Hero image replacement code executed!")
        print("   The fix is working - hero image CID was replaced")
    elif "Activity hero image not found" in output:
        print("\n⚠️ WARNING: Hero image file not found")
        print("   The code is working but the hero image file is missing")
    else:
        print("\n❌ FAILURE: Hero image replacement code did NOT execute!")
        print("   The fix may not be working correctly")
    
    # Check if email was attempted
    if "EMAIL SENT SUCCESSFULLY" in output:
        print("\n✅ Email send attempted (may fail if SMTP not configured)")
    elif "FAILED TO SEND EMAIL" in output:
        print("\n⚠️ Email send failed (check SMTP configuration)")
    else:
        print("\n❓ No email send status found in output")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)