#!/usr/bin/env python3
"""
Simple test script for notification endpoints without BeautifulSoup
"""
import requests
import json

def test_endpoints():
    """Test the notification endpoints with proper session"""
    session = requests.Session()
    
    print("🔍 Testing notification endpoints...")
    
    # Step 1: Try to login (skip CSRF for now)
    print("\n1. Attempting login...")
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123'
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
        
        if 'dashboard' in location:
            print("   ✅ Login successful!")
        else:
            print("   ❌ Login may have failed - check CSRF requirement")
            # Still try the endpoints
    
    # Step 2: Test payment notification endpoint
    print("\n2. Testing payment notification endpoint...")
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
        # Show a preview of the HTML
        html = payment_response.text
        print(f"   HTML preview (first 200 chars): {html[:200]}")
        
        # Basic checks
        checks = [
            ('Contains John Doe', 'John Doe' in html),
            ('Contains Mountain Biking', 'Mountain Biking' in html),
            ('Contains amount', '175' in html),
            ('Contains payment icon', 'ti-credit-card' in html),
            ('Contains event-notification', 'event-notification' in html)
        ]
        
        for check_name, result in checks:
            print(f"   {check_name}: {'✅' if result else '❌'}")
            
    else:
        print(f"   ❌ Payment endpoint response: {payment_response.text}")
    
    # Step 3: Test signup notification endpoint
    print("\n3. Testing signup notification endpoint...")
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
        # Show a preview of the HTML
        html = signup_response.text
        print(f"   HTML preview (first 200 chars): {html[:200]}")
        
        # Basic checks
        checks = [
            ('Contains Jane Smith', 'Jane Smith' in html),
            ('Contains Rock Climbing', 'Rock Climbing' in html),
            ('Contains Standard Pass', 'Standard Pass' in html),
            ('Contains signup icon', 'ti-user-plus' in html),
            ('Contains event-notification', 'event-notification' in html)
        ]
        
        for check_name, result in checks:
            print(f"   {check_name}: {'✅' if result else '❌'}")
            
    else:
        print(f"   ❌ Signup endpoint response: {signup_response.text}")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    test_endpoints()