#!/usr/bin/env python3
"""Test the activity dashboard to see what's actually happening"""

import requests
from bs4 import BeautifulSoup

# Create session for cookie persistence
session = requests.Session()

# Login
print("Logging in...")
login_data = {
    'email': 'kdresdell@gmail.com',
    'password': 'admin123'
}
response = session.post('http://127.0.0.1:8890/login', data=login_data)
print(f"Login status: {response.status_code}")

# Navigate to activity dashboard
print("\nFetching activity dashboard...")
response = session.get('http://127.0.0.1:8890/activity-dashboard/1')
print(f"Dashboard status: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for filter buttons
    print("\n=== Checking Filter Buttons ===")
    
    # Find passport filter buttons
    passport_filters = soup.find_all('a', class_='github-filter-btn')
    print(f"Found {len(passport_filters)} passport filter buttons")
    
    for button in passport_filters[:2]:  # Show first 2
        print(f"  - Text: {button.get_text(strip=True)}")
        print(f"    href: {button.get('href', 'No href')}")
        print(f"    onclick: {button.get('onclick', 'No onclick')}")
    
    # Check if JavaScript functions exist
    print("\n=== Checking JavaScript Functions ===")
    script_tags = soup.find_all('script')
    
    has_filter_passports = False
    has_filter_signups = False
    
    for script in script_tags:
        if script.string:
            if 'function filterPassports' in script.string:
                has_filter_passports = True
            if 'function filterSignups' in script.string:
                has_filter_signups = True
    
    print(f"filterPassports function exists: {has_filter_passports}")
    print(f"filterSignups function exists: {has_filter_signups}")
    
    # Test API endpoint
    print("\n=== Testing API Endpoint ===")
    api_response = session.get('http://127.0.0.1:8890/api/activity-dashboard-data/1?passport_filter=unpaid')
    print(f"API status: {api_response.status_code}")
    if api_response.status_code == 200:
        data = api_response.json()
        print(f"API success: {data.get('success', False)}")
        if 'passport_counts' in data:
            print(f"Passport counts: {data['passport_counts']}")
else:
    print("Failed to load dashboard")