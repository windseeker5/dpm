#!/usr/bin/env python3
"""
Test Settings Submenu Functionality via HTTP simulation
"""

import requests
import re
import json
import time

def extract_csrf_token(html):
    """Extract CSRF token from HTML"""
    match = re.search(r'name="csrf_token".*?value="([^"]+)"', html)
    return match.group(1) if match else None

def test_submenu_functionality():
    """Test the submenu functionality by analyzing the HTML and JavaScript"""
    
    session = requests.Session()
    
    print("=== TESTING SETTINGS SUBMENU FUNCTIONALITY ===\n")
    
    # Step 1: Get login page and extract CSRF
    print("1. Getting login page...")
    login_page = session.get('http://127.0.0.1:8890/login')
    csrf_token = extract_csrf_token(login_page.text)
    
    if not csrf_token:
        print("❌ Could not extract CSRF token")
        return False
    print("✅ CSRF token extracted")
    
    # Step 2: Login
    print("\n2. Logging in...")
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    
    login_response = session.post('http://127.0.0.1:8890/login', data=login_data)
    if login_response.status_code != 200 and login_response.status_code != 302:
        print(f"❌ Login failed with status {login_response.status_code}")
        return False
    print("✅ Login successful")
    
    # Step 3: Get settings page
    print("\n3. Getting settings page...")
    settings_response = session.get('http://127.0.0.1:8890/setup')
    if settings_response.status_code != 200:
        print(f"❌ Settings page failed with status {settings_response.status_code}")
        return False
    
    html = settings_response.text
    print("✅ Settings page loaded")
    
    # Step 4: Analyze the submenu structure
    print("\n4. Analyzing submenu structure...")
    
    # Check for required elements
    checks = {
        'Settings submenu exists': 'id="settings-submenu"' in html,
        'Submenu has show class': 'nav-submenu show' in html,
        'Data-tab attributes present': len(re.findall(r'data-tab="([^"]*)"', html)) >= 5,
        'Tab panes exist': len(re.findall(r'id="tab-([^"]*)"', html)) >= 5,
        'showSettingsTab function': 'window.showSettingsTab' in html,
        'preventDefault call': 'e.preventDefault()' in html and 'window.location.pathname === \'/setup\'' in html,
        'Event listeners': 'addEventListener' in html,
    }
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}: {result}")
    
    # Step 5: Extract submenu links and their data-tab values
    print("\n5. Extracting submenu links...")
    submenu_links = re.findall(r'<a href="/setup" class="nav-link" data-tab="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
    
    if submenu_links:
        print("Found submenu links:")
        for tab_id, content in submenu_links:
            # Extract the text content (remove HTML tags)
            text = re.sub(r'<[^>]*>', '', content).strip()
            text = re.sub(r'\s+', ' ', text)  # Clean up whitespace
            print(f"  - {tab_id}: {text}")
    else:
        print("❌ No submenu links found")
        return False
    
    # Step 6: Extract available tab panes
    print("\n6. Extracting tab panes...")
    tab_panes = re.findall(r'<div class="tab-pane[^"]*"[^>]*id="tab-([^"]*)"', html)
    
    if tab_panes:
        print("Found tab panes:")
        for tab_id in tab_panes:
            print(f"  - {tab_id}")
    else:
        print("❌ No tab panes found")
        return False
    
    # Step 7: Check if submenu tabs match available panes
    print("\n7. Verifying tab consistency...")
    submenu_tabs = set([link[0] for link in submenu_links])
    main_tab_panes = set([tab for tab in tab_panes if not tab.startswith('pass_') and not tab.startswith('payment_') and tab != 'signup' and tab != 'survey_invitation'])
    
    print(f"Submenu tabs: {submenu_tabs}")
    print(f"Main tab panes: {main_tab_panes}")
    
    missing_panes = submenu_tabs - main_tab_panes
    extra_panes = main_tab_panes - submenu_tabs
    
    if missing_panes:
        print(f"❌ Missing tab panes: {missing_panes}")
    if extra_panes:
        print(f"⚠️  Extra tab panes: {extra_panes}")
    
    if not missing_panes:
        print("✅ All submenu tabs have corresponding panes")
    
    # Step 8: Check JavaScript logic
    print("\n8. Analyzing JavaScript logic...")
    
    # Extract the key JavaScript functions
    js_patterns = {
        'Tab switching function exists': r'function showTab\(tabName\)',
        'Global assignment': r'window\.showSettingsTab = showTab',
        'Event listener setup': r'settingsSubmenuLinks\.forEach\(link => \{',
        'Prevent default logic': r'if \(window\.location\.pathname === \'/setup\'\)',
        'Active state management': r'settingsSubmenuLinks\.forEach\(l => l\.classList\.remove\(\'active\'\)\)',
        'Initial tab load': r'showTab\(storedTab\)',
    }
    
    for description, pattern in js_patterns.items():
        found = bool(re.search(pattern, html))
        status = "✅" if found else "❌"
        print(f"{status} {description}: {found}")
    
    # Step 9: Summary
    print("\n9. SUMMARY")
    all_checks = list(checks.values()) + [not missing_panes] + [bool(re.search(pattern, html)) for pattern in js_patterns.values()]
    passed = sum(all_checks)
    total = len(all_checks)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The submenu should work correctly.")
        print("\n📋 MANUAL TEST INSTRUCTIONS:")
        print("1. Open http://127.0.0.1:8890/login")
        print("2. Login with: kdresdell@gmail.com / admin123")
        print("3. You should automatically be redirected or go to /setup")
        print("4. Look at the sidebar - Settings should be expanded with submenu items")
        print("5. Click different submenu items (Organization, Email Settings, etc.)")
        print("6. Verify the content changes instantly without page reload")
        print("7. Check that the active submenu item is highlighted")
        
        return True
    else:
        print(f"❌ Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = test_submenu_functionality()
    exit(0 if success else 1)