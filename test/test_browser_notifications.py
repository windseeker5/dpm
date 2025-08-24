#!/usr/bin/env python3
"""
Simple browser test for event notifications
Tests login and basic functionality without Playwright
"""

import requests
import time
import json
import re

# Test configuration
BASE_URL = "http://127.0.0.1:8890"
LOGIN_EMAIL = "kdresdell@gmail.com"
LOGIN_PASSWORD = "admin123"

def test_login():
    """Test login and session creation"""
    session = requests.Session()
    
    # Get login page first
    response = session.get(f"{BASE_URL}/login")
    print(f"Login page status: {response.status_code}")
    
    # Extract CSRF token from the response
    csrf_token = None
    if response.status_code == 200:
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"CSRF token extracted: {csrf_token[:20]}...")
        else:
            print("⚠️ CSRF token not found")
    
    # Attempt login
    login_data = {
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD
    }
    
    if csrf_token:
        login_data["csrf_token"] = csrf_token
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    print(f"Login POST status: {response.status_code}")
    
    # Check if redirected to dashboard (successful login)
    if response.status_code == 200 and "/dashboard" in response.url:
        print("✅ Login successful")
        return session
    elif response.status_code == 302:
        # Follow redirect
        response = session.get(response.headers.get('Location', f"{BASE_URL}/dashboard"))
        print(f"Dashboard access status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Login successful (with redirect)")
            return session
    
    print("❌ Login failed")
    return None

def test_notifications_api(session):
    """Test notifications API endpoints"""
    if not session:
        print("❌ No valid session for API testing")
        return
    
    # Test health endpoint
    response = session.get(f"{BASE_URL}/api/notifications/health")
    print(f"Notifications health endpoint: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Notifications API healthy: {data}")
    else:
        print("❌ Notifications API not accessible")
        return
    
    # Test notification HTML rendering endpoints
    test_notification = {
        "type": "payment",
        "id": "test_payment_123",
        "timestamp": "2025-08-24T12:00:00Z",
        "data": {
            "passport_id": 123,
            "user_name": "Test User",
            "email": "test@example.com",
            "amount": 50.0,
            "activity": "Test Activity",
            "activity_id": 456,
            "avatar": "https://www.gravatar.com/avatar/test?d=identicon",
            "paid_date": "2025-08-24T12:00:00Z"
        }
    }
    
    # Test payment notification HTML endpoint
    response = session.post(
        f"{BASE_URL}/api/payment-notification-html/test_payment_123",
        json=test_notification
    )
    print(f"Payment notification HTML endpoint: {response.status_code}")
    
    if response.status_code == 200:
        html_content = response.text
        if "event-notification" in html_content and "Payment Received" in html_content:
            print("✅ Payment notification HTML rendered correctly")
        else:
            print("❌ Payment notification HTML content invalid")
            print(f"Content preview: {html_content[:200]}...")
    else:
        print(f"❌ Payment notification HTML endpoint failed: {response.text}")
    
    # Test signup notification HTML endpoint
    test_notification["type"] = "signup"
    test_notification["id"] = "test_signup_456"
    test_notification["data"].update({
        "signup_id": 789,
        "phone": "+1 (555) 123-4567",
        "passport_type": "Premium",
        "passport_type_price": 75.0
    })
    
    response = session.post(
        f"{BASE_URL}/api/signup-notification-html/test_signup_456",
        json=test_notification
    )
    print(f"Signup notification HTML endpoint: {response.status_code}")
    
    if response.status_code == 200:
        html_content = response.text
        if "event-notification" in html_content and "New Registration" in html_content:
            print("✅ Signup notification HTML rendered correctly")
        else:
            print("❌ Signup notification HTML content invalid")
            print(f"Content preview: {html_content[:200]}...")
    else:
        print(f"❌ Signup notification HTML endpoint failed: {response.text}")

def test_static_assets(session):
    """Test that CSS and JS assets are accessible"""
    assets_to_test = [
        "/static/css/event-notifications.css",
        "/static/js/event-notifications.js"
    ]
    
    for asset in assets_to_test:
        response = session.get(f"{BASE_URL}{asset}")
        if response.status_code == 200:
            print(f"✅ Asset accessible: {asset}")
        else:
            print(f"❌ Asset not accessible: {asset} (status: {response.status_code})")

def test_dashboard_includes_assets():
    """Test that dashboard page includes our CSS/JS files"""
    session = test_login()
    if not session:
        return
    
    response = session.get(f"{BASE_URL}/dashboard")
    if response.status_code == 200:
        content = response.text
        
        # Check for CSS inclusion
        if "event-notifications.css" in content:
            print("✅ Event notifications CSS included in dashboard")
        else:
            print("❌ Event notifications CSS not included in dashboard")
        
        # Check for JS inclusion
        if "event-notifications.js" in content:
            print("✅ Event notifications JS included in dashboard")
        else:
            print("❌ Event notifications JS not included in dashboard")
        
        # Check for admin user data attribute
        if 'data-admin-user="true"' in content:
            print("✅ Admin user data attribute present")
        else:
            print("❌ Admin user data attribute missing")
    else:
        print(f"❌ Dashboard not accessible: {response.status_code}")

def main():
    print("🧪 Testing Event Notifications System")
    print("=" * 50)
    
    # Test 1: Login
    print("\n1. Testing Login...")
    session = test_login()
    
    # Test 2: Static Assets
    print("\n2. Testing Static Assets...")
    test_static_assets(session or requests.Session())
    
    # Test 3: Notifications API
    print("\n3. Testing Notifications API...")
    test_notifications_api(session)
    
    # Test 4: Dashboard Integration
    print("\n4. Testing Dashboard Integration...")
    test_dashboard_includes_assets()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main()