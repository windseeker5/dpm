#!/usr/bin/env python3
"""
Manual test script for notification endpoints
"""
import requests
import json
from bs4 import BeautifulSoup

def test_endpoints():
    """Test the notification endpoints with proper session"""
    session = requests.Session()
    
    print("🔍 Testing notification endpoints...")
    
    # Step 1: Get login page to extract CSRF token
    print("\n1. Getting login page...")
    login_page = session.get("http://127.0.0.1:8890/login")
    print(f"   Login page status: {login_page.status_code}")
    
    # Try to extract CSRF token from the form
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = None
    
    # Look for CSRF token in hidden input
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
        print(f"   CSRF token found: {csrf_token[:20]}...")
    else:
        print("   No CSRF token found, trying without...")
    
    # Step 2: Login
    print("\n2. Attempting login...")
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123'
    }
    
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    login_response = session.post(
        "http://127.0.0.1:8890/login", 
        data=login_data,
        allow_redirects=False
    )
    
    print(f"   Login response status: {login_response.status_code}")
    print(f"   Login response headers: {dict(login_response.headers)}")
    
    # Check if redirected to dashboard (successful login)
    if login_response.status_code == 302:
        location = login_response.headers.get('Location', '')
        print(f"   Redirected to: {location}")
        
        if 'dashboard' in location:
            print("   ✅ Login successful!")
        else:
            print("   ❌ Login may have failed - redirected elsewhere")
    
    # Step 3: Test access to test page
    print("\n3. Testing access to test page...")
    test_page_response = session.get("http://127.0.0.1:8890/test/notification-endpoints")
    print(f"   Test page status: {test_page_response.status_code}")
    
    # Step 4: Test payment notification endpoint
    print("\n4. Testing payment notification endpoint...")
    payment_data = {
        "type": "payment",
        "id": "payment_test_123",
        "timestamp": "2024-01-24T10:00:00Z",
        "data": {
            "user_name": "John Doe",
            "email": "john@example.com",
            "avatar": "https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e",
            "amount": 175.00,
            "activity": "Mountain Biking",
            "activity_id": 1,
            "paid_date": "2024-01-24T10:00:00Z"
        }
    }
    
    payment_response = session.post(
        "http://127.0.0.1:8890/api/payment-notification-html/test123",
        json=payment_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"   Payment endpoint status: {payment_response.status_code}")
    print(f"   Payment response length: {len(payment_response.text)}")
    
    if payment_response.status_code == 200:
        print("   ✅ Payment notification endpoint working!")
        # Check if HTML contains expected elements
        html = payment_response.text
        checks = {
            'event-notification': 'event-notification' in html,
            'John Doe': 'John Doe' in html,
            'Mountain Biking': 'Mountain Biking' in html,
            '$175.00': '$175.00' in html or '175.00' in html,
            'ti-credit-card': 'ti-credit-card' in html
        }
        
        print("   HTML content checks:")
        for check, result in checks.items():
            print(f"     - {check}: {'✅' if result else '❌'}")
            
    else:
        print(f"   ❌ Payment endpoint failed: {payment_response.text}")
    
    # Step 5: Test signup notification endpoint
    print("\n5. Testing signup notification endpoint...")
    signup_data = {
        "type": "signup",
        "id": "signup_test_456",
        "timestamp": "2024-01-24T10:05:00Z",
        "data": {
            "user_name": "Jane Smith",
            "email": "jane@example.com",
            "avatar": "https://www.gravatar.com/avatar/25f9e794323b453885f5181f1b624d0b",
            "activity": "Rock Climbing",
            "activity_id": 2,
            "passport_type": "Standard Pass",
            "passport_type_price": 50.00,
            "phone": "+1234567890"
        }
    }
    
    signup_response = session.post(
        "http://127.0.0.1:8890/api/signup-notification-html/test456",
        json=signup_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"   Signup endpoint status: {signup_response.status_code}")
    print(f"   Signup response length: {len(signup_response.text)}")
    
    if signup_response.status_code == 200:
        print("   ✅ Signup notification endpoint working!")
        # Check if HTML contains expected elements
        html = signup_response.text
        checks = {
            'event-notification': 'event-notification' in html,
            'Jane Smith': 'Jane Smith' in html,
            'Rock Climbing': 'Rock Climbing' in html,
            'Standard Pass': 'Standard Pass' in html,
            'ti-user-plus': 'ti-user-plus' in html
        }
        
        print("   HTML content checks:")
        for check, result in checks.items():
            print(f"     - {check}: {'✅' if result else '❌'}")
            
    else:
        print(f"   ❌ Signup endpoint failed: {signup_response.text}")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    test_endpoints()