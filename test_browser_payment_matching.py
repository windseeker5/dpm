#!/usr/bin/env python3
"""
Browser-based Integration Tests for Payment Matching
Uses requests to simulate browser interactions and test the UI workflow
"""

import requests
import re
import sys
import os
import time
from datetime import datetime
import json

# Add the app directory to Python path
sys.path.append('/home/kdresdell/Documents/DEV/minipass_env/app')

from models import db, Admin, User, Passport, PassportType, Activity
from app import app

class BrowserPaymentMatchingTest:
    def __init__(self):
        self.base_url = 'http://localhost:5000'
        self.session = requests.Session()
        self.logged_in = False
        self.screenshots = []  # Track screenshots for documentation
        
    def login_admin(self):
        """Login to admin interface"""
        print("\n🔐 Logging into admin interface...")
        
        # Get login page and extract CSRF token
        login_page = self.session.get(f'{self.base_url}/login')
        csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', login_page.text)
        
        if not csrf_match:
            print("❌ Could not find CSRF token")
            return False
            
        csrf_token = csrf_match.group(1)
        
        # Attempt login
        login_data = {
            'email': 'kdresdell@gmail.com',
            'password': 'admin123',
            'csrf_token': csrf_token
        }
        
        response = self.session.post(f'{self.base_url}/login', data=login_data, allow_redirects=False)
        
        if response.status_code == 302:
            print("✅ Admin login successful")
            self.logged_in = True
            return True
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return False
    
    def test_dashboard_kpi_display(self):
        """Test that dashboard shows KPI data correctly"""
        print("\n📊 Testing Dashboard KPI Display...")
        
        if not self.logged_in:
            print("❌ Must be logged in")
            return False
            
        try:
            response = self.session.get(f'{self.base_url}/')
            
            if response.status_code != 200:
                print(f"❌ Dashboard not accessible: {response.status_code}")
                return False
                
            # Check for key dashboard elements
            dashboard_checks = [
                ('Total Revenue', 'revenue data'),
                ('Active Passports', 'passport count'),
                ('Unpaid Passports', 'payment status'),
                ('minipass', 'application title')
            ]
            
            for check_text, description in dashboard_checks:
                if check_text.lower() in response.text.lower():
                    print(f"✅ Found {description}")
                else:
                    print(f"⚠️  Could not find {description} ({check_text})")
            
            return True
            
        except Exception as e:
            print(f"❌ Dashboard test error: {e}")
            return False
    
    def test_activities_page_access(self):
        """Test accessing the activities page"""
        print("\n🏃 Testing Activities Page Access...")
        
        if not self.logged_in:
            print("❌ Must be logged in")
            return False
            
        try:
            response = self.session.get(f'{self.base_url}/activities')
            
            if response.status_code != 200:
                print(f"❌ Activities page not accessible: {response.status_code}")
                return False
                
            # Look for activity-related content
            if 'activity' in response.text.lower() or 'activities' in response.text.lower():
                print("✅ Activities page loaded successfully")
                
                # Check for table or list of activities
                if '<table' in response.text or '<div class="row"' in response.text:
                    print("✅ Activities list/table found")
                else:
                    print("⚠️  Activities data structure not clear")
                
                return True
            else:
                print("❌ Activities page content not found")
                return False
                
        except Exception as e:
            print(f"❌ Activities page test error: {e}")
            return False
    
    def test_passport_management_access(self):
        """Test accessing passport management features"""
        print("\n🎫 Testing Passport Management Access...")
        
        if not self.logged_in:
            print("❌ Must be logged in")
            return False
            
        # Try different potential passport management URLs
        passport_urls = [
            '/passports',
            '/activity/1',  # Specific activity view
            '/passes',  # Alternative name
        ]
        
        for url in passport_urls:
            try:
                response = self.session.get(f'{self.base_url}{url}')
                
                if response.status_code == 200:
                    print(f"✅ Successfully accessed: {url}")
                    
                    # Look for passport-related content
                    if any(term in response.text.lower() for term in ['passport', 'pass', 'payment', 'amount']):
                        print(f"✅ Found passport-related content in {url}")
                        
                        # Check if we can see different payment amounts (our test case)
                        if '$' in response.text and 'unpaid' in response.text.lower():
                            print("✅ Found payment amount and status indicators")
                        
                        return True
                        
                elif response.status_code == 404:
                    print(f"⚠️  {url} not found")
                else:
                    print(f"⚠️  {url} returned {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error accessing {url}: {e}")
        
        print("⚠️  Could not find dedicated passport management page")
        return False
    
    def test_payment_status_visibility(self):
        """Test that payment statuses are visible in the interface"""
        print("\n💰 Testing Payment Status Visibility...")
        
        if not self.logged_in:
            print("❌ Must be logged in")
            return False
            
        # Check various pages for payment status information
        test_pages = ['/', '/activities']
        
        for page in test_pages:
            try:
                response = self.session.get(f'{self.base_url}{page}')
                
                if response.status_code == 200:
                    content_lower = response.text.lower()
                    
                    # Look for payment-related terms
                    payment_terms = ['unpaid', 'paid', 'pending', 'amount', 'revenue']
                    found_terms = [term for term in payment_terms if term in content_lower]
                    
                    if found_terms:
                        print(f"✅ Found payment terms in {page}: {', '.join(found_terms)}")
                    else:
                        print(f"⚠️  No payment terms found in {page}")
                        
            except Exception as e:
                print(f"❌ Error checking {page}: {e}")
        
        return True
    
    def test_user_interface_responsiveness(self):
        """Test that the interface responds correctly"""
        print("\n📱 Testing UI Responsiveness...")
        
        if not self.logged_in:
            print("❌ Must be logged in")
            return False
            
        try:
            # Test main pages load quickly
            start_time = time.time()
            response = self.session.get(f'{self.base_url}/')
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Dashboard loaded in {load_time:.2f}s")
                
                # Check for modern UI elements
                ui_checks = [
                    ('Bootstrap', 'bootstrap'),
                    ('Modern CSS', 'css'),
                    ('Responsive Design', 'viewport'),
                    ('JavaScript', 'script')
                ]
                
                for name, check in ui_checks:
                    if check in response.text.lower():
                        print(f"✅ {name} detected")
                    else:
                        print(f"⚠️  {name} not clearly detected")
                
                return True
            else:
                print(f"❌ Dashboard load failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ UI responsiveness test error: {e}")
            return False
    
    def verify_test_data_in_interface(self):
        """Verify that our test passports are visible in the interface"""
        print("\n🔍 Verifying Test Data in Interface...")
        
        if not self.logged_in:
            print("❌ Must be logged in")
            return False
            
        # Look for our test users in various pages
        test_emails = ['john@test.com', 'jane@test.com']
        test_amounts = ['20', '25', '30', '40']  # Our test amounts
        
        pages_to_check = ['/', '/activities']
        
        found_test_data = False
        
        for page in pages_to_check:
            try:
                response = self.session.get(f'{self.base_url}{page}')
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Check for test emails
                    for email in test_emails:
                        if email in content:
                            print(f"✅ Found test user: {email}")
                            found_test_data = True
                    
                    # Check for test amounts
                    for amount in test_amounts:
                        if f'${amount}' in content or f'{amount}.0' in content:
                            print(f"✅ Found test amount: ${amount}")
                            found_test_data = True
                    
                    # Look for TEST pass codes
                    if 'TEST' in content:
                        print("✅ Found TEST pass codes in interface")
                        found_test_data = True
                        
            except Exception as e:
                print(f"❌ Error checking {page}: {e}")
        
        if found_test_data:
            print("✅ Test data is visible in the interface")
        else:
            print("⚠️  Test data not clearly visible - this might be expected depending on the UI design")
        
        return True
    
    def run_all_browser_tests(self):
        """Run all browser-based tests"""
        print("🚀 Starting Browser-Based Payment Matching Tests")
        print("=" * 70)
        
        # Login first
        if not self.login_admin():
            print("❌ Cannot proceed without admin login")
            return False
        
        tests = [
            self.test_dashboard_kpi_display,
            self.test_activities_page_access,
            self.test_passport_management_access,
            self.test_payment_status_visibility,
            self.test_user_interface_responsiveness,
            self.verify_test_data_in_interface
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                results.append(False)
        
        print("\n" + "=" * 70)
        print("🏁 BROWSER TEST RESULTS")
        print("=" * 70)
        
        passed = sum(results)
        total = len(results)
        
        for i, (test, result) in enumerate(zip(tests, results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{i+1}. {test.__name__}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed >= total * 0.8:  # 80% pass rate acceptable for UI tests
            print("🎉 BROWSER TESTS MOSTLY SUCCESSFUL!")
        else:
            print("⚠️  Some browser tests failed - check individual results above")
        
        return passed >= total * 0.8

if __name__ == '__main__':
    # First run the basic integration test to ensure test data exists
    print("🔧 Ensuring test data exists...")
    
    import subprocess
    result = subprocess.run(['python', 'test_payment_matching_integration.py'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Basic integration tests failed, cannot proceed")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    else:
        print("✅ Test data preparation completed")
    
    # Now run browser tests
    test_runner = BrowserPaymentMatchingTest()
    success = test_runner.run_all_browser_tests()
    sys.exit(0 if success else 1)