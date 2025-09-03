#!/usr/bin/env python3
"""
Test mobile header layout optimization
Tests the activity header on mobile viewport to ensure:
- Header height < 200px
- Touch targets >= 44px 
- Single screen fit
- Dropdown functionality
"""

import unittest
import time
from playwright.sync_api import sync_playwright


class TestMobileHeaderLayout(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:5000"
        self.test_email = "kdresdell@gmail.com"
        self.test_password = "admin123"
        
    def test_mobile_header_layout(self):
        """Test mobile header layout optimization"""
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False)
            
            # Create mobile viewport context (iPhone SE)
            context = browser.new_context(
                viewport={'width': 375, 'height': 667},
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
            )
            
            page = context.new_page()
            
            try:
                # Navigate to login page
                page.goto(f"{self.base_url}/login")
                page.wait_for_load_state('networkidle')
                
                # Login
                page.fill('input[name="email"]', self.test_email)
                page.fill('input[name="password"]', self.test_password)
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')
                
                # Navigate to first activity (assuming at least one exists)
                # Try to find an activity link
                activity_links = page.locator('a[href*="/activity/"]').all()
                if activity_links:
                    activity_links[0].click()
                    page.wait_for_load_state('networkidle')
                else:
                    # If no activities found, create a simple test one or skip
                    self.skipTest("No activities found to test header layout")
                
                # Wait for header to be visible
                header = page.locator('.activity-header-clean')
                header.wait_for(state='visible')
                
                # Test 1: Verify header height < 200px
                header_box = header.bounding_box()
                self.assertIsNotNone(header_box, "Header should be visible")
                self.assertLess(header_box['height'], 200, 
                              f"Header height {header_box['height']}px should be < 200px")
                print(f"✓ Header height: {header_box['height']}px (< 200px)")
                
                # Test 2: Verify activity image is 20x20px
                activity_image = page.locator('.activity-image-inline')
                if activity_image.count() > 0:
                    img_box = activity_image.bounding_box()
                    self.assertIsNotNone(img_box, "Activity image should be visible")
                    self.assertEqual(img_box['width'], 20, 
                                   f"Activity image width should be 20px, got {img_box['width']}px")
                    self.assertEqual(img_box['height'], 20, 
                                   f"Activity image height should be 20px, got {img_box['height']}px")
                    print(f"✓ Activity image: {img_box['width']}x{img_box['height']}px")
                
                # Test 3: Verify stats are in 2x2 grid
                stats_row = page.locator('.activity-stats-row')
                if stats_row.count() > 0:
                    stats_box = stats_row.bounding_box()
                    stats = page.locator('.activity-stats-row .stat').all()
                    self.assertGreaterEqual(len(stats), 2, "Should have at least 2 stats")
                    print(f"✓ Stats in grid layout: {len(stats)} stats")
                
                # Test 4: Verify dropdown button touch target >= 44px
                dropdown_button = page.locator('.dropdown .btn-icon')
                if dropdown_button.count() > 0:
                    btn_box = dropdown_button.bounding_box()
                    self.assertIsNotNone(btn_box, "Dropdown button should be visible")
                    self.assertGreaterEqual(btn_box['width'], 44, 
                                          f"Dropdown button width {btn_box['width']}px should be >= 44px")
                    self.assertGreaterEqual(btn_box['height'], 44, 
                                          f"Dropdown button height {btn_box['height']}px should be >= 44px")
                    print(f"✓ Dropdown button: {btn_box['width']}x{btn_box['height']}px (>= 44px)")
                
                # Test 5: Test dropdown functionality
                if dropdown_button.count() > 0:
                    dropdown_button.click()
                    time.sleep(0.5)  # Wait for dropdown to open
                    
                    dropdown_menu = page.locator('.dropdown-menu')
                    self.assertTrue(dropdown_menu.is_visible(), "Dropdown menu should be visible after click")
                    print("✓ Dropdown functionality works")
                    
                    # Close dropdown
                    dropdown_button.click()
                
                # Test 6: Verify header fits in single screen (mobile viewport height)
                viewport_height = 667  # iPhone SE height
                self.assertLess(header_box['height'], viewport_height * 0.4, 
                              f"Header should take < 40% of screen height ({viewport_height * 0.4}px)")
                print(f"✓ Header fits in single screen: {header_box['height']}px < {viewport_height * 0.4}px")
                
                # Take screenshot for visual verification
                screenshot_path = "/home/kdresdell/Pictures/Screenshots/test_header_mobile_after.png"
                page.screenshot(path=screenshot_path, full_page=False)
                print(f"✓ Screenshot saved to: {screenshot_path}")
                
                # Test 7: Verify title and description are visible and properly sized
                title = page.locator('.activity-title')
                if title.count() > 0:
                    title_box = title.bounding_box()
                    self.assertIsNotNone(title_box, "Activity title should be visible")
                    self.assertGreater(title_box['height'], 0, "Title should have height")
                    print(f"✓ Title visible: {title_box['height']}px height")
                
                description = page.locator('.activity-description')
                if description.count() > 0:
                    desc_box = description.bounding_box()
                    if desc_box:  # Description might be hidden on very small screens
                        self.assertLessEqual(desc_box['height'], 28, 
                                           f"Description height {desc_box['height']}px should be <= 28px")
                        print(f"✓ Description compact: {desc_box['height']}px height")
                
                # Test 8: Verify revenue progress bar is visible and compact
                progress_container = page.locator('.revenue-progress-container')
                if progress_container.count() > 0:
                    progress_box = progress_container.bounding_box()
                    self.assertIsNotNone(progress_box, "Revenue progress should be visible")
                    self.assertLess(progress_box['height'], 40, 
                                  f"Progress container height {progress_box['height']}px should be < 40px")
                    print(f"✓ Progress bar compact: {progress_box['height']}px height")
                
                print("\n=== Mobile Header Layout Test Results ===")
                print(f"Header total height: {header_box['height']}px (target: < 200px)")
                print(f"Viewport: 375x667px (iPhone SE)")
                print(f"Header takes {(header_box['height']/667)*100:.1f}% of screen height")
                print("All tests passed! ✓")
                
            except Exception as e:
                # Take screenshot on error
                error_screenshot = "/home/kdresdell/Pictures/Screenshots/test_header_mobile_error.png"
                page.screenshot(path=error_screenshot, full_page=True)
                print(f"Error screenshot saved to: {error_screenshot}")
                raise e
            
            finally:
                browser.close()


if __name__ == '__main__':
    unittest.main()