#!/usr/bin/env python3
"""
Functional test for live preview endpoint
"""
import sys
import os
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Activity, Admin

def test_live_preview_with_mock_session():
    """Test live preview by mocking the session"""
    print("🔍 Testing live preview with mocked session...")
    
    with app.test_client() as client:
        with app.app_context():
            # Check if we have any activities in the database
            activity = Activity.query.first()
            if not activity:
                print("❌ No activities found in database")
                return False
            
            print(f"Using activity: {activity.name} (ID: {activity.id})")
            
            # Mock the session by setting admin
            with client.session_transaction() as sess:
                sess['admin'] = 'kdresdell@gmail.com'
            
            # Test the live preview endpoint
            response = client.post(
                f'/activity/{activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'Live Preview Test Subject',
                    'newPass_title': 'Live Preview Test Title',
                    'newPass_intro_text': 'This is a live preview test'
                }
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                html_content = response.data.decode('utf-8')
                print(f"Response length: {len(html_content)} characters")
                
                # Check for key indicators that it worked
                checks = [
                    ('LIVE PREVIEW' in html_content, 'Live preview banner'),
                    ('Live Preview Test Subject' in html_content, 'Custom subject'),
                    ('Live Preview Test Title' in html_content, 'Custom title'),
                    ('This is a live preview test' in html_content, 'Custom intro text'),
                    ('Changes not saved' in html_content, 'Warning message')
                ]
                
                all_passed = True
                for check, description in checks:
                    if check:
                        print(f"  ✅ {description}")
                    else:
                        print(f"  ❌ {description}")
                        all_passed = False
                
                return all_passed
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"Response content: {response.data.decode('utf-8')[:500]}")
                return False

def test_mobile_mode():
    """Test mobile mode specifically"""
    print("\n🔍 Testing mobile mode...")
    
    with app.test_client() as client:
        with app.app_context():
            activity = Activity.query.first()
            if not activity:
                return False
            
            # Mock the session
            with client.session_transaction() as sess:
                sess['admin'] = 'kdresdell@gmail.com'
            
            # Test mobile mode
            response = client.post(
                f'/activity/{activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'device': 'mobile',
                    'newPass_subject': 'Mobile Test'
                }
            )
            
            if response.status_code == 200:
                html_content = response.data.decode('utf-8')
                
                mobile_checks = [
                    ('width: 375px' in html_content, 'Mobile wrapper width'),
                    ('Mobile Preview' in html_content, 'Mobile indicator'),
                    ('LIVE PREVIEW' in html_content, 'Live preview banner')
                ]
                
                all_passed = True
                for check, description in mobile_checks:
                    if check:
                        print(f"  ✅ {description}")
                    else:
                        print(f"  ❌ {description}")
                        all_passed = False
                
                return all_passed
            else:
                print(f"❌ Mobile test failed with status: {response.status_code}")
                return False

def test_database_not_modified():
    """Test that database is not modified by live preview"""
    print("\n🔍 Testing that database is not modified...")
    
    with app.test_client() as client:
        with app.app_context():
            activity = Activity.query.first()
            if not activity:
                return False
            
            # Get original templates
            original_templates = activity.email_templates.copy() if activity.email_templates else {}
            
            # Mock the session
            with client.session_transaction() as sess:
                sess['admin'] = 'kdresdell@gmail.com'
            
            # Make live preview request
            response = client.post(
                f'/activity/{activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'SHOULD NOT BE SAVED TO DB',
                    'newPass_title': 'SHOULD NOT BE SAVED TO DB'
                }
            )
            
            if response.status_code == 200:
                # Refresh the activity from database
                db.session.refresh(activity)
                current_templates = activity.email_templates if activity.email_templates else {}
                
                if current_templates == original_templates:
                    print("  ✅ Database unchanged")
                    return True
                else:
                    print("  ❌ Database was modified!")
                    print(f"    Original: {original_templates}")
                    print(f"    Current:  {current_templates}")
                    return False
            else:
                print(f"❌ Request failed with status: {response.status_code}")
                return False

def test_error_handling():
    """Test error handling"""
    print("\n🔍 Testing error handling...")
    
    with app.test_client() as client:
        with app.app_context():
            # Mock the session
            with client.session_transaction() as sess:
                sess['admin'] = 'kdresdell@gmail.com'
            
            # Test with non-existent activity
            response = client.post(
                '/activity/99999/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'Test'
                }
            )
            
            if response.status_code == 404:
                print("  ✅ 404 for non-existent activity")
                return True
            else:
                print(f"  ❌ Expected 404, got {response.status_code}")
                return False

if __name__ == '__main__':
    print("🧪 Functional Live Preview Tests")
    print("=" * 50)
    
    tests = [
        test_live_preview_with_mock_session,
        test_mobile_mode,
        test_database_not_modified,
        test_error_handling
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ All functional tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)