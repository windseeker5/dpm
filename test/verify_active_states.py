#!/usr/bin/env python3
"""
Verify that the submenu shows correct active states
"""

import requests
import re

def test_active_states():
    """Test that submenu active states work correctly"""
    
    # Login and get session
    session = requests.Session()
    
    # Get login page and extract CSRF
    login_page = session.get('http://127.0.0.1:8890/login')
    csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    # Login
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    session.post('http://127.0.0.1:8890/login', data=login_data)
    
    # Get settings page
    response = session.get('http://127.0.0.1:8890/setup')
    html = response.text
    
    print("VERIFYING ACTIVE STATES")
    print("="*30)
    
    # Check default active tab
    active_tab_match = re.search(r'<div class="tab-pane[^"]*active[^"]*"[^>]*id="tab-([^"]*)"', html)
    if active_tab_match:
        active_tab = active_tab_match.group(1)
        print(f"✅ Default active tab: {active_tab}")
    else:
        print("❌ No active tab found")
        return False
    
    # Check if submenu is expanded (should be on settings page)
    submenu_expanded = 'nav-submenu show' in html
    print(f"✅ Submenu expanded: {submenu_expanded}")
    
    # Check that Settings parent nav item has active class
    settings_nav_active = re.search(r'nav-link[^>]*active[^>]*>.*?<i class="nav-icon ti ti-settings"', html, re.DOTALL)
    print(f"✅ Settings nav item active: {bool(settings_nav_active)}")
    
    # Verify JavaScript sets up correctly
    js_setup_correct = (
        'window.showSettingsTab = showTab' in html and
        'showTab(storedTab)' in html and
        'settings-active-tab' in html
    )
    print(f"✅ JavaScript setup correct: {js_setup_correct}")
    
    print()
    print("SUBMENU VISUAL STATE:")
    print("-"*20)
    
    # Extract each submenu link and check if it would be highlighted
    submenu_links = re.findall(r'<a href="/setup" class="nav-link" data-tab="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
    
    for tab_id, link_html in submenu_links:
        # Extract the display text
        text = re.sub(r'<[^>]*>', '', link_html).strip()
        text = ' '.join(text.split())  # Clean whitespace
        
        # The active state will be set by JavaScript, not server-side HTML
        # So we just show which tab should be active
        is_default = (tab_id == active_tab)
        status = "🟦" if is_default else "⬜"
        print(f"{status} {text} ({tab_id})")
    
    print()
    print("FINAL VERIFICATION:")
    print("- Default tab should be 'admins' (Admin Accounts)")
    print("- Submenu should be visible and expanded") 
    print("- JavaScript should handle active state switching")
    print("- No page reloads should occur on submenu clicks")
    
    # All checks
    all_good = (
        active_tab == 'admins' and
        submenu_expanded and
        bool(settings_nav_active) and
        js_setup_correct
    )
    
    if all_good:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("The settings submenu is ready for use!")
        return True
    else:
        print("\n⚠️  Some verifications failed - check above")
        return False

if __name__ == "__main__":
    success = test_active_states()
    exit(0 if success else 1)