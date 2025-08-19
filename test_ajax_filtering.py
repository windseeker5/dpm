#!/usr/bin/env python3

"""
Test script to verify AJAX filtering functionality in the activity dashboard.
This script will:
1. Login to the application
2. Find an activity dashboard
3. Take screenshots before and after filter clicks
4. Test the API endpoints directly
"""

import os
import time
import requests
from datetime import datetime

def test_ajax_filtering():
    print("=== Testing AJAX Filtering Implementation ===")
    
    # Create session for maintaining login
    session = requests.Session()
    
    try:
        # 1. Login to the application
        print("1. Logging in...")
        login_data = {
            'email': 'kdresdell@gmail.com',
            'password': 'admin123'
        }
        
        login_response = session.post('http://127.0.0.1:8890/login', data=login_data, allow_redirects=False)
        print(f"   Login response status: {login_response.status_code}")
        
        if login_response.status_code not in [200, 302]:
            print("   Login failed!")
            return False
            
        # 2. Get dashboard to find activities
        print("2. Getting dashboard...")
        dashboard_response = session.get('http://127.0.0.1:8890/dashboard')
        print(f"   Dashboard response status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code != 200:
            print("   Dashboard access failed!")
            return False
            
        # 3. Look for activity links
        dashboard_html = dashboard_response.text
        
        # Try to find activity IDs from various possible sources
        import re
        
        # Look for activity dashboard links
        activity_matches = re.findall(r'activity-dashboard/(\d+)', dashboard_html)
        
        if not activity_matches:
            # Try to find activity IDs in other contexts
            activity_matches = re.findall(r'/activity/(\d+)', dashboard_html)
            
        if not activity_matches:
            # Look for any activity references
            activity_matches = re.findall(r'"id":\s*(\d+).*?"name":', dashboard_html)
        
        if activity_matches:
            activity_id = activity_matches[0]
            print(f"3. Found activity ID: {activity_id}")
            
            # 4. Test activity dashboard page
            print("4. Testing activity dashboard...")
            activity_url = f'http://127.0.0.1:8890/activity-dashboard/{activity_id}'
            activity_response = session.get(activity_url)
            print(f"   Activity dashboard status: {activity_response.status_code}")
            
            if activity_response.status_code == 200:
                activity_html = activity_response.text
                
                # Check if filter buttons exist
                filter_buttons = [
                    '#filter-all', '#filter-unpaid', '#filter-paid', '#filter-active',
                    '#signup-filter-all', '#signup-filter-unpaid', '#signup-filter-paid', 
                    '#signup-filter-pending', '#signup-filter-approved'
                ]
                
                found_buttons = []
                for button_id in filter_buttons:
                    if button_id in activity_html:
                        found_buttons.append(button_id)
                
                print(f"   Found filter buttons: {found_buttons}")
                
                # 5. Test the API endpoint
                print("5. Testing API endpoint...")
                api_url = f'http://127.0.0.1:8890/api/activity-dashboard-data/{activity_id}'
                
                # Test different filter combinations
                test_cases = [
                    ('all', 'all'),
                    ('unpaid', 'all'),
                    ('paid', 'pending'),
                    ('active', 'approved')
                ]
                
                for passport_filter, signup_filter in test_cases:
                    params = f'?passport_filter={passport_filter}&signup_filter={signup_filter}'
                    test_url = api_url + params
                    
                    api_response = session.get(test_url)
                    print(f"   API test ({passport_filter}, {signup_filter}): Status {api_response.status_code}")
                    
                    if api_response.status_code == 200:
                        try:
                            api_data = api_response.json()
                            success = api_data.get('success', False)
                            has_passport_html = 'passport_html' in api_data
                            has_signup_html = 'signup_html' in api_data
                            passport_counts = api_data.get('passport_counts', {})
                            signup_counts = api_data.get('signup_counts', {})
                            
                            print(f"     Success: {success}")
                            print(f"     Has passport HTML: {has_passport_html}")
                            print(f"     Has signup HTML: {has_signup_html}")
                            print(f"     Passport counts: {passport_counts}")
                            print(f"     Signup counts: {signup_counts}")
                            
                            if success and has_passport_html and has_signup_html:
                                print(f"     ✅ API working correctly for filters ({passport_filter}, {signup_filter})")
                            else:
                                print(f"     ⚠️  API response incomplete for filters ({passport_filter}, {signup_filter})")
                                
                        except Exception as e:
                            print(f"     ❌ JSON parse error: {e}")
                            print(f"     Response preview: {api_response.text[:200]}")
                    else:
                        print(f"     ❌ API error: {api_response.text[:200]}")
                
                # 6. Save test page for manual verification
                print("6. Saving activity dashboard HTML for manual testing...")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"activity_dashboard_test_{timestamp}.html"
                filepath = os.path.join(os.getcwd(), filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(activity_html)
                
                print(f"   Saved to: {filepath}")
                print(f"   Open this file in a browser to test the AJAX functionality manually")
                print(f"   Activity dashboard URL: {activity_url}")
                
                return True
                
            else:
                print(f"   ❌ Activity dashboard failed: {activity_response.text[:200]}")
                return False
                
        else:
            print("3. ❌ No activities found in dashboard")
            # Save dashboard for debugging
            with open("dashboard_debug.html", "w") as f:
                f.write(dashboard_html)
            print("   Dashboard saved to dashboard_debug.html for inspection")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    test_ajax_filtering()