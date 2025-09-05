#!/usr/bin/env python3
"""
Test script to verify signup emails no longer have logo attachments
"""

import unittest
import os
import sys
import tempfile
from unittest.mock import patch, mock_open

# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, Activity, Signup
from utils import notify_signup_event
from datetime import datetime, timezone

class TestSignupLogoAttachmentFix(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        with self.app.app_context():
            # Create test data
            self.user = User(
                name="Test User",
                email="test@example.com", 
                phone_number="123-456-7890"
            )
            db.session.add(self.user)
            
            self.activity = Activity(
                name="Test Activity",
                description="Test activity for signup email testing"
            )
            db.session.add(self.activity)
            db.session.commit()
            
            self.signup = Signup(
                user_id=self.user.id,
                activity_id=self.activity.id,
                subject="Test Signup",
                signed_up_at=datetime.now(timezone.utc)
            )
            db.session.add(self.signup)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
    
    @patch('utils.send_email_async')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_signup_email_no_logo_attachment(self, mock_file, mock_exists, mock_send_email):
        """Test that signup emails don't include logo attachments"""
        
        # Mock file system responses
        def mock_exists_side_effect(path):
            # Make compiled template files exist
            if 'signup_compiled/index.html' in path:
                return True
            if 'inline_images.json' in path:
                return True
            # Logo file exists but should not be attached
            if 'logo.png' in path:
                return True
            return False
        
        mock_exists.side_effect = mock_exists_side_effect
        
        # Mock file content
        mock_file.return_value.read.side_effect = [
            '<html>Test signup template {{user_name}}</html>',  # index.html
            '{"hero": "base64encodedimage"}'  # inline_images.json
        ]
        
        with self.app.app_context():
            # Call the signup notification function
            notify_signup_event(
                app=self.app,
                signup=self.signup,
                activity=self.activity,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Verify send_email_async was called
            self.assertTrue(mock_send_email.called)
            
            # Get the call arguments
            call_args = mock_send_email.call_args
            
            # Check that inline_images does NOT contain 'logo'
            if 'inline_images' in call_args.kwargs:
                inline_images = call_args.kwargs['inline_images']
                self.assertNotIn('logo', inline_images, 
                    "Signup emails should NOT have logo attachments!")
                print("✅ PASS: Signup email has no logo attachment")
            else:
                print("✅ PASS: No inline_images parameter (no attachments)")
    
    def test_signup_function_exists(self):
        """Test that the signup function exists and is importable"""
        from utils import notify_signup_event
        self.assertTrue(callable(notify_signup_event))
        print("✅ PASS: notify_signup_event function exists")

if __name__ == '__main__':
    print("🧪 Testing Signup Email Logo Attachment Fix...")
    print("=" * 60)
    
    # Run the tests
    unittest.main(verbosity=2)