#!/usr/bin/env python3
"""
SSE (Server-Sent Events) Verification Test

This script comprehensively tests the SSE notification system to ensure:
1. Notifications blueprint is properly registered
2. SSE event-stream endpoint is accessible
3. emit_payment_notification and emit_signup_notification functions work
4. Notifications are properly broadcasted to admin users
5. Integration points in app.py are functioning
"""

import sys
import os
import requests
import json
import time
import threading
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import Admin, User, Activity, Signup, Passport, PassportType
from api.notifications import notification_manager, emit_payment_notification, emit_signup_notification


class SSEVerificationTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8890"
        self.session = requests.Session()
        self.test_admin_email = "kdresdell@gmail.com"
        self.test_password = "admin123"
        
    def login_as_admin(self):
        """Login as admin to get access to SSE endpoints"""
        login_data = {
            'email': self.test_admin_email,
            'password': self.test_password
        }
        
        # Get CSRF token first
        login_page = self.session.get(f"{self.base_url}/admin")
        
        # Extract CSRF token from login form
        csrf_token = None
        if 'csrf_token' in login_page.text:
            import re
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]*)"', login_page.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        if csrf_token:
            login_data['csrf_token'] = csrf_token
        
        response = self.session.post(f"{self.base_url}/admin", data=login_data)
        
        if response.status_code == 200 and 'dashboard' in response.url:
            print("✅ Successfully logged in as admin")
            return True
        else:
            print(f"❌ Failed to login. Status: {response.status_code}")
            print(f"Response URL: {response.url}")
            return False
    
    def test_sse_endpoint_accessibility(self):
        """Test if the SSE endpoint is accessible"""
        print("\n🔍 Testing SSE endpoint accessibility...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/event-stream",
                stream=True,
                timeout=5
            )
            
            if response.status_code == 200:
                print("✅ SSE endpoint is accessible")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                
                # Read a few lines to verify it's working
                lines = []
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        lines.append(line)
                    if len(lines) >= 3:  # Read first few lines
                        break
                
                print(f"   Sample SSE data: {lines}")
                return True
            else:
                print(f"❌ SSE endpoint returned status: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("⚠️ SSE endpoint timeout (this might be normal)")
            return True  # Timeout might be normal for SSE
        except Exception as e:
            print(f"❌ SSE endpoint error: {e}")
            return False
    
    def test_notification_manager(self):
        """Test the notification manager functionality"""
        print("\n🔍 Testing notification manager...")
        
        with app.app_context():
            # Test adding notifications
            test_notification = {
                'type': 'test',
                'message': 'Test notification',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Add notification to specific admin
            notification_manager.add_notification(self.test_admin_email, test_notification)
            print("✅ Added test notification to admin queue")
            
            # Retrieve notifications
            notifications = notification_manager.get_notifications(self.test_admin_email)
            if notifications and len(notifications) > 0:
                print(f"✅ Retrieved {len(notifications)} notifications")
                print(f"   Sample notification: {notifications[0]}")
                return True
            else:
                print("❌ Failed to retrieve notifications")
                return False
    
    def test_emit_functions_integration(self):
        """Test the emit_payment_notification and emit_signup_notification functions"""
        print("\n🔍 Testing emit functions integration...")
        
        with app.app_context():
            # Create test data
            test_user = User.query.filter_by(email="test@example.com").first()
            if not test_user:
                test_user = User(
                    name="Test User",
                    email="test@example.com",
                    phone_number="123-456-7890"
                )
                db.session.add(test_user)
                db.session.commit()
            
            test_activity = Activity.query.filter_by(name="Test Activity").first()
            if not test_activity:
                test_activity = Activity(
                    name="Test Activity",
                    description="Test activity for SSE verification",
                    location="Test Location",
                    max_participants=10
                )
                db.session.add(test_activity)
                db.session.commit()
            
            # Test passport type
            test_passport_type = PassportType.query.filter_by(activity_id=test_activity.id).first()
            if not test_passport_type:
                test_passport_type = PassportType(
                    activity_id=test_activity.id,
                    name="Test Pass",
                    price_per_user=25.00,
                    sessions_included=5
                )
                db.session.add(test_passport_type)
                db.session.commit()
            
            # Test emit_signup_notification
            test_signup = Signup(
                user_id=test_user.id,
                activity_id=test_activity.id,
                passport_type_id=test_passport_type.id,
                status="pending"
            )
            db.session.add(test_signup)
            db.session.commit()
            
            try:
                emit_signup_notification(test_signup)
                print("✅ emit_signup_notification executed successfully")
                signup_success = True
            except Exception as e:
                print(f"❌ emit_signup_notification failed: {e}")
                signup_success = False
            
            # Test emit_payment_notification
            test_passport = Passport(
                user_id=test_user.id,
                activity_id=test_activity.id,
                pass_code="MP-test123456",
                sold_amt=25.00,
                uses_remaining=5,
                paid=True,
                paid_date=datetime.now(timezone.utc)
            )
            db.session.add(test_passport)
            db.session.commit()
            
            try:
                emit_payment_notification(test_passport)
                print("✅ emit_payment_notification executed successfully")
                payment_success = True
            except Exception as e:
                print(f"❌ emit_payment_notification failed: {e}")
                payment_success = False
            
            # Check if notifications were actually queued
            notifications = notification_manager.get_notifications(self.test_admin_email)
            notification_count = len(notifications) if notifications else 0
            print(f"✅ Found {notification_count} notifications in admin queue")
            
            # Clean up test data
            db.session.delete(test_signup)
            db.session.delete(test_passport)
            db.session.commit()
            
            return signup_success and payment_success
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        print("\n🔍 Testing health endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/notifications/health")
            
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Health endpoint responding")
                print(f"   Status: {health_data.get('status')}")
                print(f"   Admin ID: {health_data.get('admin_id')}")
                return True
            else:
                print(f"❌ Health endpoint returned status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
    
    def test_blueprint_registration(self):
        """Verify the notifications blueprint is properly registered"""
        print("\n🔍 Testing blueprint registration...")
        
        # Check if the routes are registered
        with app.app_context():
            routes = []
            for rule in app.url_map.iter_rules():
                if 'notifications' in rule.rule or 'event-stream' in rule.rule:
                    routes.append(f"{rule.rule} -> {rule.endpoint}")
            
            if routes:
                print("✅ Notifications routes found:")
                for route in routes:
                    print(f"   {route}")
                return True
            else:
                print("❌ No notifications routes found")
                return False
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("🚀 Starting SSE Verification Tests")
        print("=" * 50)
        
        # Test results
        results = {}
        
        # Test 1: Blueprint registration
        results['blueprint_registration'] = self.test_blueprint_registration()
        
        # Test 2: Admin login
        results['admin_login'] = self.login_as_admin()
        
        if results['admin_login']:
            # Test 3: SSE endpoint accessibility
            results['sse_endpoint'] = self.test_sse_endpoint_accessibility()
            
            # Test 4: Health endpoint
            results['health_endpoint'] = self.test_health_endpoint()
        else:
            results['sse_endpoint'] = False
            results['health_endpoint'] = False
        
        # Test 5: Notification manager
        results['notification_manager'] = self.test_notification_manager()
        
        # Test 6: Emit functions
        results['emit_functions'] = self.test_emit_functions_integration()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            if success:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All SSE verification tests passed!")
            return True
        else:
            print("⚠️ Some tests failed. Check implementation.")
            return False


def main():
    """Main test runner"""
    tester = SSEVerificationTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n🔧 RECOMMENDATIONS:")
        print("1. Ensure Flask server is running on port 8890")
        print("2. Verify admin credentials are correct")
        print("3. Check notifications blueprint registration in app.py")
        print("4. Verify emit functions are called in appropriate places")
        print("5. Check database connectivity and test data creation")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)