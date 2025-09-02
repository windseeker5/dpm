#!/usr/bin/env python
"""
Comprehensive test suite for email customization system
Tests all 6 email types and verifies customization functionality
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from app import app, db
from models import Activity
from utils import get_email_context, safe_template
from flask import render_template


class TestEmailCustomizationComplete(unittest.TestCase):
    """Complete test suite for email customization system"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.client = app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create test activity with customizations
        self.test_activity = Activity.query.get(3)
        if not self.test_activity:
            self.test_activity = MagicMock()
            self.test_activity.id = 3
            self.test_activity.name = "Test Activity"
            self.test_activity.email_templates = {}
    
    def tearDown(self):
        """Clean up test environment"""
        self.app_context.pop()
    
    def test_all_six_email_types(self):
        """Test all 6 email template types"""
        template_types = [
            'newPass', 
            'paymentReceived', 
            'latePayment', 
            'signup', 
            'redeemPass', 
            'survey_invitation'
        ]
        
        for template_type in template_types:
            with self.subTest(template=template_type):
                # Get template path
                template_path = safe_template(template_type)
                self.assertIn('_compiled', template_path, 
                             f"{template_type} should use compiled template")
                
                # Create context for template
                base_context = {
                    'user_name': 'Test User',
                    'activity_name': 'Test Activity',
                    'title': f'Test {template_type}',
                    'intro_text': f'Testing {template_type} template'
                }
                
                # Add blocks for templates that need them
                if template_type in ['newPass', 'paymentReceived', 'latePayment', 'redeemPass']:
                    pass_data = {
                        'activity': {'name': 'Test Activity'},
                        'user': {'name': 'Test User', 'email': 'test@example.com'}
                    }
                    base_context['owner_html'] = render_template(
                        "email_blocks/owner_card_inline.html", 
                        pass_data=pass_data
                    )
                    base_context['history_html'] = render_template(
                        "email_blocks/history_table_inline.html", 
                        history=[]
                    )
                
                # Get merged context
                context = get_email_context(self.test_activity, template_type, base_context)
                
                # Verify context has required fields
                self.assertIn('title', context)
                self.assertIn('intro_text', context)
                
                # Render template
                html = render_template(template_path, **context)
                self.assertIsNotNone(html)
                self.assertGreater(len(html), 100, 
                                  f"{template_type} should render content")
    
    def test_customization_saving_and_retrieval(self):
        """Test saving and retrieving email customizations"""
        # Set customizations
        self.test_activity.email_templates = {
            'newPass': {
                'subject': 'Custom Subject',
                'title': 'Custom Title',
                'intro_text': 'Custom intro text',
                'custom_message': 'Special message'
            }
        }
        
        # Retrieve and verify
        base_context = {'title': 'Default Title'}
        context = get_email_context(self.test_activity, 'newPass', base_context)
        
        self.assertEqual(context['subject'], 'Custom Subject')
        self.assertEqual(context['title'], 'Custom Title')
        self.assertEqual(context['intro_text'], 'Custom intro text')
        self.assertEqual(context['custom_message'], 'Special message')
    
    def test_blocks_preserved_in_all_operations(self):
        """Test that email blocks are never overridden"""
        # Try to override blocks via customizations
        self.test_activity.email_templates = {
            'newPass': {
                'title': 'Custom Title',
                'owner_html': 'MALICIOUS OVERRIDE',  # Should be ignored
                'history_html': 'ANOTHER OVERRIDE'   # Should be ignored
            }
        }
        
        # Create base context with blocks
        base_context = {
            'owner_html': '<div>ORIGINAL OWNER BLOCK</div>',
            'history_html': '<div>ORIGINAL HISTORY BLOCK</div>'
        }
        
        # Get merged context
        context = get_email_context(self.test_activity, 'newPass', base_context)
        
        # Verify blocks are preserved
        self.assertEqual(context['owner_html'], '<div>ORIGINAL OWNER BLOCK</div>')
        self.assertEqual(context['history_html'], '<div>ORIGINAL HISTORY BLOCK</div>')
        self.assertEqual(context['title'], 'Custom Title')  # Other customizations work
    
    def test_default_values_when_no_customizations(self):
        """Test default values are used when no customizations exist"""
        # Activity with no customizations
        activity_no_custom = MagicMock()
        activity_no_custom.email_templates = None
        
        context = get_email_context(activity_no_custom, 'newPass', {})
        
        # Should have default values
        self.assertIn('subject', context)
        self.assertIn('title', context)
        self.assertIn('intro_text', context)
        self.assertIn('conclusion_text', context)
        
        # Defaults should not be empty
        self.assertIsNotNone(context['subject'])
        self.assertIsNotNone(context['title'])
    
    @patch('utils.send_email')
    def test_email_preview_generation(self, mock_send):
        """Test email preview generation"""
        with self.client.session_transaction() as sess:
            sess['admin'] = 1
        
        # Test preview for each template type
        template_types = ['newPass', 'paymentReceived', 'signup']
        
        for template_type in template_types:
            response = self.client.get(
                f'/activity/3/email-preview?type={template_type}'
            )
            self.assertEqual(response.status_code, 200)
            
            html = response.data.decode('utf-8')
            
            # Should contain preview elements
            if template_type in ['newPass', 'paymentReceived']:
                # Should have owner block for these templates
                self.assertIn('owner', html.lower(), 
                             f"{template_type} preview should contain owner block")
    
    def test_customization_persistence(self):
        """Test that customizations persist correctly"""
        # Save customizations
        custom_data = {
            'subject': 'Persistent Subject',
            'title': 'Persistent Title',
            'intro_text': 'This should persist'
        }
        
        self.test_activity.email_templates = {'newPass': custom_data}
        
        # Retrieve multiple times
        for i in range(3):
            context = get_email_context(self.test_activity, 'newPass', {})
            self.assertEqual(context['subject'], 'Persistent Subject')
            self.assertEqual(context['title'], 'Persistent Title')
            self.assertEqual(context['intro_text'], 'This should persist')


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)