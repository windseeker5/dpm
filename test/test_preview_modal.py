#!/usr/bin/env python3
"""
Test file for Email Template Preview Modal System

Tests the modal-based preview functionality for email templates,
including device toggle, template navigation, and responsive behavior.
"""

import unittest
import os
import sys
import time
import tempfile
from datetime import datetime, timedelta

# Add the parent directory to sys.path to import our application modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our application modules
import app
from models import db, Activity, Admin


class TestPreviewModal(unittest.TestCase):
    """Test cases for the Email Template Preview Modal System"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary database
        db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        app.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.app.test_client()
        self.app_context = app.app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
        
        # Create test admin user
        admin = Admin(
            email="test@example.com",
            password_hash="$2b$12$somehashedpassword123",
            first_name="Test",
            last_name="Admin"
        )
        db.session.add(admin)
        
        # Create test activity
        self.test_activity = Activity(
            name="Test Activity for Modal",
            created_by=1,
            type="fitness",
            start_date=datetime.now() + timedelta(days=7),
            description="Test activity for modal testing"
        )
        db.session.add(self.test_activity)
        db.session.commit()
        
        # Login as admin
        with self.app.session_transaction() as sess:
            sess['admin'] = 1
    
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_modal_structure_in_template(self):
        """Test that the modal HTML structure is properly included in the template"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for modal structure elements
        self.assertIn('id="previewModal"', html_content)
        self.assertIn('class="modal modal-lg fade"', html_content)
        self.assertIn('id="previewModalLabel"', html_content)
        self.assertIn('Email Template Preview', html_content)
        
        # Check for device toggle buttons
        self.assertIn('id="desktopView"', html_content)
        self.assertIn('id="mobileView"', html_content)
        self.assertIn('data-device="desktop"', html_content)
        self.assertIn('data-device="mobile"', html_content)
        
        # Check for iframe container
        self.assertIn('id="previewIframe"', html_content)
        self.assertIn('id="previewWrapper"', html_content)
        
        # Check for template navigation buttons
        self.assertIn('template-nav-btn', html_content)
        
        # Check for modal action buttons
        self.assertIn('id="openInNewTab"', html_content)
        self.assertIn('Open in New Tab', html_content)
    
    def test_preview_button_data_attributes(self):
        """Test that preview buttons have correct data attributes for modal triggering"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for modal trigger attributes
        self.assertIn('data-bs-toggle="modal"', html_content)
        self.assertIn('data-bs-target="#previewModal"', html_content)
        self.assertIn('data-template-type=', html_content)
        self.assertIn('data-template-name=', html_content)
        self.assertIn('data-activity-id=', html_content)
        
        # Check that button text is updated
        self.assertIn('Preview Template', html_content)
        self.assertIn('ti-eye', html_content)
    
    def test_modal_css_classes(self):
        """Test that required CSS classes for responsive modal are present"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for modal sizing classes
        self.assertIn('modal-xl', html_content)
        self.assertIn('modal-dialog-centered', html_content)
        
        # Check for responsive wrapper classes
        self.assertIn('iframe-wrapper', html_content)
        self.assertIn('preview-container', html_content)
        
        # Check for CSS styles in the style block
        self.assertIn('.iframe-wrapper.desktop', html_content)
        self.assertIn('.iframe-wrapper.mobile', html_content)
        self.assertIn('width: 375px', html_content)
    
    def test_javascript_modal_functionality(self):
        """Test that JavaScript for modal functionality is included"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for modal-related JavaScript variables and functions
        self.assertIn('previewModal', html_content)
        self.assertIn('previewIframe', html_content)
        self.assertIn('previewWrapper', html_content)
        self.assertIn('updatePreview', html_content)
        self.assertIn('desktopView', html_content)
        self.assertIn('mobileView', html_content)
        
        # Check for event listeners setup
        self.assertIn('addEventListener', html_content)
        self.assertIn('data-bs-target="#previewModal"', html_content)
    
    def test_template_navigation_buttons(self):
        """Test that template navigation buttons are generated for all template types"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for common email template types
        expected_templates = ['newPass', 'passConfirmation', 'passReminder', 'waitlist', 'cancellation']
        
        for template_type in expected_templates:
            # Check that template navigation buttons exist
            self.assertIn(f'data-template-type="{template_type}"', html_content)
    
    def test_modal_accessibility_attributes(self):
        """Test that proper ARIA attributes are included for accessibility"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for ARIA attributes
        self.assertIn('aria-labelledby="previewModalLabel"', html_content)
        self.assertIn('aria-hidden="true"', html_content)
        self.assertIn('aria-label="Close"', html_content)
        self.assertIn('role="group"', html_content)
        self.assertIn('aria-label="Device preview toggle"', html_content)
        self.assertIn('aria-label="Template type navigation"', html_content)
        
        # Check for proper title attribute on iframe
        self.assertIn('title="Email template preview"', html_content)
    
    def test_preview_url_generation(self):
        """Test that preview URLs are correctly generated for the iframe"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check that JavaScript contains the correct URL pattern
        expected_url_pattern = f'/activity/{self.test_activity.id}/email-preview'
        self.assertIn(expected_url_pattern, html_content)
        
        # Check that the URL includes the type parameter
        self.assertIn('?type=', html_content)
    
    def test_modal_responsive_behavior(self):
        """Test that responsive CSS for mobile devices is included"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for mobile-specific CSS rules
        self.assertIn('@media (max-width: 767.98px)', html_content)
        self.assertIn('max-width: 95%', html_content)
        self.assertIn('width: 100% !important', html_content)
        
        # Check that device toggle buttons are hidden on mobile
        self.assertIn('.modal-header .btn-group', html_content)
        self.assertIn('display: none', html_content)
    
    def test_device_toggle_button_states(self):
        """Test that device toggle buttons have proper active states"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check that desktop view is active by default
        desktop_button_pattern = 'id="desktopView"'
        desktop_active_pattern = 'btn-outline-primary active'
        
        # Find desktop button and check it has active class
        desktop_button_start = html_content.find(desktop_button_pattern)
        self.assertNotEqual(desktop_button_start, -1, "Desktop view button not found")
        
        # Check for active state styling in CSS
        self.assertIn('.btn-group .btn.active', html_content)
        self.assertIn('background-color: #206bc4', html_content)


class TestPreviewModalIntegration(unittest.TestCase):
    """Integration tests for preview modal with existing email system"""
    
    def setUp(self):
        """Set up integration test fixtures."""
        db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        app.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.app.test_client()
        self.app_context = app.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test data
        admin = Admin(
            email="integration@example.com",
            password_hash="$2b$12$somehashedpassword123",
            first_name="Integration",
            last_name="Test"
        )
        db.session.add(admin)
        
        self.test_activity = Activity(
            name="Integration Test Activity",
            created_by=1,
            type="sports",
            start_date=datetime.now() + timedelta(days=14),
            description="Activity for integration testing"
        )
        db.session.add(self.test_activity)
        db.session.commit()
        
        with self.app.session_transaction() as sess:
            sess['admin'] = 1
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_modal_with_customized_templates(self):
        """Test modal functionality with customized email templates"""
        # First, save some custom email template data
        template_data = {
            'csrf_token': 'test-token',
            'newPass_subject': 'Custom Pass Subject',
            'newPass_title': 'Custom Pass Title',
            'newPass_intro_text': 'Custom introduction text',
            'passConfirmation_subject': 'Custom Confirmation Subject'
        }
        
        response = self.app.post(
            f'/activity/{self.test_activity.id}/save-email-templates',
            data=template_data,
            follow_redirects=True
        )
        
        # Now check that the modal shows the customized status
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check that customized templates are marked as such
        self.assertIn('(Customized)', html_content)
        
        # Check that the modal includes all template types
        self.assertIn('data-template-type="newPass"', html_content)
        self.assertIn('data-template-type="passConfirmation"', html_content)
    
    def test_modal_preview_url_accessibility(self):
        """Test that the preview URLs generated by the modal are accessible"""
        response = self.app.get(f'/activity/{self.test_activity.id}/email-templates')
        self.assertEqual(response.status_code, 200)
        
        # Test that the preview endpoint exists and returns proper content
        preview_response = self.app.get(f'/activity/{self.test_activity.id}/email-preview?type=newPass')
        self.assertEqual(preview_response.status_code, 200)
        
        # Check that it returns HTML content (email template)
        preview_content = preview_response.data.decode('utf-8')
        self.assertIn('<html', preview_content.lower())
        self.assertIn('email', preview_content.lower())


def run_tests():
    """Run all preview modal tests"""
    print("Running Email Template Preview Modal Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPreviewModal))
    suite.addTests(loader.loadTestsFromTestCase(TestPreviewModalIntegration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)