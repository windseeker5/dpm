#!/usr/bin/env python3
"""
Quick SSE Integration Check

Tests the most critical parts of the SSE implementation
"""

import requests
import json
import sys
import os

def quick_sse_integration_check():
    """Perform quick checks on SSE integration"""
    
    print("🚀 Quick SSE Integration Check")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:8890"
    results = {}
    
    # Test 1: Check if Flask server is running
    print("\n1️⃣ Testing Flask server...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is running")
            results['server'] = True
        else:
            print(f"⚠️ Flask server returned {response.status_code}")
            results['server'] = False
    except Exception as e:
        print(f"❌ Flask server not accessible: {e}")
        results['server'] = False
        return results
    
    # Test 2: Test SSE endpoint protection
    print("\n2️⃣ Testing SSE endpoint protection...")
    try:
        response = requests.get(f"{base_url}/api/event-stream", timeout=5)
        if response.status_code == 401:
            print("✅ SSE endpoint properly protected")
            results['sse_protection'] = True
        else:
            print(f"⚠️ SSE endpoint returned {response.status_code}")
            results['sse_protection'] = False
    except Exception as e:
        print(f"❌ SSE endpoint error: {e}")
        results['sse_protection'] = False
    
    # Test 3: Test health endpoint protection
    print("\n3️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/notifications/health", timeout=5)
        if response.status_code == 401:
            print("✅ Health endpoint properly protected")
            results['health_protection'] = True
        else:
            print(f"⚠️ Health endpoint returned {response.status_code}")
            results['health_protection'] = False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        results['health_protection'] = False
    
    # Test 4: Check route registration programmatically
    print("\n4️⃣ Checking route registration...")
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    try:
        from app import app
        with app.app_context():
            notification_routes = []
            for rule in app.url_map.iter_rules():
                if any(keyword in rule.rule for keyword in ['notifications', 'event-stream']):
                    notification_routes.append(rule.rule)
            
            if len(notification_routes) >= 3:  # event-stream, health, test
                print(f"✅ Found {len(notification_routes)} notification routes")
                results['routes'] = True
            else:
                print(f"⚠️ Only found {len(notification_routes)} notification routes")
                results['routes'] = False
                
        # Test 5: Check notification functions
        print("\n5️⃣ Testing notification functions...")
        from api.notifications import notification_manager, emit_payment_notification, emit_signup_notification
        
        # Test broadcast function
        test_notification = {
            'type': 'integration_test',
            'message': 'Testing integration',
            'timestamp': '2024-01-01T00:00:00Z'
        }
        
        notification_manager.broadcast_to_admins(test_notification)
        print("✅ Notification functions are importable and executable")
        results['functions'] = True
        
    except Exception as e:
        print(f"❌ Route/function check failed: {e}")
        import traceback
        traceback.print_exc()
        results['routes'] = False
        results['functions'] = False
    
    return results

def check_integration_in_app():
    """Check if emit functions are properly integrated in app.py"""
    print("\n6️⃣ Checking app.py integration...")
    
    app_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.py')
    
    if not os.path.exists(app_py_path):
        print("❌ app.py not found")
        return False
    
    with open(app_py_path, 'r') as f:
        content = f.read()
    
    # Check for emit function calls
    emit_payment_count = content.count('emit_payment_notification')
    emit_signup_count = content.count('emit_signup_notification')
    
    print(f"📊 Found {emit_payment_count} emit_payment_notification calls")
    print(f"📊 Found {emit_signup_count} emit_signup_notification calls")
    
    if emit_payment_count >= 2 and emit_signup_count >= 2:  # Individual + bulk operations
        print("✅ Emit functions properly integrated")
        return True
    else:
        print("⚠️ Emit functions may need more integration points")
        return False

def main():
    """Main check function"""
    
    # Run basic checks
    results = quick_sse_integration_check()
    
    # Check app.py integration
    results['app_integration'] = check_integration_in_app()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 QUICK CHECK RESULTS")
    print("=" * 40)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 SSE integration looks good!")
        print("\n📋 Ready for testing:")
        print("1. Login to admin panel")
        print("2. Visit /test-notifications to see live notifications")
        print("3. Process payments to trigger payment notifications")
        print("4. Process signups to trigger signup notifications")
    else:
        print("⚠️ SSE integration needs attention")
        
        if not results.get('server'):
            print("🔧 Fix: Ensure Flask server is running on port 8890")
        if not results.get('routes') or not results.get('functions'):
            print("🔧 Fix: Check notifications blueprint registration")
        if not results.get('app_integration'):
            print("🔧 Fix: Add more emit function calls in payment/signup processing")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)