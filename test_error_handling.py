#!/usr/bin/env python3
"""
Test script to verify Unsplash error handling improvements.
This script simulates the user interaction to test error messages.
"""

import requests
import json
import time

def test_unsplash_error_handling():
    base_url = "http://127.0.0.1:8890"
    session = requests.Session()
    
    print("🧪 Testing Unsplash Error Handling Improvements")
    print("=" * 50)
    
    # Step 1: Login
    print("1. Logging in...")
    login_response = session.post(f"{base_url}/login", data={
        "email": "kdresdell@gmail.com",
        "password": "admin123"
    }, allow_redirects=False)
    
    if login_response.status_code == 302:
        print("✅ Login successful")
    else:
        print("❌ Login failed")
        return False
    
    # Step 2: Test Unsplash search endpoint directly
    print("\n2. Testing Unsplash search endpoint...")
    search_response = session.get(f"{base_url}/unsplash-search", params={
        "q": "test",
        "page": 1
    })
    
    print(f"   Status Code: {search_response.status_code}")
    
    if search_response.status_code == 200:
        try:
            data = search_response.json()
            print(f"   ✅ API working - returned {len(data)} images")
            return True
        except json.JSONDecodeError:
            print("   ❌ Invalid JSON response")
            print(f"   Response: {search_response.text[:200]}...")
            return False
    else:
        try:
            error_data = search_response.json()
            error_message = error_data.get("error", "Unknown error")
            print(f"   ❌ API Error: {error_message}")
            
            # Check if error message is user-friendly
            if "API key" in error_message:
                print("   ✅ User-friendly API key error detected")
            elif "temporarily unavailable" in error_message:
                print("   ✅ User-friendly service unavailable error detected")
            elif error_message == "Error loading images":
                print("   ❌ Generic error message (needs improvement)")
            else:
                print(f"   ⚠️  Custom error message: {error_message}")
            
            return False
        except json.JSONDecodeError:
            print(f"   ❌ Non-JSON error response: {search_response.text[:200]}...")
            return False

def test_activity_page_access():
    """Test accessing the activity edit page"""
    base_url = "http://127.0.0.1:8890"
    session = requests.Session()
    
    print("\n3. Testing activity edit page access...")
    
    # Login first
    login_response = session.post(f"{base_url}/login", data={
        "email": "kdresdell@gmail.com", 
        "password": "admin123"
    }, allow_redirects=False)
    
    if login_response.status_code != 302:
        print("   ❌ Login failed for activity page test")
        return False
    
    # Access activity edit page
    activity_response = session.get(f"{base_url}/edit-activity/1")
    
    if activity_response.status_code == 200:
        print("   ✅ Activity edit page accessible")
        
        # Check if the page contains the image search functionality
        page_content = activity_response.text
        if "Search images from the Web" in page_content:
            print("   ✅ Image search toggle found on page")
        else:
            print("   ❌ Image search toggle not found")
            
        if "searchImagesBtn" in page_content:
            print("   ✅ Search button JavaScript found")
        else:
            print("   ❌ Search button JavaScript not found")
            
        return True
    else:
        print(f"   ❌ Cannot access activity page (status: {activity_response.status_code})")
        return False

if __name__ == "__main__":
    print("Testing Unsplash Error Handling Implementation")
    print("This will verify the improved error messages are working.")
    print()
    
    # Test the backend functionality
    api_working = test_unsplash_error_handling()
    page_accessible = test_activity_page_access()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   API Functionality: {'✅ Working' if api_working else '❌ Has errors (this is expected for testing)'}")
    print(f"   Page Accessibility: {'✅ Working' if page_accessible else '❌ Failed'}")
    
    if not api_working:
        print("\n💡 Note: API errors are expected if the Unsplash API key is not configured.")
        print("   The important thing is that user-friendly error messages are shown.")