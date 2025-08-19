#!/usr/bin/env python3
"""
Debug Settings Submenu - Check JavaScript Loading
"""

import requests
import re
import sys

def test_submenu_javascript():
    """Test if the submenu JavaScript is properly loaded"""
    
    # Create session and login
    session = requests.Session()
    
    # Get login page first to get CSRF token
    print("Getting login page...")
    login_page = session.get('http://127.0.0.1:8890/login')
    
    # Extract CSRF token
    csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    # Login with CSRF token
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    
    print("Logging in...")
    login_response = session.post('http://127.0.0.1:8890/login', data=login_data)
    
    if login_response.status_code != 200:
        print(f"Login failed with status {login_response.status_code}")
        return False
    
    # Get the settings page
    print("Getting settings page...")
    settings_response = session.get('http://127.0.0.1:8890/setup')
    
    if settings_response.status_code != 200:
        print(f"Settings page failed with status {settings_response.status_code}")
        return False
    
    html_content = settings_response.text
    
    # Check for required elements
    print("\nChecking page elements:")
    
    # 1. Check if submenu exists in HTML
    submenu_exists = '#settings-submenu' in html_content
    print(f"✓ Settings submenu in HTML: {submenu_exists}")
    
    # 2. Check for data-tab attributes
    data_tab_count = len(re.findall(r'data-tab="[^"]*"', html_content))
    print(f"✓ data-tab attributes found: {data_tab_count}")
    
    # 3. Check for tab panes
    tab_panes = re.findall(r'id="tab-([^"]*)"', html_content)
    print(f"✓ Tab panes found: {tab_panes}")
    
    # 4. Check for JavaScript functions
    js_functions_to_check = [
        'showSettingsTab',
        'localStorage.setItem',
        'data-tab',
        'preventDefault'
    ]
    
    print("\nChecking JavaScript:")
    for func in js_functions_to_check:
        exists = func in html_content
        print(f"✓ {func}: {exists}")
    
    # 5. Look for potential issues
    print("\nPotential Issues:")
    
    # Check for parent.document references (should not exist)
    parent_refs = 'parent.document' in html_content
    if parent_refs:
        print("⚠️  Found 'parent.document' references - this could cause issues")
    else:
        print("✓ No 'parent.document' references found")
    
    # Check for event listeners
    event_listeners = html_content.count('addEventListener')
    print(f"✓ Event listeners found: {event_listeners}")
    
    # Extract and show the submenu HTML structure
    print("\nSubmenu HTML structure:")
    submenu_match = re.search(r'<div[^>]*id="settings-submenu"[^>]*>.*?</div>\s*</div>', html_content, re.DOTALL)
    if submenu_match:
        submenu_html = submenu_match.group(0)
        # Pretty print the submenu structure
        lines = submenu_html.split('\n')
        for i, line in enumerate(lines[:20]):  # First 20 lines
            if 'data-tab=' in line:
                print(f"  → {line.strip()}")
    
    return True

if __name__ == "__main__":
    success = test_submenu_javascript()
    if success:
        print("\n✅ Page loaded successfully. Check above for any issues.")
    else:
        print("\n❌ Failed to load page properly.")
        sys.exit(1)