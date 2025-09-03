"""
Test for desktop header layout - compact design with inline activity picture.
Tests the new compact header design to ensure it meets the requirements:
- Max height of 180px on desktop
- Activity image inline with title (30x30px)
- All elements visible and functional
"""

import unittest
import time
from playwright.sync_api import sync_playwright


class TestDesktopHeaderLayout(unittest.TestCase):
    """Test the compact desktop header layout implementation."""
    
    def setUp(self):
        """Set up test environment."""
        self.base_url = "http://localhost:5000"
        self.login_email = "kdresdell@gmail.com"
        self.login_password = "admin123"
        
    def test_header_height_and_compactness(self):
        """Test that the header meets the height and compactness requirements."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={'width': 1200, 'height': 800})
            page = context.new_page()
            
            try:
                # Login
                page.goto(f"{self.base_url}/login")
                page.fill('input[name="email"]', self.login_email)
                page.fill('input[name="password"]', self.login_password)
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')
                
                # Navigate to first activity dashboard
                page.goto(f"{self.base_url}/dashboard")
                page.wait_for_load_state('networkidle')
                
                # Click on first activity link (assuming there's at least one)
                activity_links = page.query_selector_all('a[href*="/activity/"]')
                if activity_links:
                    activity_links[0].click()
                    page.wait_for_load_state('networkidle')
                else:
                    # Skip test if no activities available
                    self.skipTest("No activities available to test")
                
                # Wait for header to be visible
                header = page.wait_for_selector('.activity-header-clean', timeout=5000)
                self.assertIsNotNone(header, "Header not found")
                
                # Test 1: Header height should be <= 180px
                header_height = header.bounding_box()['height']
                print(f"Header height: {header_height}px")
                self.assertLessEqual(header_height, 180, 
                                   f"Header height {header_height}px exceeds 180px limit")
                
                # Test 2: Activity image should be 30x30px and inline
                inline_image = page.query_selector('.activity-image-inline')
                self.assertIsNotNone(inline_image, "Inline activity image not found")
                
                image_box = inline_image.bounding_box()
                self.assertEqual(image_box['width'], 30, 
                               f"Activity image width {image_box['width']}px should be 30px")
                self.assertEqual(image_box['height'], 30, 
                               f"Activity image height {image_box['height']}px should be 30px")
                
                # Test 3: Title should be next to the image
                title = page.query_selector('.activity-title')
                self.assertIsNotNone(title, "Activity title not found")
                
                title_box = title.bounding_box()
                # Image should be to the left of title (with some margin)
                self.assertLess(image_box['x'] + image_box['width'], title_box['x'], 
                              "Activity image should be to the left of title")
                
                # Test 4: All essential elements should be visible
                self.assertIsNotNone(page.query_selector('.activity-title'), "Title missing")
                self.assertIsNotNone(page.query_selector('.activity-description'), "Description missing")
                self.assertIsNotNone(page.query_selector('.activity-stats-row'), "Stats row missing")
                self.assertIsNotNone(page.query_selector('.revenue-progress-container'), "Revenue progress missing")
                self.assertIsNotNone(page.query_selector('.activity-actions'), "Action buttons missing")
                
                # Test 5: Badge should be visible
                badge = page.query_selector('.badge-active')
                self.assertIsNotNone(badge, "Active badge not found")
                
                # Test 6: User avatars should be visible on the right
                avatars = page.query_selector('.user-avatar-section .avatar-list')
                self.assertIsNotNone(avatars, "User avatars not found")
                
                print("✅ All header layout tests passed")
                
                # Take a screenshot for visual verification
                page.screenshot(path='/home/kdresdell/Pictures/Screenshots/test_header_desktop_after.png')
                print("📸 Screenshot saved to /home/kdresdell/Pictures/Screenshots/test_header_desktop_after.png")
                
            except Exception as e:
                print(f"❌ Test failed: {str(e)}")
                # Take screenshot on failure for debugging
                page.screenshot(path='/home/kdresdell/Pictures/Screenshots/test_header_desktop_failed.png')
                raise
                
            finally:
                browser.close()
    
    def test_stats_visibility_and_formatting(self):
        """Test that all stats are visible and properly formatted."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={'width': 1200, 'height': 800})
            page = context.new_page()
            
            try:
                # Login and navigate to activity
                page.goto(f"{self.base_url}/login")
                page.fill('input[name="email"]', self.login_email)
                page.fill('input[name="password"]', self.login_password)
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')
                
                page.goto(f"{self.base_url}/dashboard")
                page.wait_for_load_state('networkidle')
                
                activity_links = page.query_selector_all('a[href*="/activity/"]')
                if activity_links:
                    activity_links[0].click()
                    page.wait_for_load_state('networkidle')
                else:
                    self.skipTest("No activities available to test")
                
                # Check stats row
                stats = page.query_selector_all('.activity-stats-row .stat')
                self.assertGreaterEqual(len(stats), 4, "Should have at least 4 stats")
                
                # Verify icons and text are present
                for stat in stats:
                    icon = stat.query_selector('i')
                    text = stat.query_selector('span')
                    self.assertIsNotNone(icon, "Stat should have an icon")
                    self.assertIsNotNone(text, "Stat should have text")
                    self.assertTrue(len(text.inner_text()) > 0, "Stat text should not be empty")
                
                print("✅ Stats visibility and formatting tests passed")
                
            finally:
                browser.close()
    
    def test_action_buttons_functionality(self):
        """Test that all action buttons are present and clickable."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={'width': 1200, 'height': 800})
            page = context.new_page()
            
            try:
                # Login and navigate to activity
                page.goto(f"{self.base_url}/login")
                page.fill('input[name="email"]', self.login_email)
                page.fill('input[name="password"]', self.login_password)
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')
                
                page.goto(f"{self.base_url}/dashboard")
                page.wait_for_load_state('networkidle')
                
                activity_links = page.query_selector_all('a[href*="/activity/"]')
                if activity_links:
                    activity_links[0].click()
                    page.wait_for_load_state('networkidle')
                else:
                    self.skipTest("No activities available to test")
                
                # Check desktop action buttons
                desktop_actions = page.query_selector('.activity-actions.d-none.d-md-flex')
                self.assertIsNotNone(desktop_actions, "Desktop action buttons not found")
                
                # Check for expected buttons
                expected_buttons = ['Edit', 'Email Templates', 'Delete', 'Scan', 'Passport']
                buttons = desktop_actions.query_selector_all('a.btn, button.btn')
                
                button_texts = [btn.inner_text().strip() for btn in buttons]
                for expected in expected_buttons:
                    found = any(expected in text for text in button_texts)
                    self.assertTrue(found, f"Expected button '{expected}' not found. Found: {button_texts}")
                
                print("✅ Action buttons functionality tests passed")
                
            finally:
                browser.close()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)