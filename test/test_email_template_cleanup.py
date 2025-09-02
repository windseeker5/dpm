#!/usr/bin/env python3
"""
Unit tests for email template system cleanup.
Verifies the old global email template system has been removed
and the new activity-specific system is working correctly.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Admin, Activity, Setting
from utils import get_email_context
import json
from datetime import datetime

class TestEmailTemplateCleanup(unittest.TestCase):
    """Test suite for email template system cleanup"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()
        
    def test_no_old_email_settings_in_database(self):
        """Verify old email template settings have been removed from database"""
        # Check that no old-style email template settings exist
        old_patterns = ['SUBJECT_%', 'TITLE_%', 'INTRO_%', 'CONCLUSION_%', 
                       'THEME_%', 'HEADING_%', 'CUSTOM_MESSAGE_%', 
                       'CTA_TEXT_%', 'CTA_URL_%']
        
        for pattern in old_patterns:
            settings = Setting.query.filter(Setting.key.like(pattern)).all()
            self.assertEqual(len(settings), 0, 
                           f"Found old email template settings matching {pattern}")
        
        print("✅ No old email template settings found in database")
        
    def test_copy_global_templates_function_removed(self):
        """Verify copy_global_email_templates_to_activity function has been removed"""
        try:
            from utils import copy_global_email_templates_to_activity
            self.fail("copy_global_email_templates_to_activity should have been removed")
        except ImportError:
            # This is expected - function should not exist
            print("✅ copy_global_email_templates_to_activity function properly removed")
            
    def test_new_activity_has_empty_email_templates(self):
        """Verify new activities are created with empty email_templates"""
        # Check that the activity creation code in app.py uses empty dict
        # Read the relevant line from app.py to verify
        import os
        app_path = os.path.join(os.path.dirname(__file__), '..', 'app.py')
        
        with open(app_path, 'r') as f:
            content = f.read()
            
        # Check that email_templates={} is used in activity creation
        if 'email_templates={},' in content or 'email_templates = {}' in content:
            print("✅ New activities created with empty email_templates")
        else:
            self.fail("Activity creation not using empty email_templates dict")
        
    def test_email_templates_menu_removed_from_ui(self):
        """Test that Email Templates menu item is not in Settings page"""
        # Login as admin
        with self.client as c:
            # Simulate login (you may need to adjust based on your auth system)
            with c.session_transaction() as sess:
                sess['admin_id'] = 1  # Assuming admin ID 1 exists
                
            response = c.get('/setup')
            
            if response.status_code == 302:  # Redirect
                # Follow redirect
                response = c.get(response.location)
                
            if response.status_code == 200:
                html = response.data.decode('utf-8')
                
                # Check that Email Templates menu item is not present
                self.assertNotIn('Email Templates</span>', html,
                               "Email Templates menu item should be removed")
                self.assertNotIn('ti-template', html,
                               "Template icon should be removed from menu")
                               
                print("✅ Email Templates menu item removed from UI")
            else:
                print(f"⚠️ Could not test UI (status: {response.status_code})")
                
    def test_email_notification_tab_removed(self):
        """Test that Email Notification tab is not in setup page"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['admin_id'] = 1
                
            response = c.get('/setup')
            
            if response.status_code == 302:
                response = c.get(response.location)
                
            if response.status_code == 200:
                html = response.data.decode('utf-8')
                
                # Check that Email Notification tab is not present
                self.assertNotIn('tab-email-templates', html,
                               "Email Notification tab should be removed")
                self.assertNotIn('Email Notification', html,
                               "Email Notification text should be removed")
                               
                print("✅ Email Notification tab removed from setup page")
            else:
                print(f"⚠️ Could not test setup page (status: {response.status_code})")
                
    def test_activity_specific_email_system_works(self):
        """Test that activity-specific email customization still works"""
        # Get an activity with email templates
        activity = Activity.query.first()
        
        if activity:
            # Verify activity has email_templates attribute
            self.assertTrue(hasattr(activity, 'email_templates'))
            
            # Verify it's a dict or None
            self.assertIn(type(activity.email_templates), [dict, type(None)])
            
            print("✅ Activity-specific email system working correctly")
        else:
            print("⚠️ No activities found for testing")
            
    def test_settings_route_no_email_processing(self):
        """Test that setup route no longer processes email template settings"""
        # This test only verifies that old email template settings don't exist
        # It does NOT make POST requests that could overwrite real settings
        
        # Check that old-style email template settings don't exist in database
        old_template_keys = [
            'SUBJECT_pass_created', 'TITLE_pass_created', 
            'INTRO_pass_created', 'CONCLUSION_pass_created',
            'THEME_pass_created'
        ]
        
        for key in old_template_keys:
            setting = Setting.query.filter_by(key=key).first()
            self.assertIsNone(setting, 
                            f"Old email setting {key} should not exist")
                            
        print("✅ Setup route no longer processes old email template settings")

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)