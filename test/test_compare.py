#!/usr/bin/env python3
"""
COMPARE: What's different between the working Python test and the button?
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Activity
from utils import send_email
from datetime import datetime

print("\n" + "="*80)
print("DIRECT COMPARISON TEST")
print("="*80)

with app.app_context():
    # Test 1: EXACTLY like the Python script that works
    print("\n1️⃣ PYTHON SCRIPT METHOD (WORKS):")
    activity = Activity.query.get(2)
    template_type = 'newPass'
    
    custom_data = {}
    if activity.email_templates and template_type in activity.email_templates:
        custom_data = activity.email_templates[template_type]
    
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
    subject = f"📧 {subject} - PYTHON {datetime.now().strftime('%H:%M:%S')}"
    
    print(f"Sending via Python: {subject}")
    result1 = send_email(
        subject=subject,
        to_email="kdresdell@gmail.com",
        template_name="signup",
        context=test_context
    )
    print(f"Result: {result1}")
    
    # Test 2: EXACTLY like the button route
    print("\n2️⃣ BUTTON ROUTE METHOD:")
    
    # Import the actual function
    from app import test_email_template
    from flask import session, request
    
    with app.test_request_context('/activity/2/email-test', method='POST', 
                                   data={'template_type': 'newPass', 'csrf_token': 'test'}):
        session['admin'] = 'kdresdell@gmail.com'
        
        # Mock request.form
        request.form = {'template_type': 'newPass', 'csrf_token': 'test'}
        
        print("Calling test_email_template function directly...")
        try:
            # Call the actual route function
            response = test_email_template(2)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

print("\n" + "="*80)
print("CHECK THE OUTPUT ABOVE")
print("Both should send emails if the button works correctly")
print("="*80)