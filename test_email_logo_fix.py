#!/usr/bin/env python3
"""
Test that logo appears inline only, not as attachment.
"""

from app import app, db
from models import Passport, Activity
from utils import notify_pass_event

with app.app_context():
    # Get a test passport
    passport = Passport.query.first()
    activity = Activity.query.first()
    
    if passport and activity:
        print(f"Testing email for passport: {passport.pass_code}")
        print(f"Activity: {activity.name}")
        print(f"User email: {passport.user.email}")
        
        # This will send an email with the fix applied
        notify_pass_event(
            app,
            event_type='pass_created',
            pass_data=passport,
            activity=activity
        )
        
        print("\n✅ Email sent! Check if logo appears only inline, not as attachment")
    else:
        print("❌ No passport or activity found to test with")