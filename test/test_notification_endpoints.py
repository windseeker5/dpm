#!/usr/bin/env python3
"""
Test script for notification HTML endpoints
"""
import requests
import json

def test_notification_endpoints():
    """Test the notification HTML endpoints"""
    base_url = "http://127.0.0.1:8890"
    
    # First login to get session
    session = requests.Session()
    
    # Get login page to extract CSRF token
    login_page = session.get(f"{base_url}/login")
    
    # Simple login without CSRF for testing (if the app allows)
    # Try to login
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123'
    }
    
    try:
        # Try a simple POST first
        login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        print(f"Login response status: {login_response.status_code}")
        print(f"Login response headers: {dict(login_response.headers)}")
        
        if 'Set-Cookie' in login_response.headers:
            print("Session cookie set")
        
        # Test payment notification endpoint
        payment_data = {
            "type": "payment",
            "id": "payment_123_1640995200",
            "timestamp": "2024-01-24T10:00:00Z",
            "data": {
                "user_name": "John Doe",
                "email": "john@example.com", 
                "avatar": "https://www.gravatar.com/avatar/placeholder",
                "amount": 175.00,
                "activity": "Mountain Biking",
                "activity_id": 1,
                "paid_date": "2024-01-24T10:00:00Z"
            }
        }
        
        response = session.post(
            f"{base_url}/api/payment-notification-html/test123",
            json=payment_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nPayment notification endpoint:")
        print(f"Status: {response.status_code}")
        print(f"Response length: {len(response.text)}")
        print(f"Response type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            print("✅ Payment notification endpoint working!")
            print(f"HTML preview (first 200 chars): {response.text[:200]}")
        else:
            print(f"❌ Payment notification endpoint failed: {response.text}")
        
        # Test signup notification endpoint
        signup_data = {
            "type": "signup",
            "id": "signup_456_1640995300", 
            "timestamp": "2024-01-24T10:05:00Z",
            "data": {
                "user_name": "Jane Smith",
                "email": "jane@example.com",
                "avatar": "https://www.gravatar.com/avatar/placeholder2",
                "activity": "Rock Climbing",
                "activity_id": 2,
                "passport_type": "Standard Pass",
                "passport_type_price": 50.00,
                "phone": "+1234567890"
            }
        }
        
        response = session.post(
            f"{base_url}/api/signup-notification-html/test456", 
            json=signup_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nSignup notification endpoint:")
        print(f"Status: {response.status_code}")
        print(f"Response length: {len(response.text)}")
        print(f"Response type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            print("✅ Signup notification endpoint working!")
            print(f"HTML preview (first 200 chars): {response.text[:200]}")
        else:
            print(f"❌ Signup notification endpoint failed: {response.text}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    test_notification_endpoints()