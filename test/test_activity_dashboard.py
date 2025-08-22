#!/usr/bin/env python3
"""
Test script to verify activity dashboard AJAX filtering functionality
"""
import requests
import json

# Base URL for the Flask app
BASE_URL = "http://127.0.0.1:8890"

def login():
    """Login and get session cookie"""
    session = requests.Session()
    
    # First get the login page to get CSRF token
    login_page = session.get(f"{BASE_URL}/login")
    
    # Extract CSRF token (simple approach)
    csrf_token = None
    if 'csrf_token' in login_page.text:
        import re
        match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page.text)
        if match:
            csrf_token = match.group(1)
    
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123'
    }
    
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    # Check if redirected to dashboard or if we're still on login page
    if 'dashboard' in response.url or response.status_code == 302:
        print("✅ Login successful")
        return session
    else:
        print(f"❌ Login failed - Status: {response.status_code}, URL: {response.url}")
        return None

def test_activity_dashboard_page(session):
    """Test that the activity dashboard page loads"""
    response = session.get(f"{BASE_URL}/activity-dashboard/1")
    
    if response.status_code == 200:
        print("✅ Activity dashboard page loads successfully")
        
        # Check for filter buttons
        if 'github-filter-btn' in response.text:
            print("✅ Filter buttons found in HTML")
        else:
            print("❌ Filter buttons not found")
            
        # Check for search input
        if 'enhancedSearchInput' in response.text:
            print("✅ Search input found in HTML")
        else:
            print("❌ Search input not found")
            
        # Check for FilterComponent initialization
        if 'FilterComponent.init' in response.text:
            print("✅ FilterComponent initialization found")
        else:
            print("❌ FilterComponent initialization not found")
            
        # Check for AJAX mode
        if 'mode: \'ajax\'' in response.text:
            print("✅ FilterComponent set to AJAX mode")
        else:
            print("❌ FilterComponent not in AJAX mode")
        
        return True
    else:
        print(f"❌ Activity dashboard page failed to load: {response.status_code}")
        return False

def test_api_endpoint(session):
    """Test the API endpoint for filtering"""
    api_url = f"{BASE_URL}/api/activity-dashboard-data/1"
    params = {
        'passport_filter': 'all',
        'signup_filter': 'all'
    }
    
    response = session.get(api_url, params=params)
    
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get('success'):
                print("✅ API endpoint returns successful response")
                
                # Check for required fields
                required_fields = ['passport_html', 'signup_html', 'passport_counts', 'signup_counts']
                for field in required_fields:
                    if field in data:
                        print(f"✅ API response contains {field}")
                    else:
                        print(f"❌ API response missing {field}")
                
                return True
            else:
                print(f"❌ API endpoint returns error: {data.get('error', 'Unknown error')}")
                return False
        except json.JSONDecodeError:
            print("❌ API endpoint returns invalid JSON")
            return False
    else:
        print(f"❌ API endpoint failed: {response.status_code}")
        if response.status_code == 404:
            print("   Activity ID 1 might not exist")
        return False

def main():
    print("🧪 Testing Activity Dashboard AJAX Filtering")
    print("=" * 50)
    
    # Login
    session = login()
    if not session:
        print("Cannot proceed without login")
        return
    
    # Test activity dashboard page
    if not test_activity_dashboard_page(session):
        print("Activity dashboard page test failed")
        return
    
    print()
    
    # Test API endpoint
    if not test_api_endpoint(session):
        print("API endpoint test failed") 
        return
    
    print()
    print("🎉 Testing complete!")

if __name__ == "__main__":
    main()
