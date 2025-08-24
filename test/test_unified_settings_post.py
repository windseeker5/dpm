#!/usr/bin/env python3
"""
Test script for unified settings POST functionality
"""
import sys
import os

# Add the parent directory to sys.path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Setting

def test_unified_settings_post():
    """Test that unified settings route handles POST requests"""
    with app.test_client() as client:
        with app.app_context():
            # Create a test session
            with client.session_transaction() as sess:
                sess['admin'] = 'test@example.com'
            
            # Test POST request with sample data
            test_data = {
                'ORG_NAME': 'Test Organization',
                'CALL_BACK_DAYS': '7',
                'mail_server': 'smtp.test.com',
                'mail_port': '587',
                'mail_use_tls': 'on',
                'mail_username': 'test@example.com',
                'mail_default_sender': 'test@example.com',
                'mail_sender_name': 'Test Sender',
                'enable_email_payment_bot': 'on',
                'bank_email_from': 'bank@test.com',
                'bank_email_subject': 'Payment Notification',
                'bank_email_name_confidance': '90'
            }
            
            response = client.post('/admin/unified-settings', data=test_data)
            print(f"POST /admin/unified-settings status: {response.status_code}")
            
            if response.status_code == 302:  # Redirect after successful POST
                print("✅ POST request handled successfully (redirected)")
                
                # Check if settings were saved
                org_name = Setting.query.filter_by(key='ORG_NAME').first()
                mail_server = Setting.query.filter_by(key='MAIL_SERVER').first()
                bot_enabled = Setting.query.filter_by(key='ENABLE_EMAIL_PAYMENT_BOT').first()
                
                if org_name and org_name.value == 'Test Organization':
                    print("✅ Organization setting saved correctly")
                else:
                    print("❌ Organization setting not saved properly")
                
                if mail_server and mail_server.value == 'smtp.test.com':
                    print("✅ Email setting saved correctly")
                else:
                    print("❌ Email setting not saved properly")
                    
                if bot_enabled and bot_enabled.value == 'True':
                    print("✅ Payment bot setting saved correctly")
                else:
                    print("❌ Payment bot setting not saved properly")
                    
            else:
                print(f"❌ POST request failed with status {response.status_code}")
                print("Response data:", response.data.decode('utf-8')[:500])

if __name__ == '__main__':
    test_unified_settings_post()