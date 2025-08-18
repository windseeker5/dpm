#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup

session = requests.Session()

# Get login page 
login_page = session.get('http://127.0.0.1:8890/login')
print(f"Login page status: {login_page.status_code}")

# Parse CSRF token if exists
soup = BeautifulSoup(login_page.text, 'html.parser')
csrf_token = None
csrf_input = soup.find('input', {'name': 'csrf_token'})
if csrf_input:
    csrf_token = csrf_input.get('value')
    print(f"CSRF token found: {csrf_token[:20]}...")

# Login
login_data = {
    'email': 'kdresdell@gmail.com',
    'password': 'admin123'
}
if csrf_token:
    login_data['csrf_token'] = csrf_token

login_response = session.post('http://127.0.0.1:8890/login', data=login_data)
print(f"Login response status: {login_response.status_code}")
print(f"Login response URL: {login_response.url}")

# Get dashboard
dashboard_response = session.get('http://127.0.0.1:8890/dashboard')
print(f"Dashboard status: {dashboard_response.status_code}")
print(f"Dashboard URL: {dashboard_response.url}")

# Check if we're redirected to login (not authenticated)
if 'login' in dashboard_response.url:
    print("❌ Redirected to login - authentication failed")
else:
    print("✅ Successfully accessed dashboard")
    
    # Look for specific content
    html = dashboard_response.text
    
    print(f"HTML length: {len(html)} characters")
    
    # Check for key indicators
    if "Recent system events" in html:
        print("✅ Found 'Recent system events' section")
    else:
        print("❌ Missing 'Recent system events' section")
        
    if "github-filter-group" in html:
        print("✅ Found filter group")
    else:
        print("❌ Missing filter group")
        
    # Look for the activity log section
    if "activity-log-section" in html:
        print("✅ Found activity log section")
        
        # Extract the events section
        start = html.find('activity-log-section')
        if start != -1:
            end = html.find('</div>', start + 1000)  # Look for closing div
            section = html[start:end]
            print(f"Events section length: {end - start} characters")
            
            # Count elements in section
            if 'github-filter-btn' in section:
                print("✅ Filter buttons found in section")
            if 'log-row' in section:
                print("✅ Log rows found in section")
    else:
        print("❌ Missing activity log section")
        
    # Save HTML for inspection
    with open('/tmp/dashboard_debug.html', 'w') as f:
        f.write(html)
    print("💾 Full HTML saved to /tmp/dashboard_debug.html")