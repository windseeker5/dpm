#!/usr/bin/env python3

"""
Focused test for AJAX filtering on Activity 1 (which has 5 passports and 3 signups)
"""

import requests
import time
import json
from datetime import datetime

def test_ajax_filtering_focused():
    print("=== AJAX Filtering Test for Activity 1 ===")
    print(f"Test time: {datetime.now()}")
    print("")
    
    # Test the specific activity that has data
    activity_id = 1  # From database check: has 5 passports, 3 signups
    
    print(f"Testing Activity {activity_id} (has 5 passports, 3 signups)")
    
    try:
        # Test activity dashboard page (without login - just to see structure)
        print("\n1. Testing activity dashboard page structure...")
        url = f"http://127.0.0.1:8890/activity-dashboard/{activity_id}"
        response = requests.get(url)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            
            # Check for filter buttons
            filter_buttons = [
                'id="filter-all"', 'id="filter-unpaid"', 'id="filter-paid"', 'id="filter-active"',
                'id="signup-filter-all"', 'id="signup-filter-unpaid"', 'id="signup-filter-paid"', 
                'id="signup-filter-pending"', 'id="signup-filter-approved"'
            ]
            
            found_buttons = []
            for button in filter_buttons:
                if button in html:
                    found_buttons.append(button)
            
            print(f"   Found {len(found_buttons)} filter buttons:")
            for btn in found_buttons:
                print(f"     ✅ {btn}")
            
            # Check for JavaScript functions
            js_functions = [
                'function filterPassports', 'function filterSignups',
                'getCurrentPassportFilter', 'getCurrentSignupFilter',
                'updateFilterCounts', 'updateURL', 'showFilterError'
            ]
            
            found_functions = []
            for func in js_functions:
                if func in html:
                    found_functions.append(func)
            
            print(f"   Found {len(found_functions)} JavaScript functions:")
            for func in found_functions:
                print(f"     ✅ {func}")
            
            # Check for AJAX API calls
            if 'api/activity-dashboard-data' in html:
                print("     ✅ API endpoint references found in JavaScript")
            else:
                print("     ⚠️  No API endpoint references found")
            
            # Look for table structure
            passport_table_found = 'passport-checkbox' in html
            signup_table_found = 'signup-checkbox' in html
            
            print(f"   Passport table: {'✅ Found' if passport_table_found else '❌ Not found'}")
            print(f"   Signup table: {'✅ Found' if signup_table_found else '❌ Not found'}")
            
        elif response.status_code == 302:
            print("   ⚠️  Redirected to login (expected without authentication)")
            print("   This means the route exists and is protected correctly")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            
        # Test API endpoint directly (will fail without auth, but we can see if it exists)
        print("\n2. Testing API endpoint...")
        api_url = f"http://127.0.0.1:8890/api/activity-dashboard-data/{activity_id}?passport_filter=all&signup_filter=all"
        api_response = requests.get(api_url)
        
        print(f"   API Status: {api_response.status_code}")
        if api_response.status_code == 401:
            print("   ✅ API endpoint exists (returns 401 Unauthorized as expected)")
        elif api_response.status_code == 404:
            print("   ❌ API endpoint not found")
        else:
            print(f"   Status: {api_response.status_code}")
            
        print("\n=== Manual Testing Instructions ===")
        print("To complete the test:")
        print("1. Open browser and navigate to: http://127.0.0.1:8890/login")
        print("2. Login with: kdresdell@gmail.com / admin123")
        print(f"3. Navigate to: http://127.0.0.1:8890/activity-dashboard/{activity_id}")
        print("4. Open Browser Dev Tools (F12) -> Network tab")
        print("5. Click different filter buttons:")
        print("   - Passport filters: All, Unpaid, Paid, Active")
        print("   - Signup filters: All Signups, Unpaid, Paid, Pending, Approved")
        print("6. Verify:")
        print("   - AJAX requests appear in Network tab to /api/activity-dashboard-data/1")
        print("   - Tables update without page reload")
        print("   - URL updates with filter parameters") 
        print("   - Filter counts update correctly")
        print("   - No scroll position changes")
        
        print("\n=== Expected Behavior ===")
        print("✅ Filter buttons should trigger AJAX calls")
        print("✅ Tables should update content without page reload") 
        print("✅ URL should update with ?passport_filter=X&signup_filter=Y")
        print("✅ Filter button counts should update: (5), (3), etc.")
        print("✅ Page should NOT scroll or reload")
        print("❌ Old behavior: Page reloads and scrolls to top")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_ajax_filtering_focused()
    if success:
        print("\n🎯 Test setup completed. Please follow manual testing instructions above.")
    else:
        print("\n💥 Test setup failed. Check errors above.")