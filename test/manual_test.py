#!/usr/bin/env python3
"""
Manual verification of signup form changes using simple requests.
"""
import requests
import re

def test_signup_form_changes():
    """Test signup form visual changes by examining the HTML."""
    
    print("🔍 Testing signup form changes...")
    
    # Start a session
    session = requests.Session()
    
    try:
        # Login first
        login_data = {
            'email': 'kdresdell@gmail.com',
            'password': 'admin123'
        }
        
        login_response = session.post('http://127.0.0.1:8890/login', data=login_data)
        if login_response.status_code == 200:
            print("✅ Successfully logged in")
        else:
            print(f"❌ Login failed with status: {login_response.status_code}")
            return
        
        # Get the dashboard to find activities
        dashboard_response = session.get('http://127.0.0.1:8890/dashboard')
        
        # Look for signup links in the dashboard
        signup_links = re.findall(r'/signup/(\d+)', dashboard_response.text)
        
        if not signup_links:
            # Try activities page
            activities_response = session.get('http://127.0.0.1:8890/activities')
            signup_links = re.findall(r'/signup/(\d+)', activities_response.text)
        
        if signup_links:
            activity_id = signup_links[0]
            print(f"📋 Found activity with ID: {activity_id}")
            
            # Get the signup form
            signup_url = f'http://127.0.0.1:8890/signup/{activity_id}'
            signup_response = session.get(signup_url)
            
            if signup_response.status_code == 200:
                html_content = signup_response.text
                print("✅ Successfully loaded signup form")
                
                # Test 1: Check if desktop logo doesn't have d-none class
                if 'class="d-md-block"' in html_content and 'class="d-none d-md-block"' not in html_content:
                    print("✅ Desktop logo visibility fixed (d-none removed)")
                elif 'class="d-none d-md-block"' in html_content:
                    print("❌ Desktop logo still has d-none class")
                else:
                    print("⚠️  Could not verify logo class changes")
                
                # Test 2: Check if Anton font is used in CSS
                if "font-family: 'Anton', sans-serif;" in html_content:
                    print("✅ Anton font added to .signup-title")
                else:
                    print("❌ Anton font not found in .signup-title")
                
                # Test 3: Check if color classes are removed
                if 'text-success' not in re.search(r'<i class="ti ti-currency-dollar[^>]*>', html_content).group(0) if re.search(r'<i class="ti ti-currency-dollar[^>]*>', html_content) else False:
                    print("✅ text-success class removed from price icon")
                else:
                    print("❌ text-success class still present on price icon")
                
                if 'text-primary' not in re.search(r'<i class="ti ti-ticket[^>]*>', html_content).group(0) if re.search(r'<i class="ti ti-ticket[^>]*>', html_content) else False:
                    print("✅ text-primary class removed from sessions icon")
                else:
                    print("❌ text-primary class still present on sessions icon")
                
                print(f"\n🔗 You can manually test the form at: {signup_url}")
                print("🔗 Thank you page will be at: http://127.0.0.1:8890/signup/thank-you/[signup_id]")
                
            else:
                print(f"❌ Failed to load signup form: {signup_response.status_code}")
                
        else:
            print("❌ No activities found. Please create an activity first to test signup form.")
            print("💡 Go to: http://127.0.0.1:8890/activities and create an activity")
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_signup_form_changes()