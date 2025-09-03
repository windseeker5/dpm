#!/usr/bin/env python3
"""
Unit tests for Email Template Customization UI

Tests the redesigned accordion-based email template interface including:
- Accordion expand/collapse functionality
- Activity context header visibility
- Mobile responsiveness
- Form field accessibility

Created: 2025-09-02
Author: Claude Code (Flask UI Development Specialist)
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Activity, Admin
import tempfile


class TestEmailTemplateUI(unittest.TestCase):
    """Test cases for the redesigned email template customization interface"""

    def setUp(self):
        """Set up test environment"""
        # Configure Flask app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Create test database
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up after tests"""
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
        self.app_context.pop()

    @patch('app.Activity')
    @patch('app.session')
    def test_email_template_page_loads(self, mock_session, mock_activity):
        """Test that the email template customization page loads successfully"""
        # Mock authenticated session
        mock_session.get.return_value = 'test@example.com'
        
        # Mock activity data
        mock_activity_instance = MagicMock()
        mock_activity_instance.id = 1
        mock_activity_instance.name = "Test Activity"
        mock_activity_instance.description = "Test Description"
        mock_activity_instance.image = None
        
        mock_activity.query.get.return_value = mock_activity_instance
        
        with patch('app.render_template') as mock_render:
            mock_render.return_value = '<html>Test Template</html>'
            
            response = self.client.get('/activity/1/email-templates')
            
            # Verify template was called with correct context
            mock_render.assert_called_once()
            template_name, context = mock_render.call_args[0][0], mock_render.call_args[1]
            
            self.assertEqual(template_name, 'email_template_customization.html')
            self.assertEqual(context['activity'], mock_activity_instance)

    def test_accordion_structure_in_template(self):
        """Test that the template contains proper accordion structure"""
        with app.test_request_context():
            # Mock activity and template data
            activity = MagicMock()
            activity.id = 1
            activity.name = "Test Activity"
            activity.description = "Test Description"
            activity.image = None
            
            template_types = {
                'welcome': 'Welcome Email',
                'confirmation': 'Confirmation Email',
                'reminder': 'Reminder Email'
            }
            
            current_templates = {}
            
            # Render the template with test data
            with patch('flask.render_template_string') as mock_render:
                from jinja2 import Template
                
                # Read the actual template file
                template_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    'templates', 
                    'email_template_customization.html'
                )
                
                with open(template_path, 'r') as f:
                    template_content = f.read()
                
                # Check for key accordion elements
                self.assertIn('accordion', template_content.lower())
                self.assertIn('accordion-item', template_content)
                self.assertIn('accordion-header', template_content)
                self.assertIn('accordion-button', template_content)
                self.assertIn('accordion-collapse', template_content)
                self.assertIn('data-bs-toggle="collapse"', template_content)

    def test_activity_header_structure(self):
        """Test that the activity header contains proper elements"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates', 
            'email_template_customization.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for activity header elements
        self.assertIn('activity-header-clean', template_content)
        self.assertIn('header-split-layout', template_content)
        self.assertIn('activity-title', template_content)
        self.assertIn('activity-description', template_content)
        self.assertIn('EMAIL TEMPLATES', template_content)
        self.assertIn('badge-active', template_content)

    def test_mobile_responsive_classes(self):
        """Test that mobile responsive classes are present"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates', 
            'email_template_customization.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for responsive column classes
        self.assertIn('col-lg-8', template_content)
        self.assertIn('col-lg-4', template_content)
        
        # Check for mobile styles in CSS
        self.assertIn('@media (max-width: 767.98px)', template_content)
        self.assertIn('flex-direction: column', template_content)

    def test_preview_button_replaces_iframe(self):
        """Test that preview button is used instead of inline iframe"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates', 
            'email_template_customization.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check that iframe is NOT present
        self.assertNotIn('<iframe', template_content)
        
        # Check that preview button IS present
        self.assertIn('Open Preview', template_content)
        self.assertIn('ti-external-link', template_content)
        self.assertIn('target="_blank"', template_content)

    def test_tabler_icons_usage(self):
        """Test that Tabler icons are used consistently"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates', 
            'email_template_customization.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for proper Tabler icon usage
        tabler_icons = [
            'ti-mail',
            'ti-arrow-left', 
            'ti-info-circle',
            'ti-eye',
            'ti-external-link',
            'ti-device-floppy',
            'ti-x',
            'ti-trash'
        ]
        
        for icon in tabler_icons:
            self.assertIn(icon, template_content, f"Tabler icon '{icon}' should be present")

    def test_form_accessibility(self):
        """Test that form elements have proper accessibility attributes"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates', 
            'email_template_customization.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for proper form labels
        self.assertIn('form-label', template_content)
        
        # Check for ARIA attributes in accordion
        self.assertIn('aria-expanded', template_content)
        self.assertIn('aria-controls', template_content)
        self.assertIn('aria-labelledby', template_content)
        
        # Check for proper input placeholders
        self.assertIn('placeholder="Leave empty to use system default"', template_content)

    @patch('app.Activity')
    @patch('app.session')
    def test_template_status_indicators(self, mock_session, mock_activity):
        """Test that template status indicators work correctly"""
        mock_session.get.return_value = 'test@example.com'
        
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates', 
            'email_template_customization.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for status indicators
        self.assertIn('(Customized)', template_content)
        self.assertIn('(Using default)', template_content)
        self.assertIn('Template Status:', template_content)
        self.assertIn('badge bg-blue-lt', template_content)
        self.assertIn('badge bg-secondary-lt', template_content)

    def test_save_cancel_buttons(self):
        """Test that save and cancel buttons are properly structured"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates', 
            'email_template_customization.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for save button
        self.assertIn('Save All Templates', template_content)
        self.assertIn('btn btn-primary', template_content)
        self.assertIn('ti-device-floppy', template_content)
        
        # Check for cancel button  
        self.assertIn('Cancel', template_content)
        self.assertIn('btn btn-outline-secondary', template_content)
        self.assertIn('ti-x', template_content)

    def test_css_structure_and_imports(self):
        """Test that CSS structure is properly organized"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates', 
            'email_template_customization.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for activity header CSS import
        self.assertIn("css/activity-header-clean.css", template_content)
        
        # Check for custom styles in {% block head %}
        self.assertIn("{% block head %}", template_content)
        
        # Check for dashboard container max-width
        self.assertIn("max-width: 1400px", template_content)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)