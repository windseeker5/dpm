#!/usr/bin/env python3
"""
Test template compatibility with unified settings route
"""
import sys
import os

# Add the parent directory to sys.path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Setting

def test_template_rendering():
    """Test that template renders with sample data"""
    with app.test_client() as client:
        with app.app_context():
            # Create a test session
            with client.session_transaction() as sess:
                sess['admin'] = 'test@example.com'
            
            # Create some test settings in database
            test_settings = [
                Setting(key='ORG_NAME', value='Test Organization'),
                Setting(key='MAIL_SERVER', value='smtp.test.com'),
                Setting(key='ENABLE_EMAIL_PAYMENT_BOT', value='True')
            ]
            
            # Add to database if they don't exist
            for setting in test_settings:
                existing = Setting.query.filter_by(key=setting.key).first()
                if not existing:
                    db.session.add(setting)
            
            db.session.commit()
            
            # Test GET request with data
            response = client.get('/admin/unified-settings')
            print(f"Template render status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.data.decode('utf-8')
                
                # Check for key template elements
                checks = [
                    ('Organization Settings section', 'Organization Settings' in content),
                    ('Form action URL', 'save_unified_settings' in content),
                    ('ORG_NAME field', 'name="ORG_NAME"' in content),
                    ('Email settings section', 'mail_server' in content),
                    ('Payment bot section', 'enable_email_payment_bot' in content),
                    ('Settings data populated', 'Test Organization' in content),
                ]
                
                all_passed = True
                for check_name, result in checks:
                    status = "✅" if result else "❌"
                    print(f"{status} {check_name}: {result}")
                    if not result:
                        all_passed = False
                
                if all_passed:
                    print("\n✅ All template compatibility checks passed!")
                else:
                    print("\n❌ Some template compatibility issues found")
                    
            else:
                print(f"❌ Template failed to render: {response.status_code}")

if __name__ == '__main__':
    test_template_rendering()