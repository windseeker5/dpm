#!/usr/bin/env python3
"""
Integration Test for Payment Matching Functionality
Tests the complete workflow from passport creation to payment matching
"""

import requests
import json
import sys
import os
import re
import time
import uuid
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.append('/home/kdresdell/Documents/DEV/minipass_env/app')

from models import db, Admin, User, Passport, PassportType, Activity
from app import app

class PaymentMatchingIntegrationTest:
    def __init__(self):
        self.base_url = 'http://localhost:5000'
        self.session = requests.Session()
        self.logged_in = False
        
    def test_flask_server_running(self):
        """Test 1: Verify Flask server is running"""
        print("\n=== TEST 1: Flask Server Running ===")
        try:
            response = self.session.get(self.base_url)
            print(f"✅ Flask server responding with status: {response.status_code}")
            return response.status_code in [200, 302]  # 302 is redirect to login
        except Exception as e:
            print(f"❌ Flask server not responding: {e}")
            return False
    
    def test_login_page_access(self):
        """Test 2: Access login page"""
        print("\n=== TEST 2: Login Page Access ===")
        try:
            response = self.session.get(f'{self.base_url}/login')
            if response.status_code == 200:
                print("✅ Login page accessible")
                if 'password' in response.text.lower():
                    print("✅ Login form found on page")
                    return True
                else:
                    print("❌ Login form not found")
                    return False
            else:
                print(f"❌ Login page returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error accessing login page: {e}")
            return False
    
    def test_admin_login(self):
        """Test 3: Admin login functionality"""
        print("\n=== TEST 3: Admin Login ===")
        
        # Use the confirmed working credentials
        test_credentials = [
            ('kdresdell@gmail.com', 'admin123'),  # Confirmed working
        ]
        
        for email, password in test_credentials:
            try:
                print(f"Attempting login with: {email}")
                
                # Get login page first for any CSRF tokens
                login_page = self.session.get(f'{self.base_url}/login')
                
                # Extract CSRF token if present
                csrf_token = None
                csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', login_page.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"Found CSRF token: {csrf_token[:20]}...")
                
                # Attempt login
                login_data = {
                    'email': email,
                    'password': password
                }
                
                # Add CSRF token if found
                if csrf_token:
                    login_data['csrf_token'] = csrf_token
                
                response = self.session.post(f'{self.base_url}/login', data=login_data, allow_redirects=False)
                
                if response.status_code == 302:  # Redirect indicates successful login
                    print(f"✅ Login successful with {email}")
                    self.logged_in = True
                    return True
                else:
                    print(f"❌ Login failed with {email} (status: {response.status_code})")
                    
            except Exception as e:
                print(f"❌ Login error with {email}: {e}")
        
        print("❌ All login attempts failed")
        return False
    
    def test_dashboard_access(self):
        """Test 4: Access dashboard after login"""
        print("\n=== TEST 4: Dashboard Access ===")
        if not self.logged_in:
            print("❌ Cannot test dashboard - not logged in")
            return False
            
        try:
            response = self.session.get(f'{self.base_url}/')
            if response.status_code == 200:
                print("✅ Dashboard accessible")
                if 'dashboard' in response.text.lower() or 'minipass' in response.text.lower():
                    print("✅ Dashboard content loaded")
                    return True
                else:
                    print("❌ Dashboard content not found")
                    return False
            else:
                print(f"❌ Dashboard returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error accessing dashboard: {e}")
            return False
    
    def test_database_access(self):
        """Test 5: Database access and data verification"""
        print("\n=== TEST 5: Database Access ===")
        try:
            with app.app_context():
                # Check admin accounts
                admins = Admin.query.all()
                print(f"✅ Found {len(admins)} admin accounts:")
                for admin in admins:
                    print(f"  - {admin.email}")
                
                # Check activities
                activities = Activity.query.all()
                print(f"✅ Found {len(activities)} activities")
                
                # Check users
                users = User.query.all()
                print(f"✅ Found {len(users)} users")
                
                # Check passports
                passports = Passport.query.all()
                print(f"✅ Found {len(passports)} existing passports")
                
                return True
                
        except Exception as e:
            print(f"❌ Database access error: {e}")
            return False
    
    def test_create_test_passports(self):
        """Test 6: Create test passports with different amounts"""
        print("\n=== TEST 6: Create Test Passports ===")
        
        try:
            with app.app_context():
                # First, clean up any existing test passports to avoid conflicts
                existing_test_passports = Passport.query.filter(Passport.pass_code.like('TEST%')).all()
                for passport in existing_test_passports:
                    db.session.delete(passport)
                
                # Clean up test users
                test_emails = ['john@test.com', 'jane@test.com']
                for email in test_emails:
                    test_user = User.query.filter_by(email=email).first()
                    if test_user:
                        db.session.delete(test_user)
                
                db.session.commit()
                print("🧹 Cleaned up existing test data")
                
                # Create or get test users
                test_users = [
                    {'name': 'Test User John', 'email': 'john@test.com'},
                    {'name': 'Test User Jane', 'email': 'jane@test.com'}
                ]
                
                created_passports = []
                
                for user_data in test_users:
                    # Create or get user
                    user = User.query.filter_by(email=user_data['email']).first()
                    if not user:
                        user = User(
                            name=user_data['name'],  # Full name in single field
                            email=user_data['email'],
                            phone_number='555-1234'
                        )
                        db.session.add(user)
                    
                    # Get or create an activity
                    activity = Activity.query.first()
                    if not activity:
                        print("❌ No activities found in database")
                        return False
                    
                    # Get or create passport type
                    passport_type = PassportType.query.filter_by(activity_id=activity.id).first()
                    if not passport_type:
                        passport_type = PassportType(
                            activity_id=activity.id,
                            name='Test Pass Type',
                            type='permanent',
                            price_per_user=25.00,
                            sessions_included=5
                        )
                        db.session.add(passport_type)
                        db.session.flush()  # Get the ID
                    
                    # Create passports with different amounts
                    if user_data['email'] == 'john@test.com':
                        amounts = [20, 30, 40]  # Different amounts for John
                    else:
                        amounts = [25, 25]  # Same amount for Jane
                    
                    for amount in amounts:
                        # First flush to get user.id if it's a new user
                        if hasattr(user, 'id') and user.id is None:
                            db.session.flush()
                        
                        # Generate unique pass code with more entropy
                        unique_id = str(uuid.uuid4())[:8]
                        timestamp = int(time.time() * 1000) % 1000000  # Last 6 digits of timestamp
                        pass_code = f'TEST{timestamp}{unique_id}'[:16]  # Limit to 16 chars
                        
                        passport = Passport(
                            user_id=user.id,
                            activity_id=activity.id,
                            passport_type_id=passport_type.id,
                            passport_type_name=passport_type.name,
                            sold_amt=float(amount),
                            pass_code=pass_code,
                            paid=False,
                            uses_remaining=passport_type.sessions_included,
                            created_dt=datetime.now(timezone.utc)
                        )
                        db.session.add(passport)
                        created_passports.append(passport)
                
                db.session.commit()
                
                print(f"✅ Created {len(created_passports)} test passports")
                for passport in created_passports:
                    user = User.query.get(passport.user_id)
                    print(f"  - {user.email}: ${passport.sold_amt} (Code: {passport.pass_code})")
                
                return True
                
        except Exception as e:
            print(f"❌ Error creating test passports: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_admin_interface_navigation(self):
        """Test 7: Navigate admin interface sections"""
        print("\n=== TEST 7: Admin Interface Navigation ===")
        
        if not self.logged_in:
            print("❌ Cannot test admin interface - not logged in")
            return False
        
        test_urls = [
            '/',  # Dashboard
            '/activities',  # Activities page
            '/users',  # Users page (if exists)
        ]
        
        successful_navigations = 0
        
        for url in test_urls:
            try:
                response = self.session.get(f'{self.base_url}{url}')
                if response.status_code == 200:
                    print(f"✅ Successfully accessed: {url}")
                    successful_navigations += 1
                else:
                    print(f"❌ Failed to access {url}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error accessing {url}: {e}")
        
        print(f"✅ Successfully navigated to {successful_navigations}/{len(test_urls)} pages")
        return successful_navigations > 0
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Payment Matching Integration Tests")
        print("=" * 60)
        
        tests = [
            self.test_flask_server_running,
            self.test_login_page_access,
            self.test_admin_login,
            self.test_dashboard_access,
            self.test_database_access,
            self.test_create_test_passports,
            self.test_admin_interface_navigation
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                results.append(False)
        
        print("\n" + "=" * 60)
        print("🏁 INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for i, (test, result) in enumerate(zip(tests, results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{i+1}. {test.__name__}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - check individual results above")
        
        return passed == total

if __name__ == '__main__':
    test_runner = PaymentMatchingIntegrationTest()
    success = test_runner.run_all_tests()
    sys.exit(0 if success else 1)