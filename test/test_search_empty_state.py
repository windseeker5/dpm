#!/usr/bin/env python3
"""
Test script to verify empty state fixes in search results
Tests that large white box doesn't appear when searching with no results
"""

import requests
from bs4 import BeautifulSoup
import sys

# Test configuration
BASE_URL = "http://127.0.0.1:8890"
LOGIN_URL = f"{BASE_URL}/login"
ACTIVITIES_URL = f"{BASE_URL}/activities"
PASSPORTS_URL = f"{BASE_URL}/passports"
SIGNUPS_URL = f"{BASE_URL}/signups"

# Login credentials
EMAIL = "kdresdell@gmail.com"
PASSWORD = "admin123"

def test_search_empty_state():
    """Test that empty state doesn't show large white box when searching"""
    
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
    
    all_tests_passed = True
    
    # Test Activities page search
    print("\n📄 Testing Activities page search...")
    search_url = f"{ACTIVITIES_URL}?q=nonexistentsearch"
    response = session.get(search_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for large empty state card
        empty_card = soup.find('div', class_='card-body')
        if empty_card and 'No activities found' in empty_card.text:
            # Check padding style
            style = empty_card.get('style', '')
            if 'padding: 3rem' in style or 'py-5' in ' '.join(empty_card.get('class', [])):
                print("❌ Activities: Large empty state card still appears during search")
                all_tests_passed = False
            else:
                print("✅ Activities: Empty state card padding reduced")
        else:
            # Should show "No entries found" in pagination area instead
            no_entries = soup.find(text="No entries found")
            if no_entries:
                print("✅ Activities: Shows 'No entries found' for search with no results")
            else:
                print("⚠️ Activities: Unexpected empty state behavior")
    else:
        print(f"❌ Activities page failed to load: {response.status_code}")
        all_tests_passed = False
    
    # Test Passports page search
    print("\n📄 Testing Passports page search...")
    search_url = f"{PASSPORTS_URL}?q=nonexistentsearch"
    response = session.get(search_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for large empty state card
        empty_card = soup.find('div', class_='card-body')
        if empty_card and 'No passports found' in empty_card.text:
            # Check padding style
            style = empty_card.get('style', '')
            if 'padding: 3rem' in style or 'py-5' in ' '.join(empty_card.get('class', [])):
                print("❌ Passports: Large empty state card still appears during search")
                all_tests_passed = False
            else:
                print("✅ Passports: Empty state card padding reduced")
        else:
            # Should show "No entries found" in pagination area instead
            no_entries = soup.find(text="No entries found")
            if no_entries:
                print("✅ Passports: Shows 'No entries found' for search with no results")
            else:
                print("⚠️ Passports: Unexpected empty state behavior")
    else:
        print(f"❌ Passports page failed to load: {response.status_code}")
        all_tests_passed = False
    
    # Test Actions column alignment
    print("\n🎨 Testing Actions column alignment...")
    
    for page_name, url in [("Activities", ACTIVITIES_URL), ("Passports", PASSPORTS_URL), ("Signups", SIGNUPS_URL)]:
        response = session.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find Actions header
            headers = soup.find_all('th')
            actions_header = None
            for header in headers:
                if 'Actions' in header.text:
                    actions_header = header
                    break
            
            if actions_header:
                classes = actions_header.get('class', [])
                if 'text-end' in classes:
                    print(f"✅ {page_name}: Actions column header is right-aligned")
                else:
                    print(f"❌ {page_name}: Actions column header is NOT right-aligned")
                    all_tests_passed = False
            else:
                print(f"⚠️ {page_name}: Actions column header not found")
        else:
            print(f"❌ {page_name} page failed to load: {response.status_code}")
            all_tests_passed = False
    
    if all_tests_passed:
        print("\n✨ All tests passed!")
    else:
        print("\n⚠️ Some tests failed")
    
    return all_tests_passed

if __name__ == "__main__":
    success = test_search_empty_state()
    sys.exit(0 if success else 1)