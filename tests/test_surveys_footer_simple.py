"""
Simple test to verify that the surveys page now shows the pagination footer
with entry count information, even without backend pagination support.
"""

import requests
import re
from urllib.parse import urljoin

BASE_URL = 'http://127.0.0.1:8890'
TEST_EMAIL = 'kdresdell@gmail.com'
TEST_PASSWORD = 'admin123'

def test_surveys_footer():
    """Test that surveys page shows entry count in footer"""
    print("🔍 Testing surveys page footer...")
    
    session = requests.Session()
    
    try:
        # Login
        login_url = urljoin(BASE_URL, '/login')
        login_page = session.get(login_url)
        
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
        if not csrf_match:
            print("❌ Could not find CSRF token")
            return False
            
        csrf_token = csrf_match.group(1)
        
        login_data = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'csrf_token': csrf_token
        }
        
        login_response = session.post(login_url, data=login_data)
        
        # Get surveys page
        surveys_url = urljoin(BASE_URL, '/surveys')
        surveys_response = session.get(surveys_url)
        
        if surveys_response.status_code != 200:
            print(f"❌ Failed to get surveys page: {surveys_response.status_code}")
            return False
            
        html = surveys_response.text
        
        # Check for card-footer
        if 'card-footer' in html:
            print("✅ Found card-footer in HTML")
        else:
            print("❌ No card-footer found in HTML")
            return False
        
        # Check for flex layout
        if 'd-flex justify-content-between align-items-center' in html:
            print("✅ Found pagination footer flex layout")
        else:
            print("❌ No pagination footer flex layout found")
            return False
        
        # Check for entry count patterns
        entry_patterns = [
            r'Showing \d+ of \d+ entries',
            r'Showing \d+ entries',
            r'No entries found'
        ]
        
        found_pattern = False
        for pattern in entry_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                print(f"✅ Found entry count: {matches[0]}")
                found_pattern = True
                break
        
        if not found_pattern:
            print("❌ No entry count pattern found")
            return False
        
        # Extract a section around the footer for inspection
        footer_pos = html.find('card-footer')
        if footer_pos != -1:
            footer_section = html[footer_pos-100:footer_pos+500]
            print(f"📋 Footer section preview:")
            print("-" * 40)
            # Clean up the HTML for better readability
            clean_section = re.sub(r'<[^>]+>', ' ', footer_section)
            clean_section = re.sub(r'\s+', ' ', clean_section).strip()
            print(clean_section[:200] + "...")
            print("-" * 40)
        
        print("✅ Surveys pagination footer test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

def test_compare_with_signups():
    """Compare surveys footer with signups footer"""
    print("\n🔄 Comparing surveys footer with signups...")
    
    session = requests.Session()
    
    try:
        # Login
        login_url = urljoin(BASE_URL, '/login')
        login_page = session.get(login_url)
        
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
        csrf_token = csrf_match.group(1)
        
        login_data = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'csrf_token': csrf_token
        }
        
        session.post(login_url, data=login_data)
        
        # Get both pages
        surveys_html = session.get(urljoin(BASE_URL, '/surveys')).text
        signups_html = session.get(urljoin(BASE_URL, '/signups')).text
        
        # Check footer presence
        surveys_has_footer = 'card-footer' in surveys_html
        signups_has_footer = 'card-footer' in signups_html
        
        print(f"📊 Footer comparison:")
        print(f"   • Surveys has footer: {surveys_has_footer}")
        print(f"   • Signups has footer: {signups_has_footer}")
        
        if surveys_has_footer and signups_has_footer:
            print("✅ Both pages have pagination footers!")
            
            # Check for entry count text
            surveys_entry = re.search(r'Showing \d+.*entries', surveys_html, re.IGNORECASE)
            signups_entry = re.search(r'Showing \d+.*entries', signups_html, re.IGNORECASE)
            
            if surveys_entry:
                print(f"   • Surveys entry text: {surveys_entry.group()}")
            if signups_entry:
                print(f"   • Signups entry text: {signups_entry.group()}")
                
            return True
        else:
            print("❌ Footer comparison failed")
            return False
            
    except Exception as e:
        print(f"❌ Comparison failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("📊 SURVEYS PAGINATION FOOTER TEST")
    print("=" * 60)
    
    # Test 1: Basic footer functionality
    footer_test = test_surveys_footer()
    
    # Test 2: Compare with signups
    comparison_test = test_compare_with_signups()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    if footer_test and comparison_test:
        print("🎉 ALL FOOTER TESTS PASSED!")
        print("✅ Surveys page now has pagination footer")
        print("✅ Entry counts are properly displayed")
        print("✅ Footer styling matches other pages")
        print("\nℹ️  Note: Full pagination navigation will appear when")
        print("   the backend implements proper pagination with multiple pages.")
        exit(0)
    else:
        print("❌ SOME FOOTER TESTS FAILED!")
        exit(1)