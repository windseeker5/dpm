#!/usr/bin/env python3
"""Test the filter buttons on the signups page"""

import requests
from bs4 import BeautifulSoup

# Start a session to maintain cookies
session = requests.Session()

# First GET the login page to get CSRF token
login_url = "http://127.0.0.1:8890/login"
login_page = session.get(login_url)
soup = BeautifulSoup(login_page.text, 'html.parser')

# Find CSRF token
csrf_token = None
csrf_input = soup.find('input', {'name': 'csrf_token'})
if csrf_input:
    csrf_token = csrf_input.get('value')
    print(f"Found CSRF token: {csrf_token[:20]}...")
else:
    print("Warning: No CSRF token found")

# Login with CSRF token
login_data = {
    "email": "kdresdell@gmail.com",
    "password": "admin123"
}
if csrf_token:
    login_data["csrf_token"] = csrf_token

# Perform login
login_response = session.post(login_url, data=login_data, allow_redirects=False)
print(f"Login status: {login_response.status_code}")

# Follow redirect if successful
if login_response.status_code == 302:
    redirect_url = login_response.headers.get('Location', '/')
    print(f"Login successful! Redirecting to: {redirect_url}")

# Now access the signups page
signups_url = "http://127.0.0.1:8890/signups"
response = session.get(signups_url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check if filter buttons are present
    filter_section = soup.find('div', {'id': 'filterButtons'})
    if filter_section:
        print("✅ Filter buttons section found!")
        
        # Find all filter buttons
        buttons = filter_section.find_all('button', class_='btn-filter')
        print(f"\nFound {len(buttons)} filter buttons:")
        
        for btn in buttons:
            # Extract button text and filter type
            text = btn.get_text(strip=True)
            filter_type = btn.get('data-filter', 'unknown')
            active = 'active' in btn.get('class', [])
            print(f"  - {text} (filter: {filter_type}) {'[ACTIVE]' if active else ''}")
        
        # Test filter URLs
        print("\n🔍 Testing filter URLs:")
        test_filters = [
            ('All', 'http://127.0.0.1:8890/signups'),
            ('Unpaid', 'http://127.0.0.1:8890/signups?payment_status=unpaid'),
            ('Paid', 'http://127.0.0.1:8890/signups?payment_status=paid'),
            ('Pending', 'http://127.0.0.1:8890/signups?status=pending'),
            ('Approved', 'http://127.0.0.1:8890/signups?status=approved')
        ]
        
        for name, url in test_filters:
            test_response = session.get(url)
            if test_response.status_code == 200:
                test_soup = BeautifulSoup(test_response.text, 'html.parser')
                # Check which button is active - need to find buttons with both classes
                active_btns = test_soup.find_all('button', class_='btn-filter')
                active_btn = None
                for btn in active_btns:
                    if 'active' in btn.get('class', []):
                        active_btn = btn
                        break
                        
                if active_btn:
                    active_text = active_btn.get_text(strip=True).split('(')[0].strip()
                    print(f"  {name} filter: ✅ Active button is '{active_text}'")
                else:
                    print(f"  {name} filter: ⚠️  No active button found")
            else:
                print(f"  {name} filter: ❌ Failed to load (status: {test_response.status_code})")
                
    else:
        print("❌ Filter buttons section NOT found!")
        print("\nSearching for any elements with 'filter' in class or id...")
        filter_elements = soup.find_all(attrs={'class': lambda x: x and 'filter' in str(x).lower()})
        filter_elements += soup.find_all(attrs={'id': lambda x: x and 'filter' in str(x).lower()})
        print(f"Found {len(filter_elements)} elements with 'filter'")
        
else:
    print(f"❌ Failed to access signups page: {response.status_code}")
    print(f"Response URL: {response.url}")