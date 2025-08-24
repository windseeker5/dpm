#!/usr/bin/env python3
"""
Integration verification script for SSE notifications
This script checks that all components are properly integrated
"""

import requests
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

BASE_URL = "http://127.0.0.1:8890"

def check_server_running():
    """Check if the Flask server is running"""
    print("🔍 Checking if Flask server is running...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code in [200, 302]:
            print("✅ Flask server is running")
            return True
        else:
            print(f"⚠️ Flask server responded with status {response.status_code}")
            return True  # Server is running, just different response
    except requests.exceptions.RequestException as e:
        print(f"❌ Flask server not accessible: {e}")
        return False

def check_gravatar_function():
    """Check if gravatar function works"""
    print("🔍 Checking Gravatar function...")
    try:
        from utils import get_gravatar_url
        
        test_url = get_gravatar_url("test@example.com")
        expected_start = "https://www.gravatar.com/avatar/"
        
        if test_url.startswith(expected_start):
            print("✅ Gravatar function working correctly")
            return True
        else:
            print(f"❌ Gravatar function returned unexpected URL: {test_url}")
            return False
    except Exception as e:
        print(f"❌ Gravatar function error: {e}")
        return False

def check_api_endpoints():
    """Check if API endpoints are accessible"""
    print("🔍 Checking API endpoints...")
    
    endpoints = [
        "/api/notifications/health",
        "/api/event-stream"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            url = BASE_URL + endpoint
            response = requests.get(url, timeout=5)
            
            # We expect 401 Unauthorized for these endpoints without admin login
            if response.status_code == 401:
                print(f"✅ {endpoint} - Properly protected (401 Unauthorized)")
                results.append(True)
            elif response.status_code == 200:
                print(f"✅ {endpoint} - Accessible")
                results.append(True)
            else:
                print(f"⚠️ {endpoint} - Status {response.status_code}")
                results.append(False)
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Error: {e}")
            results.append(False)
    
    return all(results)

def check_imports():
    """Check if all imports work correctly"""
    print("🔍 Checking module imports...")
    
    try:
        from api.notifications import notifications_bp, emit_payment_notification, emit_signup_notification
        print("✅ Notifications module imports working")
        
        from utils import get_gravatar_url
        print("✅ Utils module imports working")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def check_flask_app_context():
    """Check if Flask app context is available"""
    print("🔍 Checking Flask app context...")
    
    try:
        import sys
        import os
        
        # This is a bit tricky - we need to simulate what happens when Flask runs
        from flask import Flask
        app = Flask(__name__)
        
        with app.app_context():
            from utils import get_gravatar_url
            test_url = get_gravatar_url("test@example.com")
            if test_url:
                print("✅ Flask app context working")
                return True
        
        return False
    except Exception as e:
        print(f"❌ Flask app context error: {e}")
        return False

def main():
    """Run all verification checks"""
    print("🚀 SSE Notifications Integration Verification")
    print("=" * 50)
    
    checks = [
        ("Server Running", check_server_running),
        ("Gravatar Function", check_gravatar_function),
        ("API Endpoints", check_api_endpoints),
        ("Module Imports", check_imports),
        ("Flask App Context", check_flask_app_context)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} crashed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{check_name:20} | {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! SSE notification system is properly integrated.")
        print("\n📝 Next steps:")
        print("   1. Login as admin at http://127.0.0.1:8890/login")
        print("   2. Open the test page: http://127.0.0.1:8890/test/html/sse_test.html")
        print("   3. Test with real signups and payments")
    else:
        print("\n⚠️ Some checks failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main()