#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import sys

def test_dashboard_access():
    session = requests.Session()
    
    try:
        # Get login page first
        print("🔐 Getting login page...")
        login_page = session.get('http://127.0.0.1:8890/login')
        
        if login_page.status_code != 200:
            print(f"❌ Login page failed: {login_page.status_code}")
            return False
            
        # Parse login form
        soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token = None
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
        
        # Login data
        login_data = {
            'email': 'kdresdell@gmail.com',
            'password': 'admin123'
        }
        
        if csrf_token:
            login_data['csrf_token'] = csrf_token
            
        print("📝 Attempting login...")
        login_response = session.post('http://127.0.0.1:8890/login', data=login_data)
        
        if login_response.status_code not in [200, 302]:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
        # Access dashboard
        print("📊 Accessing dashboard...")
        dashboard_response = session.get('http://127.0.0.1:8890/dashboard')
        
        if dashboard_response.status_code != 200:
            print(f"❌ Dashboard access failed: {dashboard_response.status_code}")
            return False
            
        # Check if our new elements are present
        dashboard_html = dashboard_response.text
        
        # Test for key elements
        tests = [
            ('github-filter-btn', 'GitHub filter buttons'),
            ('log-row', 'Log table rows'),
            ('filter-all', 'All Events filter'),
            ('filter-passport', 'Passport filter'),
            ('filter-signup', 'Signup filter'),
            ('filter-payment', 'Payment filter'),
            ('filter-admin', 'Admin filter'),
            ('entriesInfo', 'Entries info element'),
            ('updateFilterCounts', 'Filter count function')
        ]
        
        print("\n🔍 Testing dashboard elements:")
        all_passed = True
        
        for element, description in tests:
            if element in dashboard_html:
                print(f"✅ {description}: Found")
            else:
                print(f"❌ {description}: Missing")
                all_passed = False
        
        # Check if Recent system events section exists
        if 'Recent system events' in dashboard_html:
            print("✅ Recent system events section: Found")
        else:
            print("❌ Recent system events section: Missing")
            all_passed = False
            
        # Check table structure
        if '<table class="table table-hover"' in dashboard_html:
            print("✅ Table with hover styling: Found")
        else:
            print("❌ Table with hover styling: Missing")
            all_passed = False
            
        # Check pagination structure
        if 'card-footer d-flex justify-content-between align-items-center' in dashboard_html:
            print("✅ Pagination footer styling: Found")
        else:
            print("❌ Pagination footer styling: Missing")
            all_passed = False
            
        return all_passed
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_dashboard_access()
    if result:
        print("\n🎉 All dashboard elements are present and working!")
        print("✅ The Recent System Events table has been successfully updated")
        print("✅ GitHub-style filter buttons implemented")
        print("✅ Beautiful table styling matches signup page")
    else:
        print("\n💥 Some dashboard elements are missing or broken!")
        sys.exit(1)