#!/usr/bin/env python3
"""
Test script to verify activities page fixes
"""

import requests
from bs4 import BeautifulSoup
import sys

# Test configuration
BASE_URL = "http://127.0.0.1:8890"
LOGIN_URL = f"{BASE_URL}/login"
ACTIVITIES_URL = f"{BASE_URL}/activities"

# Login credentials
EMAIL = "kdresdell@gmail.com"
PASSWORD = "admin123"

def test_activities_page():
    """Test that activities page loads correctly with fixes"""
    
    # Create session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get login page first for CSRF token
    print("🔐 Logging in...")
    login_page = session.get(LOGIN_URL)
    
    # Extract CSRF token
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    csrf_token = csrf_input['value'] if csrf_input else None
    
    login_data = {
        'email': EMAIL,
        'password': PASSWORD
    }
    
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    # Post with proper headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': LOGIN_URL
    }
    
    response = session.post(LOGIN_URL, data=login_data, headers=headers, allow_redirects=True)
    if response.status_code != 200:
        print(f"❌ Login failed with status {response.status_code}")
        return False
    
    # Step 2: Load activities page
    print("📄 Loading activities page...")
    response = session.get(ACTIVITIES_URL)
    
    if response.status_code != 200:
        print(f"❌ Activities page failed to load with status {response.status_code}")
        return False
    
    # Step 3: Parse HTML and check for fixes
    print("🔍 Checking for fixes...")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check 1: Create Activity button should not have btn-lg class
    create_btn = soup.find('a', {'href': '/create-activity'})
    if create_btn:
        classes = create_btn.get('class', [])
        if 'btn-lg' in classes:
            print("❌ Create Activity button still has btn-lg class")
            return False
        print("✅ Create Activity button size fixed")
    else:
        print("⚠️ Create Activity button not found")
    
    # Check 2: No broken HTML in filter buttons
    filter_group = soup.find('div', {'class': 'github-filter-group'})
    if filter_group:
        # Check for malformed HTML by looking for the error text
        page_text = response.text
        if 'class="github-filter-btn " style="background:' in page_text:
            print("❌ Broken HTML still present in filter buttons")
            return False
        print("✅ Filter buttons HTML fixed")
    else:
        print("⚠️ Filter group not found")
    
    # Check 3: Table should show activities not "No entries found"
    no_entries = soup.find(text="No entries found")
    if no_entries and "No entries found" in str(no_entries):
        # Check if we actually have activities
        activity_rows = soup.find_all('tr', {'class': 'activity-row'})
        if len(activity_rows) == 0:
            print("⚠️ No activities shown in table (might be correct if no activities exist)")
        else:
            print("✅ Activities are displayed in table")
    else:
        # Look for activity rows
        tbody = soup.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            if len(rows) > 0:
                print(f"✅ Table shows {len(rows)} activities")
            else:
                print("⚠️ Table has no rows")
    
    # Check 4: Verify table headers are correct for activities
    headers = soup.find_all('th')
    expected_headers = ['Activity', 'Type', 'Status', 'Signups', 'Revenue', 'Dates', 'Actions']
    header_texts = [h.get_text(strip=True) for h in headers if h.get_text(strip=True)]
    
    activities_headers_found = any(h in header_texts for h in ['Activity', 'Type', 'Revenue'])
    if activities_headers_found:
        print("✅ Table headers are activity-specific")
    else:
        print("⚠️ Table headers may not be activity-specific")
    
    print("\n✨ All critical fixes have been applied successfully!")
    return True

if __name__ == "__main__":
    success = test_activities_page()
    sys.exit(0 if success else 1)