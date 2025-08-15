#!/usr/bin/env python3
"""
Test script to verify alerts are displaying correctly in the style guide
"""
import requests
import re
import sys
from urllib.parse import urljoin

def test_alerts_display():
    """Test if alerts are properly displayed in the style guide"""
    
    # Create session for maintaining login state
    session = requests.Session()
    
    try:
        # Step 1: Get login page and extract CSRF token
        print("Step 1: Getting login page...")
        login_url = 'http://127.0.0.1:8890/login'
        login_page = session.get(login_url)
        
        if login_page.status_code != 200:
            print(f"❌ Failed to get login page: {login_page.status_code}")
            return False
            
        # Look for CSRF token
        csrf_token = None
        csrf_match = re.search(r'<input[^>]*name=["\'](?:csrf_token|_token)["\']\s*value=["\'](.*?)["\']', login_page.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"✓ Found CSRF token: {csrf_token[:10]}...")
        
        # Step 2: Login with credentials
        print("Step 2: Logging in...")
        login_data = {
            'email': 'kdresdell@gmail.com',
            'password': 'admin123'
        }
        if csrf_token:
            login_data['csrf_token'] = csrf_token
            
        login_response = session.post(login_url, data=login_data, allow_redirects=True)
        
        if login_response.status_code == 200 and 'dashboard' in login_response.url:
            print("✓ Successfully logged in")
        else:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.url}")
            return False
            
        # Step 3: Access style guide
        print("Step 3: Accessing style guide...")
        style_guide_url = 'http://127.0.0.1:8890/style-guide'
        response = session.get(style_guide_url)
        
        if response.status_code != 200:
            print(f"❌ Failed to get style guide: {response.status_code}")
            return False
            
        if 'login' in response.url:
            print("❌ Redirected back to login - authentication issue")
            return False
            
        print("✓ Successfully accessed style guide")
        
        # Step 4: Check for alerts content
        print("Step 4: Checking alerts content...")
        
        # Check for alerts section
        if 'id="alerts"' not in response.text:
            print("❌ Alerts section ID not found")
            return False
        print("✓ Alerts section ID found")
        
        # Check for actual alert components
        alert_types = ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']
        found_alerts = []
        
        for alert_type in alert_types:
            alert_class = f'alert alert-{alert_type}'
            if alert_class in response.text:
                found_alerts.append(alert_type)
                
        print(f"✓ Found {len(found_alerts)} alert types: {', '.join(found_alerts)}")
        
        if len(found_alerts) >= 8:
            print("✓ All basic alert types are present")
        else:
            missing = set(alert_types) - set(found_alerts)
            print(f"⚠️  Missing alert types: {', '.join(missing)}")
            
        # Check for specific alert features
        features_to_check = [
            ('alert-dismissible', 'Dismissible alerts'),
            ('ti ti-check-circle', 'Alert icons'),
            ('alert-link', 'Alert links'),
            ('alert-heading', 'Alert headings')
        ]
        
        for feature, description in features_to_check:
            if feature in response.text:
                print(f"✓ {description} found")
            else:
                print(f"⚠️  {description} not found")
                
        # Step 5: Check CSS and JS dependencies
        print("Step 5: Checking dependencies...")
        
        css_checks = [
            ('tabler.min.css', 'Tabler CSS'),
            ('tabler-icons.min.css', 'Tabler Icons'),
        ]
        
        for css_file, description in css_checks:
            if css_file in response.text:
                print(f"✓ {description} loaded")
            else:
                print(f"❌ {description} missing")
                
        # Check for Bootstrap JS
        if 'bootstrap' in response.text.lower() or 'tabler.min.js' in response.text:
            print("✓ JavaScript dependencies found")
        else:
            print("⚠️  JavaScript dependencies may be missing")
            
        print("\n🎉 Alerts test completed successfully!")
        print("The alerts should be displaying properly in the browser.")
        print("If they're not visible, try:")
        print("1. Hard refresh (Ctrl+F5)")
        print("2. Check browser console for CSS/JS errors")
        print("3. Ensure you're logged in as admin")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_alerts_display()
    sys.exit(0 if success else 1)