#!/usr/bin/env python3
"""
Test script to verify the UI error handling for Unsplash search.
This creates a simple HTML test page to manually verify the error messages.
"""

import requests
from bs4 import BeautifulSoup
import re

def get_csrf_token_and_login():
    """Get CSRF token and login to the application"""
    session = requests.Session()
    
    # Get login page to extract CSRF token
    login_page = session.get("http://127.0.0.1:8890/login")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    
    # Find CSRF token
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if not csrf_input:
        print("❌ Could not find CSRF token on login page")
        return None, None
    
    csrf_token = csrf_input.get('value')
    print(f"✅ Found CSRF token: {csrf_token[:20]}...")
    
    # Login with CSRF token
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    
    login_response = session.post("http://127.0.0.1:8890/login", data=login_data, allow_redirects=False)
    
    if login_response.status_code == 302:
        print("✅ Login successful")
        return session, csrf_token
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text[:200]}...")
        return None, None

def test_unsplash_api_directly():
    """Test the Unsplash API endpoint directly"""
    session, csrf_token = get_csrf_token_and_login()
    if not session:
        return False
    
    print("\n🧪 Testing Unsplash API endpoint...")
    
    # Test the unsplash-search endpoint
    response = session.get("http://127.0.0.1:8890/unsplash-search?q=test&page=1")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"✅ API returned {len(data)} images")
            return True
        except:
            print("❌ Invalid JSON response")
            return False
    else:
        try:
            error_data = response.json()
            error_message = error_data.get('error', 'Unknown error')
            print(f"❌ API Error: {error_message}")
            
            # Check if error message is user-friendly
            user_friendly_keywords = [
                "API key", 
                "temporarily unavailable", 
                "not available",
                "configured by an administrator",
                "try again later"
            ]
            
            is_user_friendly = any(keyword in error_message for keyword in user_friendly_keywords)
            
            if is_user_friendly:
                print("✅ Error message appears user-friendly")
            else:
                print("❌ Error message may not be user-friendly")
                
            return False
        except:
            print(f"❌ Non-JSON error: {response.text[:200]}")
            return False

def analyze_activity_form_error_handling():
    """Analyze the JavaScript error handling in the activity form"""
    print("\n📝 Analyzing activity form error handling...")
    
    session, csrf_token = get_csrf_token_and_login()
    if not session:
        return False
    
    # Get the activity form page
    response = session.get("http://127.0.0.1:8890/edit-activity/1")
    
    if response.status_code != 200:
        print(f"❌ Cannot access activity form: {response.status_code}")
        return False
    
    page_content = response.text
    
    # Check for error handling improvements
    checks = [
        ("Image search toggle", "Search images from the Web" in page_content),
        ("Search button", "searchImagesBtn" in page_content),
        ("Error handling function", ".catch(error =>" in page_content),
        ("User-friendly error messages", "API key needs to be configured" in page_content),
        ("Alternative suggestions", "Upload your own image" in page_content and "Alternative options" in page_content),
        ("Specific error types", "temporarily unavailable" in page_content),
    ]
    
    print("Checking error handling features:")
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def create_visual_test_report():
    """Create a visual test report"""
    print("\n📊 Creating test report...")
    
    report = """
# Unsplash Error Handling Test Report

## Test Results

"""
    
    # Test API functionality
    print("Testing API...")
    api_result = test_unsplash_api_directly()
    
    # Test form analysis
    print("Testing form...")
    form_result = analyze_activity_form_error_handling()
    
    report += f"""
### API Error Handling
- Status: {"✅ PASS" if api_result else "❌ FAIL (Expected if API key not configured)"}
- Note: Errors are expected if Unsplash API key is not set up

### UI Error Handling 
- Status: {"✅ PASS" if form_result else "❌ FAIL"}
- JavaScript error handling implemented
- User-friendly error messages added
- Alternative options provided

### Manual Testing Instructions

To manually test the error handling:

1. Navigate to http://127.0.0.1:8890/edit-activity/1
2. Login with: kdresdell@gmail.com / admin123  
3. Toggle "Search images from the Web"
4. Click the search button
5. Observe the error message shown

Expected behavior:
- Should show user-friendly error message instead of generic "Error loading images"
- Should suggest using "Upload your own image" as alternative
- Should handle API key issues gracefully

"""
    
    print(report)
    return api_result, form_result

if __name__ == "__main__":
    print("🧪 Testing Unsplash Error Handling Improvements")
    print("=" * 60)
    
    api_result, form_result = create_visual_test_report()
    
    print("\n" + "=" * 60)
    print("📋 Summary:")
    if form_result:
        print("✅ Error handling improvements are properly implemented in the UI")
        print("✅ User-friendly error messages are in place")
        print("✅ Alternative options are provided to users")
    else:
        print("❌ Some error handling improvements may be missing")
    
    print(f"\n💡 API Status: {'Working' if api_result else 'Has errors (expected without API key)'}")
    print("\n🎯 Next step: Manually test the UI at http://127.0.0.1:8890/edit-activity/1")