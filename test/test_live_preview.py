#!/usr/bin/env python3
"""
Test Live Preview System

Tests the live email preview functionality that generates previews without saving to database.
"""

import unittest
import sys
import os
import json
import base64
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from io import BytesIO

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Activity, Admin


class TestLivePreview(unittest.TestCase):
    """Test the live preview system"""

    def setUp(self):
        """Set up test environment"""
        # Set up Flask app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            
            # Create test admin
            test_admin = Admin(
                username='testadmin',
                email='testadmin@test.com'
            )
            db.session.add(test_admin)
            
            # Create test activity with initial email templates
            self.test_activity = Activity(
                name="Live Preview Test Activity",
                email_templates={
                    'newPass': {
                        'subject': 'Original Subject',
                        'title': 'Original Title',
                        'intro_text': 'Original intro text'
                    }
                }
            )
            db.session.add(self.test_activity)
            db.session.commit()
        
        self.app = app
        self.app_context = app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        self.app_context.pop()

    def test_live_preview_basic_functionality(self):
        """Test basic live preview generation"""
        print("\n🔍 Testing basic live preview functionality...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Test basic live preview request
            response = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'Live Preview Subject',
                    'newPass_title': 'Live Preview Title',
                    'newPass_intro_text': 'Live preview intro text'
                }
            )
            
            self.assertEqual(response.status_code, 200)
            html_content = response.data.decode('utf-8')
            
            # Should contain live preview banner
            self.assertIn('LIVE PREVIEW', html_content)
            self.assertIn('Changes not saved', html_content)
            
            # Should contain the live customizations
            self.assertIn('Live Preview Subject', html_content)
            self.assertIn('Live Preview Title', html_content)
            self.assertIn('Live preview intro text', html_content)
            
            print("   ✅ Basic live preview functionality works")

    def test_live_preview_does_not_save_to_database(self):
        """Test that live preview doesn't modify database"""
        print("\n🔍 Testing that live preview doesn't save to database...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Get original templates
            original_templates = self.test_activity.email_templates.copy()
            
            # Make live preview request with new data
            response = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'Should Not Be Saved',
                    'newPass_title': 'Should Not Be Saved',
                    'newPass_intro_text': 'This should not be saved to database'
                }
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Refresh activity from database
            db.session.refresh(self.test_activity)
            
            # Templates should be unchanged
            self.assertEqual(self.test_activity.email_templates, original_templates)
            self.assertEqual(self.test_activity.email_templates['newPass']['subject'], 'Original Subject')
            self.assertEqual(self.test_activity.email_templates['newPass']['title'], 'Original Title')
            
            print("   ✅ Database remains unchanged after live preview")

    def test_live_preview_mobile_mode(self):
        """Test mobile device mode for live preview"""
        print("\n🔍 Testing mobile device mode...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Test mobile mode
            response = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'device': 'mobile',
                    'newPass_subject': 'Mobile Preview Test'
                }
            )
            
            self.assertEqual(response.status_code, 200)
            html_content = response.data.decode('utf-8')
            
            # Should contain mobile wrapper
            self.assertIn('Mobile Preview', html_content)
            self.assertIn('width: 375px', html_content)
            
            print("   ✅ Mobile device mode works")

    def test_live_preview_desktop_mode(self):
        """Test desktop device mode (default)"""
        print("\n🔍 Testing desktop device mode...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Test desktop mode (default)
            response = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'Desktop Preview Test'
                }
            )
            
            self.assertEqual(response.status_code, 200)
            html_content = response.data.decode('utf-8')
            
            # Should NOT contain mobile wrapper
            self.assertNotIn('Mobile Preview', html_content)
            self.assertNotIn('width: 375px', html_content)
            
            # Should contain the live preview banner
            self.assertIn('LIVE PREVIEW', html_content)
            
            print("   ✅ Desktop device mode works")

    def test_live_preview_all_template_types(self):
        """Test live preview works for all template types"""
        print("\n🔍 Testing all template types...")
        
        template_types = ['newPass', 'paymentReceived', 'redeemPass', 'latePayment', 'signup', 'survey_invitation']
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            for template_type in template_types:
                response = client.post(
                    f'/activity/{self.test_activity.id}/email-preview-live',
                    data={
                        'template_type': template_type,
                        f'{template_type}_subject': f'Test Subject for {template_type}',
                        f'{template_type}_title': f'Test Title for {template_type}'
                    }
                )
                
                self.assertEqual(response.status_code, 200, f"Template type {template_type} failed")
                html_content = response.data.decode('utf-8')
                
                # Should contain live preview banner
                self.assertIn('LIVE PREVIEW', html_content)
                
                print(f"   ✅ Template type '{template_type}' works")

    def test_live_preview_empty_customizations(self):
        """Test live preview with no customizations"""
        print("\n🔍 Testing live preview with empty customizations...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Test with no customizations
            response = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass'
                }
            )
            
            self.assertEqual(response.status_code, 200)
            html_content = response.data.decode('utf-8')
            
            # Should still contain live preview banner
            self.assertIn('LIVE PREVIEW', html_content)
            
            # Should fall back to existing saved templates or defaults
            self.assertIn('Original Subject', html_content)
            
            print("   ✅ Empty customizations handled correctly")

    def test_live_preview_mixed_customizations(self):
        """Test live preview with only some fields customized"""
        print("\n🔍 Testing mixed customizations...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Test with only some fields customized
            response = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'New Live Subject',  # Customized
                    # title not provided - should use original
                    'newPass_intro_text': 'New live intro',  # Customized
                    # conclusion_text not provided - should use default
                }
            )
            
            self.assertEqual(response.status_code, 200)
            html_content = response.data.decode('utf-8')
            
            # Should contain live customizations
            self.assertIn('New Live Subject', html_content)
            self.assertIn('New live intro', html_content)
            
            # Should contain original values for non-customized fields
            self.assertIn('Original Title', html_content)
            
            print("   ✅ Mixed customizations work correctly")

    def test_live_preview_authentication_required(self):
        """Test that authentication is required"""
        print("\n🔍 Testing authentication requirement...")
        
        with self.app.test_client() as client:
            # No login - should redirect
            response = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'Unauthorized Access Test'
                }
            )
            
            # Should redirect to login
            self.assertEqual(response.status_code, 302)
            self.assertIn('login', response.location)
            
            print("   ✅ Authentication properly required")

    def test_live_preview_activity_not_found(self):
        """Test handling of non-existent activity"""
        print("\n🔍 Testing non-existent activity handling...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Test with non-existent activity ID
            response = client.post(
                '/activity/99999/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'Test'
                }
            )
            
            # Should return 404
            self.assertEqual(response.status_code, 404)
            
            print("   ✅ Non-existent activity properly handled")

    def test_live_preview_caching_behavior(self):
        """Test that live preview doesn't interfere with caching"""
        print("\n🔍 Testing caching behavior...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Make first request
            response1 = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'First Request'
                }
            )
            
            # Make second request with different data
            response2 = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'Second Request'
                }
            )
            
            self.assertEqual(response1.status_code, 200)
            self.assertEqual(response2.status_code, 200)
            
            # Should contain different content
            self.assertIn('First Request', response1.data.decode('utf-8'))
            self.assertIn('Second Request', response2.data.decode('utf-8'))
            
            print("   ✅ No unwanted caching interference")

    def test_live_preview_with_curl_data(self):
        """Test live preview with curl-like request data"""
        print("\n🔍 Testing curl-like request data...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Test with JSON data (like curl might send)
            response = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data=json.dumps({
                    'template_type': 'newPass',
                    'newPass_subject': 'Curl Test Subject'
                }),
                content_type='application/x-www-form-urlencoded'
            )
            
            # Should still work (Flask handles form data parsing)
            self.assertEqual(response.status_code, 200)
            
            print("   ✅ Curl-like requests handled")

    def test_live_preview_error_handling(self):
        """Test error handling in live preview"""
        print("\n🔍 Testing error handling...")
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Test with invalid template type
            response = client.post(
                f'/activity/{self.test_activity.id}/email-preview-live',
                data={
                    'template_type': 'invalid_template_type',
                    'invalid_template_type_subject': 'Test'
                }
            )
            
            # Should handle gracefully and return error HTML
            self.assertEqual(response.status_code, 200)
            html_content = response.data.decode('utf-8')
            
            # Should contain error information
            self.assertIn('Live Preview Error', html_content)
            self.assertIn('Debug Info', html_content)
            
            print("   ✅ Error handling works correctly")


class TestLivePreviewIntegration(unittest.TestCase):
    """Integration tests for live preview system"""

    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
        
        self.app = app
        self.app_context = app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        self.app_context.pop()
    
    def test_live_preview_curl_command(self):
        """Test the exact curl command from requirements"""
        print("\n🔍 Testing exact curl command format...")
        
        # Create test activity
        with app.app_context():
            activity = Activity(name="Curl Test Activity")
            db.session.add(activity)
            db.session.commit()
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Test curl-equivalent request
            response = client.post(
                f'/activity/{activity.id}/email-preview-live',
                data={'template_type': 'newPass'},
                content_type='application/x-www-form-urlencoded'
            )
            
            self.assertEqual(response.status_code, 200)
            html_content = response.data.decode('utf-8')
            
            # Should contain expected elements
            self.assertIn('LIVE PREVIEW', html_content)
            self.assertIn('newPass', html_content.lower())
            
            print("   ✅ Curl command format works")

    def test_live_preview_performance(self):
        """Test live preview performance"""
        print("\n🔍 Testing live preview performance...")
        
        with app.app_context():
            activity = Activity(name="Performance Test Activity")
            db.session.add(activity)
            db.session.commit()
        
        import time
        
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['admin'] = 'testadmin@test.com'
            
            # Measure response time
            start_time = time.time()
            
            response = client.post(
                f'/activity/{activity.id}/email-preview-live',
                data={
                    'template_type': 'newPass',
                    'newPass_subject': 'Performance Test',
                    'newPass_title': 'Performance Test Title',
                    'newPass_intro_text': 'Performance test intro text'
                }
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.assertEqual(response.status_code, 200)
            
            # Should respond within reasonable time (adjust as needed)
            self.assertLess(response_time, 5.0, f"Response took {response_time:.2f}s")
            
            print(f"   ✅ Response time: {response_time:.2f}s")


if __name__ == '__main__':
    print("🧪 Running Live Preview Tests")
    print("=" * 50)
    
    # Run tests
    unittest.main(verbosity=2)