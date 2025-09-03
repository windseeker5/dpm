#!/usr/bin/env python3
"""
Test Activity Dashboard After Checkbox Removal
Tests to verify that the activity dashboard works correctly after removing all checkbox functionality.
"""

import unittest
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

class TestActivityDashboardNoCheckboxes(unittest.TestCase):
    """Test activity dashboard functionality without checkboxes."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with Chrome driver."""
        cls.base_url = "http://localhost:5000"
        cls.login_email = "kdresdell@gmail.com"
        cls.login_password = "admin123"
        
        # Chrome options for testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)
        
        # Login to the application
        cls._login()
    
    @classmethod
    def _login(cls):
        """Login to the application."""
        cls.driver.get(f"{cls.base_url}/login")
        
        email_field = cls.driver.find_element(By.NAME, "email")
        password_field = cls.driver.find_element(By.NAME, "password")
        
        email_field.send_keys(cls.login_email)
        password_field.send_keys(cls.login_password)
        
        login_button = cls.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for login to complete
        WebDriverWait(cls.driver, 10).until(
            lambda driver: "/login" not in driver.current_url
        )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        cls.driver.quit()
    
    def test_activity_dashboard_loads(self):
        """Test that the activity dashboard loads successfully."""
        # Navigate to activity dashboard (assuming there's an activity with ID 5)
        self.driver.get(f"{self.base_url}/activity/5")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check that we're on the right page
        self.assertIn("Activity Dashboard", self.driver.title)
    
    def test_no_checkboxes_present(self):
        """Test that no checkboxes are present on the page."""
        self.driver.get(f"{self.base_url}/activity/5")
        
        # Wait for tables to load
        time.sleep(2)
        
        # Check for absence of checkbox elements
        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        self.assertEqual(len(checkboxes), 0, "Found checkboxes when none should exist")
        
        # Check for absence of bulk actions containers
        bulk_actions = self.driver.find_elements(By.CLASS_NAME, "bulk-actions-container")
        self.assertEqual(len(bulk_actions), 0, "Found bulk actions containers when none should exist")
        
        # Check for absence of select all checkboxes
        select_all = self.driver.find_elements(By.ID, "selectAll")
        self.assertEqual(len(select_all), 0, "Found select all checkbox when none should exist")
        
        # Check for absence of passport/signup checkboxes
        passport_checkboxes = self.driver.find_elements(By.CLASS_NAME, "passport-checkbox")
        self.assertEqual(len(passport_checkboxes), 0, "Found passport checkboxes when none should exist")
        
        signup_checkboxes = self.driver.find_elements(By.CLASS_NAME, "signup-checkbox")
        self.assertEqual(len(signup_checkboxes), 0, "Found signup checkboxes when none should exist")
    
    def test_no_bulk_actions_cards(self):
        """Test that no bulk actions cards are present."""
        self.driver.get(f"{self.base_url}/activity/5")
        time.sleep(2)
        
        # Check for absence of bulk actions cards
        bulk_cards = self.driver.find_elements(By.CLASS_NAME, "bulk-actions-card")
        self.assertEqual(len(bulk_cards), 0, "Found bulk actions cards when none should exist")
        
        # Check for absence of bulk actions by ID
        bulk_actions_by_id = self.driver.find_elements(By.ID, "bulkActions")
        self.assertEqual(len(bulk_actions_by_id), 0, "Found bulk actions element by ID when none should exist")
    
    def test_no_bulk_delete_modal(self):
        """Test that no bulk delete modal is present."""
        self.driver.get(f"{self.base_url}/activity/5")
        time.sleep(2)
        
        # Check for absence of bulk delete modal
        bulk_modal = self.driver.find_elements(By.ID, "bulkDeleteModal")
        self.assertEqual(len(bulk_modal), 0, "Found bulk delete modal when none should exist")
    
    def test_individual_actions_dropdown_works(self):
        """Test that individual Actions dropdowns still work for passports."""
        self.driver.get(f"{self.base_url}/activity/5")
        
        # Wait for tables to load
        time.sleep(3)
        
        # Look for individual action dropdowns
        action_dropdowns = self.driver.find_elements(By.CSS_SELECTOR, ".dropdown-toggle")
        
        if len(action_dropdowns) > 0:
            # Click on the first dropdown
            first_dropdown = action_dropdowns[0]
            self.driver.execute_script("arguments[0].scrollIntoView();", first_dropdown)
            time.sleep(1)
            
            first_dropdown.click()
            time.sleep(1)
            
            # Check that dropdown menu appears
            dropdown_menu = self.driver.find_element(By.CSS_SELECTOR, ".dropdown-menu")
            self.assertTrue(dropdown_menu.is_displayed(), "Dropdown menu should be visible")
            
            # Check for individual action items (Edit, Mark as Paid, Delete, etc.)
            dropdown_items = dropdown_menu.find_elements(By.CSS_SELECTOR, ".dropdown-item")
            self.assertGreater(len(dropdown_items), 0, "Should have dropdown items in Actions menu")
        else:
            # If no dropdowns found, that might be because there's no data
            print("No action dropdowns found - this might be expected if there are no passports/signups")
    
    def test_table_layout_intact(self):
        """Test that table layouts are intact after checkbox removal."""
        self.driver.get(f"{self.base_url}/activity/5")
        time.sleep(2)
        
        # Check that tables are present
        tables = self.driver.find_elements(By.CSS_SELECTOR, "table.table")
        self.assertGreater(len(tables), 0, "Should have at least one table")
        
        for table in tables:
            # Check that table headers are present
            headers = table.find_elements(By.CSS_SELECTOR, "thead th")
            self.assertGreater(len(headers), 0, "Table should have headers")
            
            # Check that there's no empty first column (where checkboxes would have been)
            first_header = headers[0] if headers else None
            if first_header:
                header_text = first_header.text.strip()
                # First column should not be empty or just contain checkbox-related content
                self.assertNotEqual(header_text, "", "First header should not be empty")
                self.assertNotIn("Select", header_text.lower(), "First header should not be about selection")
    
    def test_no_javascript_errors(self):
        """Test that there are no JavaScript console errors after checkbox removal."""
        self.driver.get(f"{self.base_url}/activity/5")
        time.sleep(3)
        
        # Get console logs
        logs = self.driver.get_log('browser')
        
        # Filter for errors (not warnings or info)
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        # Check for checkbox-related errors
        checkbox_errors = [
            error for error in errors 
            if any(keyword in error['message'].lower() for keyword in [
                'checkbox', 'selectall', 'bulk', 'passport-checkbox', 'signup-checkbox'
            ])
        ]
        
        self.assertEqual(len(checkbox_errors), 0, 
                        f"Found checkbox-related JavaScript errors: {checkbox_errors}")
    
    def test_filters_still_work(self):
        """Test that filter buttons still work correctly."""
        self.driver.get(f"{self.base_url}/activity/5")
        time.sleep(2)
        
        # Look for filter buttons
        filter_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".github-filter-btn")
        
        if len(filter_buttons) > 0:
            # Click on a filter button
            for button in filter_buttons:
                if "All" in button.text:
                    button.click()
                    time.sleep(1)
                    
                    # Check that the button becomes active
                    self.assertIn("active", button.get_attribute("class"), 
                                "Filter button should become active when clicked")
                    break
    
    def test_page_responsive_layout(self):
        """Test that page layout is responsive after checkbox removal."""
        self.driver.get(f"{self.base_url}/activity/5")
        time.sleep(2)
        
        # Test desktop view
        self.driver.set_window_size(1920, 1080)
        time.sleep(1)
        
        # Check that tables are visible and properly laid out
        tables = self.driver.find_elements(By.CSS_SELECTOR, "table.table")
        for table in tables:
            self.assertTrue(table.is_displayed(), "Table should be visible in desktop view")
        
        # Test mobile view
        self.driver.set_window_size(375, 667)  # iPhone size
        time.sleep(1)
        
        # Tables should still be present (may be in responsive containers)
        tables = self.driver.find_elements(By.CSS_SELECTOR, "table.table")
        for table in tables:
            # Table might be in a scrollable container on mobile
            self.assertTrue(table.is_displayed() or 
                          table.find_element(By.XPATH, "./ancestor::div[contains(@class, 'table-responsive')]"),
                          "Table should be visible or in responsive container in mobile view")
        
        # Reset to desktop view
        self.driver.set_window_size(1920, 1080)


def run_tests():
    """Run all tests."""
    # Check if Flask server is running
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code != 200:
            print("Flask server is not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("Flask server is not running on localhost:5000")
        print("Please start the Flask server first with: python app.py")
        return False
    
    # Run the tests
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()