#!/usr/bin/env python3
"""
Unit tests for email template default copying functionality
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Activity, Setting
from utils import copy_global_email_templates_to_activity

class TestEmailTemplateDefaults(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        self.app_context.pop()
    
    def test_copy_global_templates_structure(self):
        """Test that copy function returns correct structure"""
        templates = copy_global_email_templates_to_activity()
        
        # Check all 6 template types exist
        expected_types = ['newPass', 'paymentReceived', 'latePayment', 
                         'signup', 'redeemPass', 'survey_invitation']
        for template_type in expected_types:
            self.assertIn(template_type, templates)
            
        # Check each template has required fields
        for template_type, config in templates.items():
            self.assertIn('subject', config)
            self.assertIn('title', config)
            self.assertIn('intro_text', config)
            self.assertIn('conclusion_text', config)
    
    def test_new_activity_gets_templates(self):
        """Test that new activities receive email templates"""
        # Login as admin
        with self.client:
            login_response = self.client.post('/admin/login', data={
                'email': 'kdresdell@gmail.com',
                'password': 'admin123'
            }, follow_redirects=True)
            
            # Create new activity
            response = self.client.post('/create-activity', data={
                'name': 'Test Activity with Templates',
                'type': 'test',
                'description': 'Testing default templates',
                'status': 'active'
            }, follow_redirects=True)
            
            # Get the created activity
            activity = Activity.query.filter_by(name='Test Activity with Templates').first()
            if activity:
                # Check email_templates is populated
                self.assertIsNotNone(activity.email_templates)
                self.assertIn('newPass', activity.email_templates)
                self.assertIn('signup', activity.email_templates)
                self.assertIn('paymentReceived', activity.email_templates)
                self.assertIn('latePayment', activity.email_templates)
                self.assertIn('redeemPass', activity.email_templates)
                self.assertIn('survey_invitation', activity.email_templates)
                
                # Verify structure of one template
                new_pass = activity.email_templates.get('newPass', {})
                self.assertIn('subject', new_pass)
                self.assertIn('title', new_pass)
                self.assertIn('intro_text', new_pass)
                
                # Clean up
                db.session.delete(activity)
                db.session.commit()

if __name__ == '__main__':
    unittest.main()