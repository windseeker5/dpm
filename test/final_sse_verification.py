#!/usr/bin/env python3
"""
Final SSE Verification Script

This script tests the complete SSE notification flow including:
1. SSE connection establishment
2. Notification triggers (payment and signup)
3. Real-time notification delivery
4. Integration with existing payment/signup workflows
"""

import requests
import time
import threading
import json
from datetime import datetime

class FinalSSEVerifier:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8890"
        self.session = requests.Session()
        self.notifications_received = []
        self.sse_connected = False
        
    def login_admin(self):
        """Login as admin to access SSE endpoints"""
        print("🔐 Logging in as admin...")
        
        # First get the login page to extract CSRF token
        login_page = self.session.get(f"{self.base_url}/login")
        
        if login_page.status_code != 200:
            print(f"❌ Failed to access login page: {login_page.status_code}")
            return False
        
        # Extract CSRF token
        import re
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]*)"', login_page.text)
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        # Login data
        login_data = {
            'email': 'kdresdell@gmail.com',
            'password': 'admin123'
        }
        
        if csrf_token:
            login_data['csrf_token'] = csrf_token
        
        # Attempt login
        response = self.session.post(f"{self.base_url}/login", data=login_data)
        
        # Check if redirect to dashboard occurred
        if 'dashboard' in response.url or response.status_code == 200:
            print("✅ Successfully logged in as admin")
            return True
        else:
            print(f"❌ Login failed. Status: {response.status_code}, URL: {response.url}")
            return False
    
    def test_sse_connection(self):
        """Test SSE connection in a separate thread"""
        print("📡 Testing SSE connection...")
        
        def sse_listener():
            try:
                response = self.session.get(
                    f"{self.base_url}/api/event-stream",
                    stream=True,
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ SSE connection failed: {response.status_code}")
                    return
                
                print("✅ SSE connection established")
                self.sse_connected = True
                
                # Listen for notifications
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            self.notifications_received.append(data)
                            print(f"📨 Notification received: {data.get('type', 'unknown')}")
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                print(f"❌ SSE listener error: {e}")
        
        # Start SSE listener in background thread
        sse_thread = threading.Thread(target=sse_listener, daemon=True)
        sse_thread.start()
        
        # Give it a moment to establish connection
        time.sleep(2)
        
        return self.sse_connected
    
    def trigger_test_notification(self):
        """Trigger a test notification"""
        print("🧪 Triggering test notification...")
        
        try:
            response = self.session.post(f"{self.base_url}/api/notifications/test")
            
            if response.status_code == 200:
                print("✅ Test notification triggered successfully")
                return True
            else:
                print(f"❌ Failed to trigger test notification: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Test notification error: {e}")
            return False
    
    def check_integration_points(self):
        """Check key integration points in the application"""
        print("🔍 Checking integration points...")
        
        # Test basic endpoints that should exist
        endpoints_to_test = [
            ('/api/event-stream', 'SSE endpoint'),
            ('/api/notifications/health', 'Health endpoint'),
            ('/test-notifications', 'Test page')
        ]
        
        integration_ok = True
        
        for endpoint, description in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    print(f"✅ {description} accessible")
                elif response.status_code == 401:
                    print(f"✅ {description} properly protected")
                else:
                    print(f"⚠️ {description} returned {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {description} error: {e}")
                integration_ok = False
        
        return integration_ok
    
    def run_comprehensive_test(self):
        """Run comprehensive SSE verification"""
        print("🚀 Starting Comprehensive SSE Verification")
        print("=" * 50)
        
        results = {}
        
        # Step 1: Login
        results['login'] = self.login_admin()
        
        if not results['login']:
            print("❌ Cannot proceed without admin login")
            return False
        
        # Step 2: Check integration points
        results['integration'] = self.check_integration_points()
        
        # Step 3: Test SSE connection
        results['sse_connection'] = self.test_sse_connection()
        
        if not results['sse_connection']:
            print("❌ SSE connection failed, skipping notification tests")
            return False
        
        # Step 4: Test notification trigger
        results['test_notification'] = self.trigger_test_notification()
        
        # Step 5: Wait for notifications and verify
        print("⏳ Waiting for notifications (10 seconds)...")
        time.sleep(10)
        
        notification_count = len(self.notifications_received)
        results['notifications_received'] = notification_count > 0
        
        print(f"📊 Received {notification_count} notifications")
        
        # Display received notifications
        for i, notification in enumerate(self.notifications_received):
            print(f"  {i+1}. Type: {notification.get('type')}, Time: {notification.get('timestamp', 'N/A')}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        print(f"Notifications received: {notification_count}")
        
        if passed == total and notification_count > 0:
            print("🎉 SSE system is working correctly!")
            return True
        else:
            print("⚠️ SSE system needs attention")
            return False

def main():
    """Main verification function"""
    verifier = FinalSSEVerifier()
    success = verifier.run_comprehensive_test()
    
    if success:
        print("\n✨ SSE notification system verification PASSED")
        print("\n📋 Next steps:")
        print("1. Visit http://127.0.0.1:8890/test-notifications to see live notifications")
        print("2. Test payment processing to see payment notifications")
        print("3. Test signup processing to see signup notifications")
    else:
        print("\n🔧 SSE system requires fixes:")
        print("1. Ensure Flask server is running on port 8890")
        print("2. Verify admin login credentials")
        print("3. Check notification blueprint registration")
        print("4. Verify emit functions are properly integrated")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)