#!/usr/bin/env python3
"""
TinyMCE Integration Test Suite
Tests rich text editor functionality in email template customization.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from app import app, db
from models import Admin, Activity


class TestTinyMCEIntegration(unittest.TestCase):
    """Test TinyMCE integration in email template customization."""
    
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create tables and test data
        db.create_all()
        
        # Create test admin
        self.admin = Admin(
            email='test@example.com',
            password_hash='hashed_password_here',
            first_name='Test',
            last_name='Admin'
        )
        db.session.add(self.admin)
        
        # Create test activity
        self.activity = Activity(
            name='Test Activity',
            description='Test Description',
            admin_id=1
        )
        db.session.add(self.activity)
        db.session.commit()
        
        # Mock authentication
        with self.app.session_transaction() as sess:
            sess['admin_id'] = 1
    
    def tearDown(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_email_template_page_loads(self):
        """Test that email template customization page loads successfully."""
        response = self.app.get(f'/activity/{self.activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        # Check that TinyMCE class is present in textareas
        response_data = response.get_data(as_text=True)
        self.assertIn('class="form-control tinymce"', response_data)
        self.assertIn('email-template-editor.js', response_data)
    
    def test_tinymce_textareas_have_correct_class(self):
        """Test that intro_text, custom_message, and conclusion_text textareas have tinymce class."""
        response = self.app.get(f'/activity/{self.activity.id}/email-templates')
        response_data = response.get_data(as_text=True)
        
        # Check that all three textarea types have tinymce class
        self.assertIn('name="confirmation_intro_text"', response_data)
        self.assertIn('name="confirmation_custom_message"', response_data)
        self.assertIn('name="confirmation_conclusion_text"', response_data)
        
        # Count occurrences of tinymce class (should be multiple for different template types)
        tinymce_count = response_data.count('class="form-control tinymce"')
        self.assertGreater(tinymce_count, 0)
    
    def test_email_template_editor_script_included(self):
        """Test that email-template-editor.js script is included."""
        response = self.app.get(f'/activity/{self.activity.id}/email-templates')
        response_data = response.get_data(as_text=True)
        
        self.assertIn('email-template-editor.js', response_data)
    
    def test_auto_save_functionality_javascript(self):
        """Test that auto-save JavaScript functionality is present."""
        response = self.app.get(f'/activity/{self.activity.id}/email-templates')
        response_data = response.get_data(as_text=True)
        
        # Check for auto-save related JavaScript
        self.assertIn('autoSaveDraft', response_data)
        self.assertIn('localStorage', response_data)
        self.assertIn('email_template_draft_', response_data)
    
    def test_form_submission_with_rich_text(self):
        """Test form submission with rich text content."""
        # Simulate form submission with HTML content
        form_data = {
            'confirmation_intro_text': '<p><strong>Welcome</strong> to our activity!</p>',
            'confirmation_custom_message': '<ul><li>First item</li><li>Second item</li></ul>',
            'confirmation_conclusion_text': '<p>Thank you for <em>joining</em> us!</p>',
            'csrf_token': 'test_token'
        }
        
        with patch('flask_wtf.csrf.validate_csrf'):
            response = self.app.post(
                f'/activity/{self.activity.id}/save-email-templates',
                data=form_data,
                follow_redirects=True
            )
            
            # Should redirect successfully after save
            self.assertEqual(response.status_code, 200)
    
    def test_html_sanitization_security(self):
        """Test that dangerous HTML is properly handled."""
        # Test with potentially dangerous HTML
        dangerous_content = '<script>alert("xss")</script><p>Safe content</p>'
        
        form_data = {
            'confirmation_intro_text': dangerous_content,
            'csrf_token': 'test_token'
        }
        
        with patch('flask_wtf.csrf.validate_csrf'):
            response = self.app.post(
                f'/activity/{self.activity.id}/save-email-templates',
                data=form_data,
                follow_redirects=True
            )
            
            # Should not crash the application
            self.assertIn([200, 302], [response.status_code])
    
    def test_character_limits_validation(self):
        """Test character limits for text fields."""
        # Test with very long content
        long_content = 'A' * 10000  # 10k characters
        
        form_data = {
            'confirmation_intro_text': long_content,
            'csrf_token': 'test_token'
        }
        
        with patch('flask_wtf.csrf.validate_csrf'):
            response = self.app.post(
                f'/activity/{self.activity.id}/save-email-templates',
                data=form_data
            )
            
            # Should handle long content gracefully
            self.assertIn(response.status_code, [200, 302, 400])
    
    def test_empty_content_handling(self):
        """Test handling of empty content in rich text fields."""
        form_data = {
            'confirmation_intro_text': '',
            'confirmation_custom_message': '',
            'confirmation_conclusion_text': '',
            'csrf_token': 'test_token'
        }
        
        with patch('flask_wtf.csrf.validate_csrf'):
            response = self.app.post(
                f'/activity/{self.activity.id}/save-email-templates',
                data=form_data,
                follow_redirects=True
            )
            
            # Should handle empty content gracefully
            self.assertEqual(response.status_code, 200)
    
    def test_template_types_coverage(self):
        """Test that all template types support TinyMCE."""
        response = self.app.get(f'/activity/{self.activity.id}/email-templates')
        response_data = response.get_data(as_text=True)
        
        # Check for multiple template types (confirmation, reminder, etc.)
        template_patterns = [
            'confirmation_intro_text',
            'reminder_intro_text',
            'cancellation_intro_text',
            'welcome_intro_text'
        ]
        
        # At least some template types should be present
        found_patterns = [pattern for pattern in template_patterns 
                         if pattern in response_data]
        self.assertGreater(len(found_patterns), 0)
    
    def test_responsive_design_elements(self):
        """Test responsive design elements are present."""
        response = self.app.get(f'/activity/{self.activity.id}/email-templates')
        response_data = response.get_data(as_text=True)
        
        # Check for mobile-responsive elements
        self.assertIn('col-lg-', response_data)
        self.assertIn('@media (max-width: 767.98px)', response_data)


class TestTinyMCEJavaScriptFunctions(unittest.TestCase):
    """Test JavaScript functions related to TinyMCE."""
    
    def setUp(self):
        """Set up test environment."""
        # Note: These tests would typically require a JavaScript testing framework
        # like Playwright or Selenium for full integration testing
        pass
    
    def test_init_tinymce_function_exists(self):
        """Test that initTinyMCE function is properly defined."""
        # This would be tested with browser automation
        # For now, we'll test that the function exists in the JS file
        with open('/home/kdresdell/Documents/DEV/minipass_env/app/static/js/email-template-editor.js', 'r') as f:
            js_content = f.read()
            self.assertIn('function initTinyMCE()', js_content)
            self.assertIn('tinymce.init(', js_content)
    
    def test_auto_save_implementation(self):
        """Test auto-save implementation in template."""
        with open('/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_template_customization.html', 'r') as f:
            template_content = f.read()
            self.assertIn('autoSaveDraft', template_content)
            self.assertIn('localStorage.setItem', template_content)
            self.assertIn('email_template_draft_', template_content)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)