#!/usr/bin/env python3
"""
Test endpoints with proper login and CSRF handling
"""
import requests
import re
import json

def test_with_proper_login():
    """Test endpoints with proper CSRF and admin session"""
    session = requests.Session()
    
    print("🔍 Testing notification endpoints with proper login...")
    
    # Step 1: Get login page and extract CSRF token
    print("\n1. Getting login page and CSRF token...")
    login_page = session.get("http://127.0.0.1:8890/login")
    print(f"   Login page status: {login_page.status_code}")
    
    # Extract CSRF token from the page source
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', login_page.text)
    
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"   CSRF token found: {csrf_token[:20]}...")
    else:
        print("   ❌ No CSRF token found in login page")
        # Try to find it with different patterns
        csrf_match2 = re.search(r'csrf_token["\']?:\s*["\']([^"\']*)["\']', login_page.text)
        if csrf_match2:
            csrf_token = csrf_match2.group(1)
            print(f"   CSRF token found (alt pattern): {csrf_token[:20]}...")
        else:
            print("   ❌ Could not extract CSRF token - checking page content...")
            print(f"   Page content preview: {login_page.text[:500]}")
            return
    
    # Step 2: Login with CSRF token
    print("\n2. Attempting login with CSRF token...")
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    
    login_response = session.post(
        "http://127.0.0.1:8890/login", 
        data=login_data,
        allow_redirects=False
    )
    
    print(f"   Login response status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        location = login_response.headers.get('Location', '')
        print(f"   Redirected to: {location}")
        
        if 'dashboard' in location or location.endswith('/'):
            print("   ✅ Login successful!")
            login_success = True
        else:
            print("   ❌ Login may have failed - unexpected redirect")
            login_success = False
    else:
        print(f"   ❌ Login failed with status {login_response.status_code}")
        print(f"   Response: {login_response.text[:200]}")
        login_success = False
    
    if not login_success:
        print("   Attempting to continue with tests anyway...")
    
    # Step 3: Test payment notification endpoint
    print("\n3. Testing payment notification endpoint...")
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
        html = payment_response.text
        
        # Save a sample of the HTML for inspection
        with open('/tmp/payment_notification_sample.html', 'w') as f:
            f.write(html)
        print("   📄 Sample HTML saved to /tmp/payment_notification_sample.html")
        
        # Basic content checks
        checks = [
            ('Contains John Doe', 'John Doe' in html),
            ('Contains Mountain Biking', 'Mountain Biking' in html),
            ('Contains amount 175.00', '175.00' in html),
            ('Contains payment icon', 'ti-credit-card' in html),
            ('Contains event-notification class', 'event-notification' in html),
            ('Contains notification-payment class', 'notification-payment' in html),
        ]
        
        for check_name, result in checks:
            print(f"   {check_name}: {'✅' if result else '❌'}")
    else:
        print(f"   ❌ Payment endpoint failed: {payment_response.text}")
    
    # Step 4: Test signup notification endpoint
    print("\n4. Testing signup notification endpoint...")
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
        html = signup_response.text
        
        # Save a sample of the HTML for inspection  
        with open('/tmp/signup_notification_sample.html', 'w') as f:
            f.write(html)
        print("   📄 Sample HTML saved to /tmp/signup_notification_sample.html")
        
        # Basic content checks
        checks = [
            ('Contains Jane Smith', 'Jane Smith' in html),
            ('Contains Rock Climbing', 'Rock Climbing' in html),
            ('Contains Standard Pass', 'Standard Pass' in html),
            ('Contains signup icon', 'ti-user-plus' in html),
            ('Contains event-notification class', 'event-notification' in html),
            ('Contains notification-signup class', 'notification-signup' in html),
        ]
        
        for check_name, result in checks:
            print(f"   {check_name}: {'✅' if result else '❌'}")
    else:
        print(f"   ❌ Signup endpoint failed: {signup_response.text}")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    test_with_proper_login()