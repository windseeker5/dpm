#!/usr/bin/env python
"""
Direct test to send email using the updated email customization system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Activity
from utils import send_email, get_email_context, safe_template
from flask import render_template
from datetime import datetime
import json

def send_test_email():
    """Send a test email for Activity 3 using newPass template"""
    
    with app.app_context():
        # Get activity
        activity = Activity.query.get(3)
        if not activity:
            print("❌ Activity 3 not found!")
            return False
        
        print(f"✅ Found activity: {activity.name}")
        
        # Create base context with test data
        base_context = {
            'user_name': 'Kevin Dresdell',
            'user_email': 'kdresdell@gmail.com',
            'activity_name': activity.name,
            'pass_code': 'TEST-2025-01',
            'amount': '$50.00',
            'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Create pass data for email blocks
        class PassData:
            def __init__(self):
                self.activity = type('obj', (object,), {
                    'name': activity.name,
                    'id': activity.id
                })()
                self.user = type('obj', (object,), {
                    'name': 'Kevin Dresdell',
                    'email': 'kdresdell@gmail.com',
                    'phone_number': '514-555-0123'
                })()
                self.pass_type = type('obj', (object,), {
                    'name': 'Season Pass',
                    'price': 50.00
                })()
                self.created_dt = datetime.now()
                self.sold_amt = 50.00
                self.paid = True
                self.pass_code = 'TEST-2025-01'
                self.remaining_activities = 5
                self.uses_remaining = 5
        
        pass_data = PassData()
        
        # Render email blocks
        print("📦 Rendering email blocks...")
        base_context['owner_html'] = render_template(
            "email_blocks/owner_card_inline.html",
            pass_data=pass_data
        )
        print(f"   Owner block: {len(base_context['owner_html'])} chars")
        
        base_context['history_html'] = render_template(
            "email_blocks/history_table_inline.html",
            history=[
                {'date': '2025-01-09 14:30', 'action': 'Pass Created'},
                {'date': '2025-01-09 14:31', 'action': 'Email Sent'}
            ]
        )
        print(f"   History block: {len(base_context['history_html'])} chars")
        
        # Get merged context with activity customizations
        print("\n🔄 Merging with activity customizations...")
        context = get_email_context(activity, 'newPass', base_context)
        
        # Get subject from context or use default
        subject = context.get('subject', 'Test: Your Digital Pass is Ready! 🎉')
        
        # Get compiled template path
        template_path = safe_template('newPass')
        print(f"\n📄 Using template: {template_path}")
        
        # Load inline images
        compiled_dir = template_path.replace('/index.html', '')
        json_path = os.path.join('templates', compiled_dir, 'inline_images.json')
        inline_images = {}
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                inline_images = json.load(f)
            print(f"   Loaded {len(inline_images)} inline images")
        
        # Generate QR code
        from utils import generate_qr_code_image
        qr_code_data = generate_qr_code_image('TEST-2025-01')
        if qr_code_data:
            inline_images['qr_code'] = qr_code_data
            print("   ✅ QR code generated")
        
        # Send the email
        print(f"\n📧 Sending email to kdresdell@gmail.com...")
        print(f"   Subject: {subject}")
        
        result = send_email(
            subject=subject,
            to_email="kdresdell@gmail.com",
            template_name='newPass',
            context=context,
            inline_images=inline_images
        )
        
        if result:
            print("\n🎉 SUCCESS! Test email sent to kdresdell@gmail.com")
            print("✅ Email contains:")
            print("   - Your beautiful compiled template")
            print("   - Email blocks (owner card & history)")
            print("   - Activity customizations")
            print("   - QR code")
            print("   - All inline images")
            return True
        else:
            print("\n❌ Failed to send email")
            return False

if __name__ == "__main__":
    print("="*60)
    print("EMAIL CUSTOMIZATION TEST - SENDING REAL EMAIL")
    print("="*60)
    success = send_test_email()
    print("="*60)
    sys.exit(0 if success else 1)