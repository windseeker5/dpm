#!/usr/bin/env python3
"""
Trace exactly what happens when the button is clicked
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Activity
from datetime import datetime

with app.app_context():
    print("🔍 TRACING BUTTON ISSUE")
    print("=" * 60)
    
    # Get the Monday Comedy Show activity (ID 2)
    activity = Activity.query.get(2)
    print(f"Activity: {activity.name}")
    print(f"Activity ID: {activity.id}")
    
    # Check what's in email_templates
    if activity.email_templates:
        print(f"\n📋 Email templates data:")
        for template_type, data in activity.email_templates.items():
            print(f"\n  {template_type}:")
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 50:
                    print(f"    {key}: {value[:50]}...")
                else:
                    print(f"    {key}: {value}")
    
    # Now simulate EXACTLY what the button does
    template_type = 'newPass'
    print(f"\n🎯 Simulating button click for template: {template_type}")
    
    # Import everything needed
    from utils import send_email_async
    import threading
    import time
    
    # Create context exactly like the button
    test_context = {
        'user_name': 'Kevin Dresdell (Test)',
        'user_email': 'kdresdell@gmail.com',
        'activity_name': activity.name,
        'pass_code': 'TEST123',
        'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'title': f'Test Email - {template_type}',
        'intro_text': f'This is a test email for template type: {template_type}',
        'conclusion_text': f'Test completed for activity: {activity.name}'
    }
    
    # The button now uses 'signup' template for newPass testing
    template_name = 'signup'  # After our fix
    
    print(f"  Using template: {template_name}")
    print(f"  To: kdresdell@gmail.com")
    print(f"  Subject: Test: {template_type} - {activity.name}")
    
    # Check if the template files exist
    template_path = os.path.join("templates/email_templates/signup_compiled/index.html")
    json_path = os.path.join("templates/email_templates/signup_compiled/inline_images.json")
    print(f"\n📂 Template files:")
    print(f"  Compiled template exists: {os.path.exists(template_path)}")
    print(f"  Inline images exists: {os.path.exists(json_path)}")
    
    # Send the email
    print(f"\n📧 Sending email...")
    
    # Track if thread completes
    thread_completed = False
    exception_caught = None
    
    def send_with_tracking():
        global thread_completed, exception_caught
        try:
            send_email_async(
                app=app,
                activity=activity,
                subject=f"📧 Test: {template_type} - {activity.name} ({datetime.now().strftime('%H:%M:%S')})",
                to_email="kdresdell@gmail.com",
                template_name=template_name,
                context=test_context
            )
            thread_completed = True
        except Exception as e:
            exception_caught = e
            thread_completed = True
    
    # Run in thread but wait for it
    thread = threading.Thread(target=send_with_tracking)
    thread.start()
    
    # Wait up to 5 seconds for thread to complete
    for i in range(50):
        if thread_completed:
            break
        time.sleep(0.1)
    
    if exception_caught:
        print(f"❌ ERROR in send_email_async: {exception_caught}")
        import traceback
        traceback.print_exc()
    else:
        print("✅ Email function called successfully")
    
    # Check the actual email sending
    print("\n📊 Checking email status...")
    
    # Give it a moment for the async thread to process
    time.sleep(2)
    
    # Check email logs
    from models import EmailLog
    recent = EmailLog.query.filter_by(to_email='kdresdell@gmail.com').order_by(EmailLog.timestamp.desc()).first()
    if recent:
        print(f"  Latest email log:")
        print(f"    Time: {recent.timestamp}")
        print(f"    Subject: {recent.subject}")
        print(f"    Result: {recent.result}")
        if recent.error_message:
            print(f"    ERROR: {recent.error_message}")
    
    print("\n🔍 DIAGNOSIS:")
    if thread_completed and not exception_caught:
        print("✅ Button code is executing correctly")
        print("✅ Email is being queued for sending")
        print("❓ Check if email is actually being sent by the thread")
    else:
        print("❌ There's an issue with the button code execution")