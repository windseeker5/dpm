#!/usr/bin/env python3
"""
Test script to verify activities page styling fixes
Tests that numbers are shown as regular text, not badges
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

def test_activities_styling():
    """Test that activities page uses correct styling (regular text not badges)"""
    
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
    
    # Step 3: Parse HTML and check styling
    print("🎨 Checking styling...")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the table body
    tbody = soup.find('tbody')
    if not tbody:
        print("❌ Table body not found")
        return False
    
    # Find all rows
    rows = tbody.find_all('tr')
    if len(rows) == 0:
        print("⚠️ No activities found to test")
        return True
    
    # Check first row for proper styling
    first_row = rows[0]
    cells = first_row.find_all('td')
    
    tests_passed = True
    
    # Check Type column (should be text-muted, not badge)
    type_cell = cells[2] if len(cells) > 2 else None
    if type_cell:
        type_span = type_cell.find('span')
        if type_span:
            classes = type_span.get('class', [])
            if 'badge' in classes:
                print("❌ Type column still uses badge styling")
                tests_passed = False
            elif 'text-muted' in classes:
                print("✅ Type column uses regular gray text")
            else:
                print("⚠️ Type column has unexpected styling")
    
    # Check Status column (should still be a badge)
    status_cell = cells[3] if len(cells) > 3 else None
    if status_cell:
        status_span = status_cell.find('span')
        if status_span:
            classes = status_span.get('class', [])
            if 'badge' in classes:
                print("✅ Status column correctly uses badge styling")
            else:
                print("❌ Status column should use badge styling")
                tests_passed = False
    
    # Check # Types column (should be text-muted, not badge)
    types_cell = cells[4] if len(cells) > 4 else None
    if types_cell:
        types_span = types_cell.find('span')
        if types_span:
            classes = types_span.get('class', [])
            if 'badge' in classes:
                print("❌ # Types column still uses badge styling")
                tests_passed = False
            elif 'text-muted' in classes:
                print("✅ # Types column uses regular gray text")
    
    # Check Active column (should be text-muted, not badge)
    active_cell = cells[5] if len(cells) > 5 else None
    if active_cell:
        active_span = active_cell.find('span')
        if active_span:
            classes = active_span.get('class', [])
            if 'badge' in classes:
                print("❌ Active column still uses badge styling")
                tests_passed = False
            elif 'text-muted' in classes:
                print("✅ Active column uses regular gray text")
    
    # Check Signups column (should be text-muted, not badge)
    signups_cell = cells[6] if len(cells) > 6 else None
    if signups_cell:
        signups_span = signups_cell.find('span')
        if signups_span:
            classes = signups_span.get('class', [])
            if 'badge' in classes:
                print("❌ Signups column still uses badge styling")
                tests_passed = False
            elif 'text-muted' in classes:
                print("✅ Signups column uses regular gray text")
    
    # Check Revenue column (should be text-muted, not text-success)
    revenue_cell = cells[7] if len(cells) > 7 else None
    if revenue_cell:
        revenue_span = revenue_cell.find('span')
        if revenue_span:
            classes = revenue_span.get('class', [])
            if 'text-success' in classes or 'fw-bold' in classes:
                print("❌ Revenue column still uses green/bold styling")
                tests_passed = False
            elif 'text-muted' in classes:
                print("✅ Revenue column uses regular gray text")
    
    # Check for activity images
    activity_name_cell = cells[1] if len(cells) > 1 else None
    if activity_name_cell:
        avatar = activity_name_cell.find('span', class_='avatar')
        if avatar:
            style = avatar.get('style', '')
            if 'background-image' in style and 'activity_images' in style:
                print("✅ Activity image path correctly uses activity_images subdirectory")
            elif 'background-image' in style:
                print("⚠️ Activity has image but path may be incorrect")
            else:
                print("ℹ️ Activity using fallback avatar (no image)")
    
    if tests_passed:
        print("\n✨ All styling tests passed!")
    else:
        print("\n⚠️ Some styling issues remain")
    
    return tests_passed

if __name__ == "__main__":
    success = test_activities_styling()
    sys.exit(0 if success else 1)