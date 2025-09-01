#!/usr/bin/env python3
"""
Send email DIRECTLY without async to see errors
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Activity
from datetime import datetime

with app.app_context():
    print("🔍 SENDING EMAIL DIRECTLY (NOT ASYNC)")
    print("=" * 60)
    
    activity = Activity.query.get(2)
    print(f"Activity: {activity.name}")
    
    # Import the actual send_email function (not async)
    from utils import send_email
    
    # Simple test context
    context = {
        'title': 'DIRECT TEST EMAIL',
        'intro_text': 'This is sent DIRECTLY not async',
        'conclusion_text': 'If you get this, the issue is with async'
    }
    
    print("\nSending email DIRECTLY (not in thread)...")
    
    try:
        # Use signup template which exists and doesn't need QR
        result = send_email(
            subject=f"DIRECT TEST - {datetime.now().strftime('%H:%M:%S')}",
            to_email="kdresdell@gmail.com",
            template_name="signup",
            context=context
        )
        print("✅ Email sent successfully!")
        
    except Exception as e:
        print(f"❌ ERROR sending email: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n🔍 This is the REAL error that's being hidden by async!")