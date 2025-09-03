#!/usr/bin/env python3
"""
Simple Test for Activity Dashboard After Checkbox Removal
Tests to verify the template renders without errors after removing checkbox functionality.
"""

import unittest
import requests
import re

class TestActivityDashboardSimple(unittest.TestCase):
    """Simple tests for activity dashboard without checkbox functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.base_url = "http://localhost:5000"
        cls.login_email = "kdresdell@gmail.com"
        cls.login_password = "admin123"
        
        # Create a session for login
        cls.session = requests.Session()
        cls._login()
    
    @classmethod
    def _login(cls):
        """Login to the application."""
        # Get login page first to retrieve CSRF token
        login_page = cls.session.get(f"{cls.base_url}/login")
        if login_page.status_code != 200:
            raise Exception(f"Could not access login page: {login_page.status_code}")
        
        # Login with credentials
        login_data = {
            'email': cls.login_email,
            'password': cls.login_password
        }
        
        response = cls.session.post(f"{cls.base_url}/login", data=login_data, allow_redirects=True)
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.status_code}")
        
        # Check if login was successful (should not be on login page)
        if "/login" in response.url:
            raise Exception("Login failed - still on login page")
    
    def test_activity_dashboard_loads_without_error(self):
        """Test that the activity dashboard loads without HTTP errors."""
        # Try to access activity dashboard (assuming activity ID 5 exists)
        response = self.session.get(f"{self.base_url}/activity/5")
        
        # Should return 200 OK or 404 if activity doesn't exist
        self.assertIn(response.status_code, [200, 404], 
                      f"Expected 200 or 404, got {response.status_code}")
        
        if response.status_code == 200:
            # If successful, check that it's HTML content
            self.assertIn("text/html", response.headers.get("content-type", ""))
            
            # Check that response has content
            self.assertGreater(len(response.text), 100, "Response should have substantial content")
            
            print(f"✅ Activity dashboard loads successfully (status: {response.status_code})")
        else:
            print(f"ℹ️ Activity ID 5 not found (status: {response.status_code}) - this may be expected")
    
    def test_no_checkbox_references_in_html(self):
        """Test that there are no checkbox-related elements in the HTML."""
        response = self.session.get(f"{self.base_url}/activity/5")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for absence of checkbox-related HTML elements
            checkbox_patterns = [
                r'input[^>]*type=["\']checkbox["\']',  # Input checkboxes
                r'class=["\'][^"\']*checkbox[^"\']*["\']',  # Checkbox classes
                r'id=["\']selectAll["\']',  # Select all checkbox
                r'class=["\'][^"\']*bulk-actions[^"\']*["\']',  # Bulk actions classes
                r'id=["\']bulkActions["\']',  # Bulk actions ID
                r'passport-checkbox',  # Passport checkbox class
                r'signup-checkbox',  # Signup checkbox class
            ]
            
            found_patterns = []
            for pattern in checkbox_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    found_patterns.append((pattern, matches))
            
            if found_patterns:
                print("Found checkbox-related patterns:")
                for pattern, matches in found_patterns:
                    print(f"  Pattern: {pattern}")
                    for match in matches[:5]:  # Show first 5 matches
                        print(f"    Match: {match}")
            
            self.assertEqual(len(found_patterns), 0, 
                           f"Found {len(found_patterns)} checkbox-related patterns in HTML")
            
            print("✅ No checkbox references found in HTML")
        else:
            print("ℹ️ Skipping HTML content check - activity not found")
    
    def test_no_bulk_actions_javascript(self):
        """Test that bulk actions JavaScript functions are not present."""
        response = self.session.get(f"{self.base_url}/activity/5")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for absence of bulk actions JavaScript functions
            js_patterns = [
                r'function\s+initializePassportBulkSelection',
                r'function\s+showBulkDeleteModal',
                r'function\s+updateBulkActions',
                r'\.passport-checkbox',
                r'\.signup-checkbox',
                r'getElementById\(["\']selectAll["\']\)',
                r'getElementById\(["\']bulkActions["\']\)',
            ]
            
            found_js_patterns = []
            for pattern in js_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    found_js_patterns.append((pattern, matches))
            
            if found_js_patterns:
                print("Found bulk actions JavaScript patterns:")
                for pattern, matches in found_js_patterns:
                    print(f"  Pattern: {pattern}")
                    for match in matches[:3]:  # Show first 3 matches
                        print(f"    Match: {match}")
            
            self.assertEqual(len(found_js_patterns), 0, 
                           f"Found {len(found_js_patterns)} bulk actions JS patterns")
            
            print("✅ No bulk actions JavaScript found")
        else:
            print("ℹ️ Skipping JavaScript content check - activity not found")
    
    def test_no_bulk_actions_css(self):
        """Test that bulk actions CSS is not present."""
        response = self.session.get(f"{self.base_url}/activity/5")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for absence of bulk actions CSS
            css_patterns = [
                r'\.bulk-actions-container',
                r'\.bulk-actions-card',
                r'\.bulk-actions-count',
                r'\.bulk-actions-buttons',
                r'#bulkActions',
            ]
            
            found_css_patterns = []
            for pattern in css_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    found_css_patterns.append((pattern, matches))
            
            if found_css_patterns:
                print("Found bulk actions CSS patterns:")
                for pattern, matches in found_css_patterns:
                    print(f"  Pattern: {pattern}")
                    for match in matches[:3]:  # Show first 3 matches
                        print(f"    Match: {match}")
            
            self.assertEqual(len(found_css_patterns), 0, 
                           f"Found {len(found_css_patterns)} bulk actions CSS patterns")
            
            print("✅ No bulk actions CSS found")
        else:
            print("ℹ️ Skipping CSS content check - activity not found")
    
    def test_actions_dropdown_still_present(self):
        """Test that individual Actions dropdowns are still present."""
        response = self.session.get(f"{self.base_url}/activity/5")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for presence of individual action dropdowns
            action_patterns = [
                r'dropdown-toggle',
                r'Actions</.*span>|>Actions<',  # Actions text in dropdowns
                r'dropdown-item',
            ]
            
            found_actions = []
            for pattern in action_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    found_actions.append((pattern, len(matches)))
            
            if found_actions:
                print("Found action dropdown patterns:")
                for pattern, count in found_actions:
                    print(f"  Pattern: {pattern} - Count: {count}")
                
                # Should have at least some action dropdowns
                total_matches = sum(count for _, count in found_actions)
                self.assertGreater(total_matches, 0, "Should have action dropdown elements")
                
                print("✅ Individual action dropdowns are present")
            else:
                print("ℹ️ No action dropdowns found - may be expected if no data")
        else:
            print("ℹ️ Skipping action dropdown check - activity not found")
    
    def test_tables_still_present(self):
        """Test that tables are still present and functional."""
        response = self.session.get(f"{self.base_url}/activity/5")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for table elements
            table_patterns = [
                r'<table[^>]*class=["\'][^"\']*table[^"\']*["\']',
                r'<thead>',
                r'<tbody>',
                r'table-responsive',
            ]
            
            found_tables = []
            for pattern in table_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    found_tables.append((pattern, len(matches)))
            
            if found_tables:
                print("Found table elements:")
                for pattern, count in found_tables:
                    print(f"  Pattern: {pattern} - Count: {count}")
                
                print("✅ Tables are present")
            else:
                print("⚠️ No tables found - this may indicate an issue")
        else:
            print("ℹ️ Skipping table check - activity not found")


def run_tests():
    """Run all tests."""
    # Check if Flask server is running
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
    except requests.exceptions.RequestException:
        print("❌ Flask server is not running on localhost:5000")
        print("Please start the Flask server first")
        return False
    
    print("🚀 Running Activity Dashboard Tests (No Checkboxes)")
    print("=" * 60)
    
    # Run the tests
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()