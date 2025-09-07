#!/usr/bin/env python3
"""
Unit Tests for Email Template Functionality
Tests the email templates interface for proper layout and functionality.
"""

import unittest
import sys
import os
import time

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, db
from models import Admin, Activity


class EmailTemplatesTestCase(unittest.TestCase):
    """Test cases for email templates functionality"""
    
    def setUp(self):
        """Set up test client and database"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        # Create application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Login as admin
        self.login_admin()
        
    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()
        
    def login_admin(self):
        """Login with admin credentials"""
        response = self.client.post('/login', data={
            'email': 'kdresdell@gmail.com',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
    def test_email_templates_page_loads(self):
        """Test that email templates page loads successfully"""
        response = self.client.get('/activity/1/email-templates')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email Communication Builder', response.data)
        
    def test_all_six_templates_present(self):
        """Test that all 6 email templates are present on the page"""
        response = self.client.get('/activity/1/email-templates')
        self.assertEqual(response.status_code, 200)
        
        # Check for all 6 templates
        templates = [
            b'New Pass Created',
            b'Payment Received', 
            b'Late Payment Reminder',
            b'Signup Confirmation',
            b'Pass Redeemed',
            b'Survey Invitation'
        ]
        
        for template in templates:
            self.assertIn(template, response.data)
            
    def test_dropdown_actions_present(self):
        """Test that dropdown action buttons are present"""
        response = self.client.get('/activity/1/email-templates')
        self.assertEqual(response.status_code, 200)
        
        # Check for dropdown actions
        actions = [
            b'Customize',
            b'Preview', 
            b'Send Test',
            b'Reset to Default'
        ]
        
        for action in actions:
            self.assertIn(action, response.data)
            
    def test_responsive_column_layout(self):
        """Test that responsive column classes are present"""
        response = self.client.get('/activity/1/email-templates')
        self.assertEqual(response.status_code, 200)
        
        # Check for responsive column classes
        self.assertIn(b'col-xl-4', response.data)  # 3 columns on extra large
        self.assertIn(b'col-lg-4', response.data)  # 3 columns on large  
        self.assertIn(b'col-md-6', response.data)  # 2 columns on medium
        self.assertIn(b'col-12', response.data)    # 1 column on small
        
    def test_toggle_switches_present(self):
        """Test that custom toggle switches are present"""
        response = self.client.get('/activity/1/email-templates')
        self.assertEqual(response.status_code, 200)
        
        # Check for toggle switches - they appear as checkboxes with "Custom" labels
        content = response.data.decode('utf-8')
        self.assertIn('checkbox', content)
        self.assertIn('Custom', content)
        
    def test_preview_images_present(self):
        """Test that preview images are present for all templates"""
        response = self.client.get('/activity/1/email-templates')
        self.assertEqual(response.status_code, 200)
        
        # Check for preview images
        preview_files = [
            b'newPass.svg',
            b'paymentReceived.svg',
            b'latePayment.svg', 
            b'signup.svg',
            b'redeemPass.svg',
            b'survey_invitation.svg'
        ]
        
        for preview in preview_files:
            self.assertIn(preview, response.data)
            
    def test_javascript_under_50_lines(self):
        """Test that JavaScript is under 50 lines as required"""
        response = self.client.get('/activity/1/email-templates')
        self.assertEqual(response.status_code, 200)
        
        # Get the JavaScript content between script tags
        content = response.data.decode('utf-8')
        start = content.find('// Simple Email Template Interface')
        end = content.find('</script>', start)
        
        if start != -1 and end != -1:
            js_content = content[start:end]
            lines = [line for line in js_content.split('\n') if line.strip()]
            self.assertLess(len(lines), 50, f"JavaScript has {len(lines)} lines, should be under 50")
            
    def test_no_email_card_hover_effects(self):
        """Test that email template card hover effects have been removed"""
        response = self.client.get('/activity/1/email-templates')
        self.assertEqual(response.status_code, 200)
        
        # Should not contain email card hover effects that cause blue glow
        content = response.data.decode('utf-8')
        self.assertNotIn('.email-template-card:hover', content)
        # Check that hover effects are commented out or removed
        hover_removed = ('/* Removed hover effects' in content or 
                        'Removed all card hover effects' in content or
                        '.email-template-card:hover' not in content)
        self.assertTrue(hover_removed, "Hover effects should be removed or commented out")
        
        
if __name__ == '__main__':
    unittest.main()