#!/usr/bin/env python3
"""
Final integration test for notification endpoints
"""
import requests
import re

def test_integration():
    """Complete integration test"""
    session = requests.Session()
    
    print("🚀 Final Integration Test - Notification HTML Endpoints")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1. 🔐 Testing admin login...")
    login_page = session.get("http://127.0.0.1:8890/login")
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', login_page.text)
    
    if not csrf_match:
        print("   ❌ Could not extract CSRF token")
        return False
    
    csrf_token = csrf_match.group(1)
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    
    login_response = session.post("http://127.0.0.1:8890/login", data=login_data, allow_redirects=False)
    
    if login_response.status_code == 302 and 'dashboard' in login_response.headers.get('Location', ''):
        print("   ✅ Admin login successful")
    else:
        print("   ❌ Login failed")
        return False
    
    # Step 2: Test Payment Notification Endpoint
    print("\n2. 💰 Testing Payment Notification Endpoint...")
    payment_data = {
        "type": "payment",
        "id": "payment_integration_test",
        "timestamp": "2024-01-24T10:00:00Z",
        "data": {
            "user_name": "John Doe",
            "email": "john@example.com",
            "avatar": "https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e",
            "amount": 175.00,
            "activity": "Mountain Biking Adventure",
            "activity_id": 1,
            "paid_date": "2024-01-24T10:00:00Z"
        }
    }
    
    payment_response = session.post(
        "http://127.0.0.1:8890/api/payment-notification-html/integration_test_1",
        json=payment_data
    )
    
    if payment_response.status_code == 200:
        html = payment_response.text
        payment_checks = [
            ('HTML structure', 'event-notification' in html and 'notification-payment' in html),
            ('User name', 'John Doe' in html),
            ('Activity name', 'Mountain Biking Adventure' in html),
            ('Amount', '$175.00' in html),
            ('Payment icon', 'ti-credit-card' in html),
            ('Close button', 'btn-close' in html),
            ('Avatar', 'avatar avatar-md' in html),
            ('Payment status', 'Payment Confirmed' in html)
        ]
        
        all_payment_passed = True
        for check, passed in payment_checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
            if not passed:
                all_payment_passed = False
        
        if all_payment_passed:
            print("   🎉 Payment notification endpoint: ALL TESTS PASSED")
        else:
            print("   ⚠️  Payment notification endpoint: Some tests failed")
    else:
        print(f"   ❌ Payment endpoint failed with status {payment_response.status_code}")
        print(f"   Response: {payment_response.text}")
        all_payment_passed = False
    
    # Step 3: Test Signup Notification Endpoint  
    print("\n3. 📝 Testing Signup Notification Endpoint...")
    signup_data = {
        "type": "signup",
        "id": "signup_integration_test",
        "timestamp": "2024-01-24T10:05:00Z",
        "data": {
            "user_name": "Jane Smith",
            "email": "jane.smith@example.com",
            "avatar": "https://www.gravatar.com/avatar/25f9e794323b453885f5181f1b624d0b",
            "activity": "Rock Climbing Expedition",
            "activity_id": 2,
            "passport_type": "Premium Pass",
            "passport_type_price": 75.50,
            "phone": "+1-555-0123"
        }
    }
    
    signup_response = session.post(
        "http://127.0.0.1:8890/api/signup-notification-html/integration_test_2",
        json=signup_data
    )
    
    if signup_response.status_code == 200:
        html = signup_response.text
        signup_checks = [
            ('HTML structure', 'event-notification' in html and 'notification-signup' in html),
            ('User name', 'Jane Smith' in html),
            ('Activity name', 'Rock Climbing Expedition' in html),
            ('Passport type', 'Premium Pass' in html),
            ('Price', '$75.50' in html),
            ('Phone number', '+1-555-0123' in html),
            ('Signup icon', 'ti-user-plus' in html),
            ('Close button', 'btn-close' in html),
            ('Avatar', 'avatar avatar-md' in html),
            ('Signup status', 'Registration Pending' in html)
        ]
        
        all_signup_passed = True
        for check, passed in signup_checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
            if not passed:
                all_signup_passed = False
        
        if all_signup_passed:
            print("   🎉 Signup notification endpoint: ALL TESTS PASSED")
        else:
            print("   ⚠️  Signup notification endpoint: Some tests failed")
    else:
        print(f"   ❌ Signup endpoint failed with status {signup_response.status_code}")
        print(f"   Response: {signup_response.text}")
        all_signup_passed = False
    
    # Step 4: Test Error Handling
    print("\n4. 🛡️  Testing Error Handling...")
    
    # Test with missing data
    error_response = session.post(
        "http://127.0.0.1:8890/api/payment-notification-html/error_test",
        json={}
    )
    
    if error_response.status_code == 400:
        print("   ✅ Empty data properly rejected")
        error_handling_passed = True
    else:
        print(f"   ❌ Expected 400 for empty data, got {error_response.status_code}")
        error_handling_passed = False
    
    # Test without admin session
    no_auth_session = requests.Session()
    no_auth_response = no_auth_session.post(
        "http://127.0.0.1:8890/api/payment-notification-html/no_auth_test",
        json=payment_data
    )
    
    if no_auth_response.status_code == 401:
        print("   ✅ Unauthorized access properly blocked")
        if error_handling_passed:
            error_handling_passed = True
    else:
        print(f"   ❌ Expected 401 for no auth, got {no_auth_response.status_code}")
        error_handling_passed = False
    
    # Final Summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS:")
    print(f"   Payment Endpoint: {'✅ PASS' if all_payment_passed else '❌ FAIL'}")
    print(f"   Signup Endpoint:  {'✅ PASS' if all_signup_passed else '❌ FAIL'}")
    print(f"   Error Handling:   {'✅ PASS' if error_handling_passed else '❌ FAIL'}")
    
    overall_pass = all_payment_passed and all_signup_passed and error_handling_passed
    print(f"\n🏆 OVERALL RESULT: {'✅ ALL TESTS PASSED!' if overall_pass else '❌ Some tests failed'}")
    
    if overall_pass:
        print("\n🎉 Notification HTML endpoints are working correctly!")
        print("   - Both payment and signup endpoints generate proper HTML")
        print("   - Authentication is properly enforced")
        print("   - Error handling works as expected")
        print("   - Integration with event-notifications.js should work seamlessly")
    
    return overall_pass

if __name__ == "__main__":
    success = test_integration()
    exit(0 if success else 1)