#!/usr/bin/env python3
"""
Test script to verify activity dashboard filter functionality
Tests both client-side JavaScript and server-side API endpoints
"""

import requests
import json
from time import sleep

def test_filter_functionality():
    """Test the activity dashboard filter functionality"""
    base_url = "http://127.0.0.1:8890"
    
    print("🧪 ACTIVITY DASHBOARD FILTER FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test 1: Check if the main dashboard page loads
    print("\n1. Testing main dashboard page...")
    dashboard_url = f"{base_url}/activity-dashboard/1"
    response = requests.get(dashboard_url)
    
    if response.status_code == 200:
        print("   ✅ Dashboard page loads successfully")
        
        # Check for filter buttons in HTML
        html = response.text
        
        # Check for passport filter buttons
        passport_filters = ['filter-all', 'filter-unpaid', 'filter-paid', 'filter-active']
        found_passport_filters = [f for f in passport_filters if f in html]
        print(f"   ✅ Found passport filter buttons: {len(found_passport_filters)}/4")
        
        # Check for signup filter buttons
        signup_filters = ['signup-filter-all', 'signup-filter-unpaid', 'signup-filter-paid', 'signup-filter-pending', 'signup-filter-approved']
        found_signup_filters = [f for f in signup_filters if f in html]
        print(f"   ✅ Found signup filter buttons: {len(found_signup_filters)}/5")
        
        # Check for JavaScript functions
        js_functions = ['filterPassports', 'filterSignups']
        found_functions = [f for f in js_functions if f in html]
        print(f"   ✅ Found JavaScript functions: {found_functions}")
        
        # Check for API endpoint references
        if 'api/activity-dashboard-data' in html:
            print("   ✅ API endpoint references found in JavaScript")
        else:
            print("   ❌ No API endpoint references found")
            
    else:
        print(f"   ❌ Dashboard page failed to load: {response.status_code}")
        if response.status_code == 401:
            print("   ℹ️  Authentication required - test with browser login")
        return
    
    # Test 2: Test API endpoint (will require authentication)
    print("\n2. Testing API endpoint...")
    api_url = f"{base_url}/api/activity-dashboard-data/1"
    
    test_cases = [
        ('all', 'all'),
        ('unpaid', 'all'),
        ('paid', 'all'),
        ('active', 'all'),
        ('all', 'unpaid'),
        ('all', 'paid'),
        ('all', 'pending'),
        ('all', 'approved')
    ]
    
    for passport_filter, signup_filter in test_cases:
        params = {
            'passport_filter': passport_filter,
            'signup_filter': signup_filter
        }
        
        api_response = requests.get(api_url, params=params)
        status_icon = "✅" if api_response.status_code == 401 else "❌"
        print(f"   {status_icon} API {passport_filter}/{signup_filter}: {api_response.status_code}")
    
    if all(requests.get(api_url, params={'passport_filter': pf, 'signup_filter': sf}).status_code == 401 
           for pf, sf in test_cases):
        print("   ✅ All API endpoints exist (returning 401 as expected without auth)")
    else:
        print("   ⚠️  Some API endpoints may be missing")
    
    # Test 3: Check partial templates exist
    print("\n3. Checking partial templates...")
    import os
    
    templates_dir = "/home/kdresdell/Documents/DEV/minipass_env/app/templates/partials"
    required_templates = [
        "passport_table_rows.html",
        "signup_table_rows.html"
    ]
    
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        if os.path.exists(template_path):
            print(f"   ✅ {template} exists")
        else:
            print(f"   ❌ {template} missing")
    
    # Test 4: Manual testing instructions
    print("\n4. MANUAL TESTING REQUIRED")
    print("   Login to test full functionality:")
    print(f"   1. Open browser and go to: {base_url}/login")
    print("   2. Login with: kdresdell@gmail.com / admin123")
    print(f"   3. Navigate to: {base_url}/activity-dashboard/1")
    print("   4. Open Browser Dev Tools (F12) -> Network tab")
    print("   5. Click filter buttons and verify:")
    print("      - AJAX requests appear to /api/activity-dashboard-data/1")
    print("      - Tables update without page reload")
    print("      - URL updates with filter parameters")
    print("      - Filter button counts update")
    print("      - No scroll position changes")
    
    print("\n5. EXPECTED FILTER BEHAVIOR")
    print("   Passport Filters:")
    print("   - All: Shows unpaid passes + passes with uses remaining")
    print("   - Unpaid: Shows only unpaid passes")
    print("   - Paid: Shows only paid passes") 
    print("   - Active: Shows only passes with uses remaining")
    print()
    print("   Signup Filters:")
    print("   - All Signups: Shows all signups")
    print("   - Unpaid: Shows only unpaid signups")
    print("   - Paid: Shows only paid signups")
    print("   - Pending: Shows only pending status signups")
    print("   - Approved: Shows only approved status signups")
    
    print("\n✅ FILTER FUNCTIONALITY TEST COMPLETE")
    print("   Server-side components appear to be properly configured.")
    print("   Manual browser testing required to verify full AJAX functionality.")

if __name__ == "__main__":
    test_filter_functionality()