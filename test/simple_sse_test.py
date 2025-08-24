#!/usr/bin/env python3
"""
Simple SSE Verification Test
Tests core SSE functionality without complex dependencies
"""

import sys
import os
import requests
import json
import threading
import time
from datetime import datetime, timezone

def test_sse_basic_functionality():
    """Test basic SSE functionality"""
    base_url = "http://127.0.0.1:8890"
    
    print("🚀 Basic SSE Functionality Test")
    print("=" * 40)
    
    # Test 1: Check if server is running
    print("\n🔍 Testing if Flask server is running...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is running")
        else:
            print(f"⚠️ Flask server returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Flask server is not accessible: {e}")
        return False
    
    # Test 2: Test SSE endpoint accessibility (without auth)
    print("\n🔍 Testing SSE endpoint accessibility...")
    try:
        response = requests.get(f"{base_url}/api/event-stream", timeout=3)
        if response.status_code == 401:
            print("✅ SSE endpoint properly protected (returns 401)")
        elif response.status_code == 200:
            print("⚠️ SSE endpoint accessible without auth")
        else:
            print(f"⚠️ SSE endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ SSE endpoint error: {e}")
    
    # Test 3: Test health endpoint
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/notifications/health", timeout=5)
        if response.status_code == 401:
            print("✅ Health endpoint properly protected (returns 401)")
        else:
            print(f"⚠️ Health endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    return True

def test_route_registration():
    """Test if notification routes are registered"""
    print("\n🔍 Testing route registration with route listing...")
    
    # Add the app directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    try:
        from app import app
        
        with app.app_context():
            notification_routes = []
            for rule in app.url_map.iter_rules():
                if any(keyword in rule.rule for keyword in ['notifications', 'event-stream']):
                    notification_routes.append(f"{rule.rule} -> {rule.endpoint}")
            
            if notification_routes:
                print("✅ Notification routes registered:")
                for route in notification_routes:
                    print(f"   {route}")
                return True
            else:
                print("❌ No notification routes found")
                return False
                
    except Exception as e:
        print(f"❌ Failed to load app and check routes: {e}")
        return False

def test_notification_functions():
    """Test notification functions directly"""
    print("\n🔍 Testing notification functions...")
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    try:
        from api.notifications import notification_manager, emit_payment_notification, emit_signup_notification
        
        # Test notification manager
        test_notification = {
            'type': 'test',
            'message': 'Direct function test',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Test adding notification
        notification_manager.add_notification("test@admin.com", test_notification)
        notifications = notification_manager.get_notifications("test@admin.com")
        
        if notifications and len(notifications) > 0:
            print("✅ Notification manager working correctly")
            print(f"   Retrieved notification: {notifications[0]['type']}")
        else:
            print("❌ Notification manager not working")
            return False
        
        # Test broadcasting
        notification_manager.broadcast_to_admins({
            'type': 'broadcast_test',
            'message': 'Broadcast test',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        print("✅ Broadcast function executed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Notification functions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Simple SSE Verification Test")
    print("=" * 50)
    
    results = []
    
    # Test basic functionality
    results.append(("Basic Functionality", test_sse_basic_functionality()))
    
    # Test route registration
    results.append(("Route Registration", test_route_registration()))
    
    # Test notification functions
    results.append(("Notification Functions", test_notification_functions()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic SSE tests passed!")
    else:
        print("⚠️ Some tests failed.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)