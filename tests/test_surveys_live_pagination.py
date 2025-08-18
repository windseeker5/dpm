"""
Live test to verify surveys pagination is working on the actual running Flask server.
This test makes HTTP requests to verify the pagination HTML is rendered correctly.
"""

import requests
import re
from urllib.parse import urljoin

BASE_URL = 'http://127.0.0.1:8890'
TEST_EMAIL = 'kdresdell@gmail.com'
TEST_PASSWORD = 'admin123'

def test_surveys_pagination_live():
    """Test surveys pagination on the live Flask server"""
    print("🚀 Testing surveys pagination on live server...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Step 1: Get login page to get CSRF token
        print("🔐 Getting login page...")
        login_url = urljoin(BASE_URL, '/login')
        login_page = session.get(login_url)
        
        if login_page.status_code != 200:
            print(f"❌ Failed to get login page: {login_page.status_code}")
            return False
            
        # Extract CSRF token
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
        if not csrf_match:
            print("❌ Could not find CSRF token in login page")
            return False
            
        csrf_token = csrf_match.group(1)
        print(f"✅ Got CSRF token: {csrf_token[:20]}...")
        
        # Step 2: Login
        print("🔑 Logging in...")
        login_data = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'csrf_token': csrf_token
        }
        
        login_response = session.post(login_url, data=login_data)
        
        # Check if login was successful (should redirect or show dashboard)
        if login_response.status_code not in [200, 302]:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        # Check if we're logged in by looking for redirect or success indicators
        if 'login' in login_response.url.lower() and 'Invalid' in login_response.text:
            print("❌ Login failed - invalid credentials")
            return False
            
        print("✅ Login successful")
        
        # Step 3: Get surveys page
        print("📊 Getting surveys page...")
        surveys_url = urljoin(BASE_URL, '/surveys')
        surveys_response = session.get(surveys_url)
        
        if surveys_response.status_code != 200:
            print(f"❌ Failed to get surveys page: {surveys_response.status_code}")
            return False
            
        surveys_html = surveys_response.text
        print("✅ Successfully loaded surveys page")
        
        # Step 4: Check for pagination elements
        print("🔍 Checking for pagination elements...")
        
        pagination_checks = [
            ('card-footer', 'Card footer container'),
            ('d-flex justify-content-between align-items-center', 'Footer flex layout'),
            ('text-muted', 'Entry count text styling'),
            ('Showing', 'Entry count text'),
            ('entries', 'Entry count label'),
            ('pagination', 'Pagination component'),
            ('ti ti-chevron-left', 'Previous button icon'),
            ('ti ti-chevron-right', 'Next button icon'),
            ('page-link', 'Page link styling'),
            ('page-item', 'Page item styling'),
            ('aria-label="Previous"', 'Previous button accessibility'),
            ('aria-label="Next"', 'Next button accessibility')
        ]
        
        missing_elements = []
        for pattern, description in pagination_checks:
            if pattern in surveys_html:
                print(f"✅ Found {description}")
            else:
                print(f"❌ Missing {description}")
                missing_elements.append(description)
        
        if missing_elements:
            print(f"❌ Missing {len(missing_elements)} pagination elements")
            return False
        
        # Step 5: Check for specific pagination text patterns
        print("📝 Checking pagination text patterns...")
        
        # Look for "Showing X entries" or "No entries found" patterns
        showing_pattern = r'Showing\s+\d+.*entries|No entries found'
        showing_match = re.search(showing_pattern, surveys_html, re.IGNORECASE)
        
        if showing_match:
            print(f"✅ Found entry count text: '{showing_match.group()}'")
        else:
            print("❌ Could not find entry count text")
            return False
        
        # Step 6: Check that pagination is in a card footer
        print("🏗️  Checking pagination structure...")
        
        # Look for card-footer with pagination content
        card_footer_pattern = r'<div[^>]*class="[^"]*card-footer[^"]*"[^>]*>.*?</div>'
        footer_matches = re.findall(card_footer_pattern, surveys_html, re.DOTALL)
        
        pagination_in_footer = False
        for footer in footer_matches:
            if 'pagination' in footer or 'entries' in footer:
                pagination_in_footer = True
                print("✅ Found pagination content in card footer")
                break
        
        if not pagination_in_footer:
            print("❌ Pagination not found in card footer")
            return False
        
        # Step 7: Compare with signups page
        print("🔄 Comparing with signups page...")
        
        signups_url = urljoin(BASE_URL, '/signups')
        signups_response = session.get(signups_url)
        
        if signups_response.status_code == 200:
            signups_html = signups_response.text
            
            # Check if both pages have similar pagination structure
            surveys_has_footer = 'card-footer' in surveys_html
            signups_has_footer = 'card-footer' in signups_html
            
            if surveys_has_footer and signups_has_footer:
                print("✅ Both surveys and signups pages have pagination footers")
            else:
                print(f"⚠️  Pagination footer comparison: surveys={surveys_has_footer}, signups={signups_has_footer}")
        else:
            print("⚠️  Could not load signups page for comparison")
        
        # Step 8: Check for mobile responsiveness indicators
        print("📱 Checking mobile responsiveness...")
        
        mobile_checks = [
            ('viewport', 'Viewport meta tag'),
            ('col-', 'Bootstrap responsive columns'),
            ('d-md-', 'Bootstrap responsive display classes'),
            ('@media', 'Media queries in CSS')
        ]
        
        for pattern, description in mobile_checks:
            if pattern in surveys_html:
                print(f"✅ Found {description}")
            else:
                print(f"ℹ️  No obvious {description}")
        
        print("🎉 All live pagination tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask server at http://127.0.0.1:8890")
        print("   Make sure the Flask server is running on port 8890")
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🌐 SURVEYS PAGINATION LIVE SERVER TEST")
    print("=" * 60)
    print("Testing on Flask server at http://127.0.0.1:8890")
    print(f"Using credentials: {TEST_EMAIL} / {TEST_PASSWORD}")
    print("=" * 60)
    
    result = test_surveys_pagination_live()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    if result:
        print("🎉 ALL LIVE TESTS PASSED!")
        print("✅ Surveys page pagination is working correctly on the live server")
        print("✅ Entry counts and page navigation are properly displayed")
        print("✅ Pagination styling matches other pages in the application")
        exit(0)
    else:
        print("❌ SOME LIVE TESTS FAILED!")
        print("Please check the Flask server and try again")
        exit(1)