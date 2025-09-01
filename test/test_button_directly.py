#!/usr/bin/env python3
"""
Test exactly what the button does
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Activity
from utils import send_email_async, safe_template
from datetime import datetime

with app.app_context():
    print("Testing exact button functionality...")
    
    # Get activity 2 like the button does
    activity = Activity.query.get(2)
    template_type = 'newPass'
    
    print(f"Activity: {activity.name}")
    print(f"Template type: {template_type}")
    
    # Check what safe_template returns
    template_name = 'newPass'
    resolved_template = safe_template(template_name)
    print(f"Template name: {template_name}")
    print(f"Resolved to: {resolved_template}")
    
    # Check if compiled template exists
    import os
    compiled_path = os.path.join("templates", "email_templates", "newPass_compiled", "index.html")
    print(f"Compiled template exists: {os.path.exists(compiled_path)}")
    
    # Create context exactly like button does
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
    
    print("\nSending email EXACTLY like the button does...")
    
    # Send exactly like the button
    send_email_async(
        app=app,
        activity=activity,
        subject=f"📧 Test: {template_type} - {activity.name} ({datetime.now().strftime('%H:%M:%S')})",
        to_email="kdresdell@gmail.com",
        template_name=template_name,  # Using 'newPass' not full path
        context=test_context
    )
    
    print("✅ Done! Check if email arrives")