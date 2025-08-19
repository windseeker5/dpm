#!/usr/bin/env python3

"""
Simple test to check if our API endpoint works
"""

import requests
import json

def test_api():
    print("=== Simple API Test ===")
    print("1. Please manually login via browser first at http://127.0.0.1:8890/login")
    print("   Email: kdresdell@gmail.com")
    print("   Password: admin123")
    print("2. Then navigate to an activity dashboard")
    print("3. Check the browser network tab to see what activity ID is being used")
    print("")
    
    # Try a few common activity IDs
    activity_ids = [1, 2, 3]
    
    for activity_id in activity_ids:
        print(f"Testing activity ID {activity_id}...")
        
        try:
            # Make a simple request to see the structure
            url = f"http://127.0.0.1:8890/activity-dashboard/{activity_id}"
            response = requests.get(url)
            
            print(f"  Activity dashboard status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ Activity {activity_id} exists")
                
                # Check if it contains filter buttons
                html = response.text
                filter_count = html.count('github-filter-btn')
                passport_table_count = html.count('passport-checkbox')
                signup_table_count = html.count('signup-checkbox')
                
                print(f"  Filter buttons found: {filter_count}")
                print(f"  Passport checkboxes: {passport_table_count}")
                print(f"  Signup checkboxes: {signup_table_count}")
                
                if filter_count > 0:
                    print(f"  💡 Activity {activity_id} has filter buttons - good for testing!")
                    break
                    
            elif response.status_code == 302:
                print(f"  ⚠️  Redirected (probably need to login)")
                break
            elif response.status_code == 404:
                print(f"  ❌ Activity {activity_id} not found")
            else:
                print(f"  ❌ Error {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    
    print("\n=== Manual Testing Instructions ===")
    print("After logging in via browser:")
    print("1. Open browser dev tools (F12)")
    print("2. Go to Network tab")
    print("3. Navigate to an activity dashboard")
    print("4. Click a filter button (e.g., 'Unpaid')")
    print("5. Look for an AJAX request to '/api/activity-dashboard-data/[ID]'")
    print("6. Check if the table updates without page reload")
    print("7. Verify URL changes to include filter parameters")

if __name__ == "__main__":
    test_api()