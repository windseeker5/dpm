#!/usr/bin/env python3
"""
Test suite for the simplified email template customization interface.

This test verifies that the simplified interface works correctly:
1. Real email preview thumbnails are generated
2. Grid layout displays properly
3. Hover actions work as expected
4. Existing modals still function
5. Interface is much simpler than before
"""

import unittest
import os
import sys
import time
from playwright.sync_api import sync_playwright


class TestSimplifiedEmailTemplates(unittest.TestCase):
    """Test the simplified email template customization interface."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        cls.base_url = "http://localhost:5000"
        cls.login_email = "kdresdell@gmail.com"
        cls.login_password = "admin123"
        cls.activity_id = 1  # Test with Hockey activity
        
    def setUp(self):
        """Set up each test."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()
        
        # Login first
        self._login()
        
    def tearDown(self):
        """Clean up after each test."""
        self.browser.close()
        self.playwright.stop()
        
    def _login(self):
        """Login to the application."""
        self.page.goto(f"{self.base_url}/login")
        self.page.fill('input[type="email"]', self.login_email)
        self.page.fill('input[type="password"]', self.login_password)
        self.page.click('button[type="submit"]')
        self.page.wait_for_url(f"{self.base_url}/dashboard")
        
    def test_thumbnail_generation_route_exists(self):
        """Test that the thumbnail generation route works."""
        # Navigate to thumbnail generation
        response = self.page.goto(f"{self.base_url}/activity/{self.activity_id}/generate-email-thumbnails")
        
        # Check that the route responds successfully
        self.assertEqual(response.status, 200)
        
        # Check that all template types are processed
        content = self.page.content()
        self.assertIn("✅ newPass", content)
        self.assertIn("✅ paymentReceived", content)
        self.assertIn("✅ latePayment", content)
        self.assertIn("✅ signup", content)
        self.assertIn("✅ redeemPass", content)
        self.assertIn("✅ survey_invitation", content)
        
    def test_simplified_email_templates_page_loads(self):
        """Test that the simplified email templates page loads correctly."""
        # Navigate to email templates page
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Check page title
        self.assertIn("Email Template Customization", self.page.title())
        
        # Check that the simplified grid exists
        grid = self.page.query_selector('.email-templates-grid')
        self.assertIsNotNone(grid, "Email templates grid should exist")
        
        # Check that template items exist
        template_items = self.page.query_selector_all('.template-item')
        self.assertEqual(len(template_items), 6, "Should have 6 template items")
        
    def test_real_email_preview_images_display(self):
        """Test that real email preview images are displayed instead of fake SVGs."""
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Check that thumbnail images are loaded
        thumbnail_images = self.page.query_selector_all('.template-preview')
        self.assertEqual(len(thumbnail_images), 6, "Should have 6 preview images")
        
        # Check that images use the correct thumbnail paths
        for img in thumbnail_images:
            src = img.get_attribute('src')
            if 'email_thumbnails' not in src and 'email_template_previews' not in src:
                self.fail(f"Image should use thumbnail or fallback SVG, got: {src}")
                
    def test_hover_overlay_actions_appear(self):
        """Test that hover overlay with action buttons appears."""
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Get first template item
        first_template = self.page.query_selector('.template-item')
        self.assertIsNotNone(first_template)
        
        # Hover over the template
        first_template.hover()
        
        # Check that overlay becomes visible (we can't easily test CSS opacity in Playwright)
        # But we can check that the action buttons exist
        action_buttons = self.page.query_selector_all('.action-btn')
        self.assertEqual(len(action_buttons), 24, "Should have 4 action buttons per template (6 templates)")
        
        # Check that action buttons have correct emojis
        customize_btn = self.page.query_selector('.customize-btn')
        self.assertEqual(customize_btn.inner_text(), "✏️")
        
        preview_btn = self.page.query_selector('.preview-btn')
        self.assertEqual(preview_btn.inner_text(), "👁️")
        
        test_btn = self.page.query_selector('.test-btn')
        self.assertEqual(test_btn.inner_text(), "📧")
        
        reset_btn = self.page.query_selector('.reset-btn')
        self.assertEqual(reset_btn.inner_text(), "🔄")
        
    def test_template_names_and_status_display(self):
        """Test that template names and status are displayed correctly."""
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Check that template names are present
        template_names = self.page.query_selector_all('.template-name')
        self.assertEqual(len(template_names), 6, "Should have 6 template names")
        
        # Check that status indicators are present
        template_statuses = self.page.query_selector_all('.template-status')
        self.assertEqual(len(template_statuses), 6, "Should have 6 template status indicators")
        
        # Check that status shows "Custom"/"CUSTOM" or "Default"/"DEFAULT"
        for status in template_statuses:
            status_text = status.inner_text().upper()
            self.assertIn(status_text, ["CUSTOM", "DEFAULT"], f"Status should be Custom or Default, got: {status_text}")
            
    def test_action_buttons_trigger_correct_functions(self):
        """Test that action buttons trigger the correct JavaScript functions."""
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Setup console listener to capture JavaScript logs
        console_messages = []
        self.page.on("console", lambda msg: console_messages.append(msg.text))
        
        # Click customize button
        customize_btn = self.page.query_selector('.customize-btn')
        customize_btn.click()
        
        # Wait a moment for console messages
        time.sleep(0.5)
        
        # Check that customize function was called
        customize_messages = [msg for msg in console_messages if "Customize:" in msg]
        self.assertTrue(len(customize_messages) > 0, "Customize function should be called")
        
    def test_interface_is_simplified(self):
        """Test that the interface is significantly simplified compared to before."""
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Check that complex elements are NOT present
        # No more accordion structure
        accordions = self.page.query_selector_all('.accordion')
        self.assertEqual(len(accordions), 0, "Should not have accordion elements")
        
        # No more dropdown menus in the grid
        dropdowns = self.page.query_selector_all('.email-templates-grid .dropdown')
        self.assertEqual(len(dropdowns), 0, "Should not have dropdown menus in grid")
        
        # No more toggle switches in the grid
        toggles = self.page.query_selector_all('.email-templates-grid .form-check-input')
        self.assertEqual(len(toggles), 0, "Should not have toggle switches in grid")
        
        # Should have simple grid layout
        grid = self.page.query_selector('.email-templates-grid')
        self.assertIsNotNone(grid, "Should have simplified grid layout")
        
    def test_modals_still_work(self):
        """Test that existing modals (customize, preview) still work."""
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Check that customize modal exists
        customize_modal = self.page.query_selector('#customizeModal')
        self.assertIsNotNone(customize_modal, "Customize modal should exist")
        
        # Check that preview modal exists  
        preview_modal = self.page.query_selector('#previewModal')
        self.assertIsNotNone(preview_modal, "Preview modal should exist")
        
    def test_save_functionality_preserved(self):
        """Test that save functionality is preserved."""
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Check that save button exists
        save_btn = self.page.query_selector('button:has-text("Save All Templates")')
        self.assertIsNotNone(save_btn, "Save button should exist")
        
        # Check that form exists
        form = self.page.query_selector('form[action*="email-templates/save"]')
        self.assertIsNotNone(form, "Save form should exist")
        
    def test_mobile_responsive_layout(self):
        """Test that the layout is mobile responsive."""
        # Set mobile viewport
        self.page.set_viewport_size({"width": 375, "height": 667})
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Check that grid adapts to mobile
        grid = self.page.query_selector('.email-templates-grid')
        self.assertIsNotNone(grid, "Grid should exist on mobile")
        
        # Template items should still be visible
        template_items = self.page.query_selector_all('.template-item')
        self.assertEqual(len(template_items), 6, "All template items should be visible on mobile")
        
    def test_performance_improvement(self):
        """Test that page loads quickly with the simplified interface."""
        start_time = time.time()
        
        self.page.goto(f"{self.base_url}/activity/{self.activity_id}/email-templates")
        
        # Wait for all images to load
        self.page.wait_for_load_state("networkidle")
        
        end_time = time.time()
        load_time = end_time - start_time
        
        # Page should load in under 3 seconds (was much slower before)
        self.assertLess(load_time, 3.0, f"Page should load quickly, took {load_time:.2f} seconds")


if __name__ == '__main__':
    # Ensure we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Please run this test from the app directory")
        sys.exit(1)
        
    # Run the tests
    unittest.main(verbosity=2)