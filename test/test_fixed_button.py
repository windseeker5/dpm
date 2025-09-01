#!/usr/bin/env python3
"""
Test the FIXED button functionality
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Activity
from utils import send_email
from datetime import datetime

with app.app_context():
    print("🔥 TESTING FIXED BUTTON")
    print("=" * 60)
    
    # Get activity 2
    activity = Activity.query.get(2)
    template_type = 'newPass'
    
    # Get actual customizations
    custom_data = {}
    if activity.email_templates and template_type in activity.email_templates:
        custom_data = activity.email_templates[template_type]
        print(f"✅ Found customizations for {template_type}:")
        for k, v in custom_data.items():
            print(f"   {k}: {v[:50] if isinstance(v, str) and len(v) > 50 else v}")
    
    # Create context with ACTUAL customizations (like the fixed button)
    test_context = {
        'user_name': 'Kevin Dresdell',
        'user_email': 'kdresdell@gmail.com',
        'activity_name': activity.name,
        'pass_code': 'TEST123',
        'title': custom_data.get('title', f'Test Email - {template_type}'),
        'intro_text': custom_data.get('intro_text', f'This is a test of the {template_type} template'),
        'conclusion_text': custom_data.get('conclusion_text', f'Test for {activity.name}'),
        'custom_message': custom_data.get('custom_message', ''),
        'cta_text': custom_data.get('cta_text', ''),
        'cta_url': custom_data.get('cta_url', ''),
        'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    subject = custom_data.get('subject', f"Test: {template_type} - {activity.name}")
    subject = f"📧 {subject} - TEST {datetime.now().strftime('%H:%M:%S')}"
    
    print(f"\n📧 Sending DIRECT email (no async):")
    print(f"   Subject: {subject}")
    print(f"   To: kdresdell@gmail.com")
    print(f"   Template: signup (works without QR)")
    print(f"   Title in email: {test_context['title']}")
    print(f"   Intro: {test_context['intro_text']}")
    
    try:
        # DIRECTLY send like the fixed button
        send_email(
            subject=subject,
            to_email="kdresdell@gmail.com",
            template_name="signup",
            context=test_context
        )
        print("\n✅ SUCCESS! Email sent directly!")
        print("📧 CHECK YOUR INBOX NOW!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()