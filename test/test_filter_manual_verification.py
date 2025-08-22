#!/usr/bin/env python3
"""
Manual verification script for activity dashboard filter functionality
This creates a simple test plan for manual verification
"""

import requests

def create_test_plan():
    """Create a comprehensive test plan for manual verification"""
    
    print("🧪 ACTIVITY DASHBOARD FILTER - MANUAL TEST PLAN")
    print("=" * 55)
    
    # First, let's check what activities exist
    print("\n📋 PRE-TEST SETUP")
    print("1. Verify Flask server is running on http://127.0.0.1:8890")
    
    # Test server connectivity
    try:
        response = requests.get("http://127.0.0.1:8890")
        if response.status_code in [200, 302]:
            print("   ✅ Flask server is running")
        else:
            print(f"   ⚠️  Flask server status: {response.status_code}")
    except:
        print("   ❌ Cannot connect to Flask server")
        return
    
    print("2. Login credentials: kdresdell@gmail.com / admin123")
    
    print("\n🔍 MANUAL TEST STEPS")
    print("=" * 30)
    
    print("\nSTEP 1: LOGIN AND NAVIGATION")
    print("1. Open browser to: http://127.0.0.1:8890/login")
    print("2. Login with: kdresdell@gmail.com / admin123")
    print("3. Navigate to: http://127.0.0.1:8890/activity-dashboard/1")
    print("4. Verify you see the activity dashboard page")
    
    print("\nSTEP 2: VISUAL INSPECTION")
    print("Expected to see:")
    print("✓ Activity details at the top")
    print("✓ KPI cards (Revenue, Signups, etc.)")
    print("✓ Two main sections: 'Passports' and 'Signups'")
    print("✓ Filter buttons above each table:")
    print("  - Passport filters: All, Unpaid, Paid, Active")
    print("  - Signup filters: All Signups, Unpaid, Paid, Pending, Approved")
    print("✓ Each filter button should show a count in parentheses")
    
    print("\nSTEP 3: JAVASCRIPT CONSOLE CHECK")
    print("1. Open Browser Dev Tools (F12)")
    print("2. Go to Console tab")
    print("3. Type: typeof filterPassports")
    print("   Expected: 'function'")
    print("4. Type: typeof filterSignups") 
    print("   Expected: 'function'")
    print("5. Check for any JavaScript errors in red")
    
    print("\nSTEP 4: NETWORK MONITORING SETUP")
    print("1. In Dev Tools, go to Network tab")
    print("2. Clear any existing requests")
    print("3. Filter by 'XHR' or 'Fetch' to see AJAX requests")
    
    print("\nSTEP 5: TEST PASSPORT FILTERS")
    print("1. Click 'Unpaid' passport filter button")
    print("   Expected:")
    print("   ✓ Button becomes active/highlighted")
    print("   ✓ AJAX request appears in Network tab to /api/activity-dashboard-data/1")
    print("   ✓ Passport table updates without page reload")
    print("   ✓ URL updates to include ?passport_filter=unpaid")
    print("   ✓ Only unpaid passports are shown")
    
    print("\n2. Click 'Paid' passport filter button")
    print("   Expected:")
    print("   ✓ 'Paid' button becomes active, 'Unpaid' becomes inactive")
    print("   ✓ New AJAX request in Network tab")
    print("   ✓ Table shows only paid passports")
    print("   ✓ URL updates to ?passport_filter=paid")
    
    print("\n3. Click 'Active' passport filter button")
    print("   Expected:")
    print("   ✓ Shows only passports with uses_remaining > 0")
    
    print("\n4. Click 'All' passport filter button")
    print("   Expected:")
    print("   ✓ Shows unpaid passports + passports with remaining uses")
    
    print("\nSTEP 6: TEST SIGNUP FILTERS")
    print("1. Click 'Unpaid' signup filter button")
    print("   Expected:")
    print("   ✓ Button becomes active")
    print("   ✓ AJAX request to API with signup_filter=unpaid")
    print("   ✓ Signup table updates to show only unpaid signups")
    print("   ✓ URL includes both passport and signup filters")
    
    print("\n2. Test other signup filters: Paid, Pending, Approved")
    print("   Expected: Similar behavior with appropriate filtering")
    
    print("\nSTEP 7: TEST COMBINED FILTERS")
    print("1. Set passport filter to 'Unpaid'")
    print("2. Set signup filter to 'Paid'")
    print("   Expected:")
    print("   ✓ URL shows both filters: ?passport_filter=unpaid&signup_filter=paid")
    print("   ✓ Both tables show correctly filtered data")
    print("   ✓ Each filter change maintains the other filter's state")
    
    print("\nSTEP 8: TEST PAGE REFRESH")
    print("1. With filters applied, refresh the page (F5)")
    print("   Expected:")
    print("   ✓ Page loads with same filters applied")
    print("   ✓ Correct filter buttons are active")
    print("   ✓ Tables show filtered data")
    
    print("\nSTEP 9: TEST RESPONSIVE DESIGN")
    print("1. Resize browser window to mobile size")
    print("   Expected:")
    print("   ✓ Filter buttons stack appropriately")
    print("   ✓ Tables remain functional")
    print("   ✓ AJAX filtering still works")
    
    print("\n🚨 TROUBLESHOOTING")
    print("=" * 20)
    print("If filter buttons don't appear:")
    print("• Check if activity has any passports/signups")
    print("• Verify you're logged in as admin")
    print("• Check browser console for JavaScript errors")
    
    print("\nIf buttons exist but don't work:")
    print("• Check Network tab for failed AJAX requests")
    print("• Look for 401/500 errors in API calls")
    print("• Verify JavaScript functions exist in console")
    
    print("\nIf AJAX requests fail:")
    print("• Check server logs for API endpoint errors") 
    print("• Verify session is still valid")
    print("• Test API endpoint directly in browser")
    
    print("\n✅ COMPLETION CRITERIA")
    print("=" * 25)
    print("Test is successful when:")
    print("✓ All filter buttons are visible and clickable")
    print("✓ AJAX requests are made on button clicks")
    print("✓ Tables update without page reload")
    print("✓ URL parameters update correctly")
    print("✓ Filter counts are accurate")
    print("✓ Combined filters work together")
    print("✓ Page refresh preserves filter state")
    print("✓ No JavaScript console errors")
    
    print(f"\n🔗 QUICK LINKS")
    print("=" * 15)
    print("Dashboard: http://127.0.0.1:8890/activity-dashboard/1")
    print("Login: http://127.0.0.1:8890/login")
    print("API Test: http://127.0.0.1:8890/api/activity-dashboard-data/1?passport_filter=all&signup_filter=all")

if __name__ == "__main__":
    create_test_plan()