#!/usr/bin/env python3
"""
Debug Email Sending - Test why emails aren't being received
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils import send_email_async
from datetime import datetime
from models import Activity

def debug_email_send():
    """Debug email sending with verbose output"""
    try:
        with app.app_context():
            print("📧 Debug Email Send Test")
            print("=" * 50)
            
            # Get activity with ID 2 (based on your screenshot)
            activity = Activity.query.get(2)
            if not activity:
                print("❌ Activity ID 2 not found")
                return
            
            print(f"✅ Found activity: {activity.name}")
            
            # Check email templates
            if activity.email_templates:
                print(f"📋 Email templates found: {list(activity.email_templates.keys())}")
                if 'newPass' in activity.email_templates:
                    newpass_template = activity.email_templates['newPass']
                    print(f"   newPass template data:")
                    for key, value in newpass_template.items():
                        if key == 'hero_image':
                            print(f"     - {key}: {value} (exists: {os.path.exists(os.path.join('static/uploads/email_heroes', value))})")
                        else:
                            print(f"     - {key}: {value[:50]}..." if len(str(value)) > 50 else f"     - {key}: {value}")
            else:
                print("📋 No email templates configured")
            
            print("\n🚀 Sending test email...")
            
            # Send test email with debug info
            test_context = {
                'user_name': 'Debug Test User',
                'user_email': 'kdresdell@gmail.com',
                'activity_name': activity.name,
                'pass_code': 'DEBUG123',
                'title': 'Debug Test Email',
                'intro_text': 'This is a debug test to verify email sending.',
                'conclusion_text': f'Test sent at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            
            # Send with activity to enable customizations
            send_email_async(
                app=app,
                activity=activity,
                subject=f"🔍 Debug Test - {activity.name} - {datetime.now().strftime('%H:%M:%S')}",
                to_email="kdresdell@gmail.com",
                template_name="newPass",  # Use newPass template
                context=test_context
            )
            
            print("✅ Email queued for sending")
            print("\n📋 Summary:")
            print(f"   - To: kdresdell@gmail.com")
            print(f"   - Template: newPass")
            print(f"   - Activity: {activity.name}")
            print(f"   - Customizations: {'Yes' if activity.email_templates else 'No'}")
            
            # Check email logs
            from models import EmailLog
            recent_logs = EmailLog.query.filter_by(to_email='kdresdell@gmail.com').order_by(EmailLog.timestamp.desc()).limit(5).all()
            
            print(f"\n📊 Recent email logs to kdresdell@gmail.com:")
            for log in recent_logs:
                print(f"   - {log.timestamp}: {log.subject} [{log.result}]")
                if log.error_message:
                    print(f"     ERROR: {log.error_message}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Full error:\n{traceback.format_exc()}")

if __name__ == "__main__":
    debug_email_send()