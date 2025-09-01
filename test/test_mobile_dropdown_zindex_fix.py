"""
Unit Test for Mobile Dropdown Z-Index Fix
Tests that mobile dropdown menus display correctly with proper z-index layering
"""
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class TestMobileDropdownZIndex(unittest.TestCase):
    
    def setUp(self):
        """Set up mobile Chrome browser for testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=375,667")  # Mobile size
        chrome_options.add_experimental_option("mobileEmulation", {
            "deviceMetrics": {"width": 375, "height": 667, "pixelRatio": 2.0},
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        })
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
    
    def tearDown(self):
        """Clean up browser"""
        self.driver.quit()
    
    def test_mobile_dropdown_zindex_visibility(self):
        """Test that mobile dropdown appears with correct z-index"""
        
        # Navigate to login page
        self.driver.get("http://localhost:5000")
        
        # Login
        email_input = self.driver.find_element(By.NAME, "email")
        password_input = self.driver.find_element(By.NAME, "password")
        
        email_input.send_keys("kdresdell@gmail.com")
        password_input.send_keys("admin123")
        
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for dashboard to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".kpi-cards-wrapper"))
        )
        
        # Find a KPI dropdown button (mobile view)
        dropdown_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".dropdown button")
        self.assertGreater(len(dropdown_buttons), 0, "No dropdown buttons found")
        
        # Click the first dropdown button
        first_dropdown = dropdown_buttons[0]
        first_dropdown.click()
        
        # Wait for dropdown menu to appear
        dropdown_menu = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".dropdown-menu"))
        )
        
        # Verify dropdown is visible
        self.assertTrue(dropdown_menu.is_displayed(), "Dropdown menu should be visible")
        
        # Verify all time options are present and visible
        dropdown_links = dropdown_menu.find_elements(By.CSS_SELECTOR, "li a")
        self.assertGreater(len(dropdown_links), 0, "No dropdown options found")
        
        # Look for "All time" option specifically
        all_time_found = False
        for link in dropdown_links:
            if "All time" in link.text:
                all_time_found = True
                self.assertTrue(link.is_displayed(), "All time option should be visible")
                break
        
        self.assertTrue(all_time_found, "All time option should exist in dropdown")
        
        # Test z-index by checking computed styles
        z_index = self.driver.execute_script(
            "return window.getComputedStyle(arguments[0]).zIndex;", dropdown_menu
        )
        
        # Z-index should be very high (999999)
        self.assertEqual(z_index, "999999", f"Expected z-index 999999, got {z_index}")
        
        # Verify position is absolute (not fixed)
        position = self.driver.execute_script(
            "return window.getComputedStyle(arguments[0]).position;", dropdown_menu
        )
        self.assertEqual(position, "absolute", f"Expected position absolute, got {position}")
    
    def test_mobile_dropdown_functional_click(self):
        """Test that 'All time' option is clickable and functional"""
        
        # Navigate and login (same as above)
        self.driver.get("http://localhost:5000")
        
        email_input = self.driver.find_element(By.NAME, "email")
        password_input = self.driver.find_element(By.NAME, "password")
        
        email_input.send_keys("kdresdell@gmail.com")
        password_input.send_keys("admin123")
        
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for dashboard
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".kpi-cards-wrapper"))
        )
        
        # Click dropdown
        dropdown_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".dropdown button")
        first_dropdown = dropdown_buttons[0]
        original_text = first_dropdown.text
        first_dropdown.click()
        
        # Wait for dropdown and click "All time"
        dropdown_menu = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".dropdown-menu"))
        )
        
        all_time_link = None
        dropdown_links = dropdown_menu.find_elements(By.CSS_SELECTOR, "li a")
        for link in dropdown_links:
            if "All time" in link.text:
                all_time_link = link
                break
        
        self.assertIsNotNone(all_time_link, "All time link should exist")
        
        # Click the "All time" option
        all_time_link.click()
        
        # Wait for dropdown to close and button text to update
        time.sleep(2)
        
        # Verify button text changed to "All time"
        updated_text = first_dropdown.text
        self.assertIn("All time", updated_text, f"Button should show 'All time', got '{updated_text}'")


if __name__ == '__main__':
    unittest.main()