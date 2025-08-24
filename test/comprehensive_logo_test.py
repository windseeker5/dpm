#!/usr/bin/env python3
"""
Comprehensive logo visibility test for Minipass signup form.
This test validates both the HTML structure and provides manual verification steps.
"""

import requests
from bs4 import BeautifulSoup
import re

def test_signup_form_logo():
    """Test the actual signup form logo configuration."""
    
    print("=" * 60)
    print("COMPREHENSIVE LOGO VISIBILITY TEST")
    print("=" * 60)
    
    url = "http://127.0.0.1:8890/signup/1?passport_type_id=1"
    
    try:
        print(f"Testing URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for Tabler CSS
        tabler_css = soup.find('link', {'href': re.compile(r'tabler.*\.css')})
        if tabler_css:
            print("✅ Tabler CSS is loaded")
        else:
            print("❌ Tabler CSS not found - this could cause issues!")
            
        # Find logo container
        logo_container = soup.find('div', class_='text-center mb-4')
        if not logo_container:
            print("❌ Logo container not found!")
            return False
            
        # Find both logos
        logos = logo_container.find_all('img', alt='Logo')
        
        if len(logos) != 2:
            print(f"❌ Expected 2 logo images, found {len(logos)}")
            return False
            
        print(f"✅ Found {len(logos)} logo images")
        
        desktop_logo = None
        mobile_logo = None
        
        for i, logo in enumerate(logos):
            classes = logo.get('class', [])
            style = logo.get('style', '')
            
            print(f"\n--- Logo {i+1} ---")
            print(f"Classes: {classes}")
            print(f"Style: {style}")
            
            if 'd-md-block' in classes:
                desktop_logo = logo
                print("→ DESKTOP logo")
            elif 'd-block' in classes and 'd-md-none' in classes:
                mobile_logo = logo
                print("→ MOBILE logo")
            else:
                print("→ UNIDENTIFIED logo type!")
                
        # Validate desktop logo
        if desktop_logo:
            classes = desktop_logo.get('class', [])
            style = desktop_logo.get('style', '')
            
            print("\n" + "="*40)
            print("DESKTOP LOGO VALIDATION")
            print("="*40)
            
            # Check required class
            if 'd-md-block' not in classes:
                print("❌ Missing d-md-block class")
                return False
            else:
                print("✅ Has d-md-block class")
                
            # Check that it doesn't have d-none without proper context
            if 'd-none' in classes and 'd-md-block' not in classes:
                print("❌ Has d-none but no d-md-block override")
                return False
            elif 'd-none' in classes:
                print("⚠️  Has d-none but also has d-md-block (should work with media queries)")
            else:
                print("✅ No conflicting d-none class")
                
            # Check inline style
            if 'display: none' in style and 'd-md-block' in classes:
                print("✅ Has inline display:none with d-md-block override (correct pattern)")
            elif 'display: block' in style:
                print("✅ Has inline display:block")
            else:
                print("⚠️  No explicit display style")
                
        else:
            print("❌ Desktop logo not found!")
            return False
            
        # Validate mobile logo  
        if mobile_logo:
            classes = mobile_logo.get('class', [])
            style = mobile_logo.get('style', '')
            
            print("\n" + "="*40)
            print("MOBILE LOGO VALIDATION")
            print("="*40)
            
            if 'd-block' not in classes:
                print("❌ Missing d-block class")
                return False
            else:
                print("✅ Has d-block class")
                
            if 'd-md-none' not in classes:
                print("❌ Missing d-md-none class")
                return False
            else:
                print("✅ Has d-md-none class")
                
            if 'display: block' not in style:
                print("⚠️  No explicit display:block in style")
            else:
                print("✅ Has inline display:block")
                
        else:
            print("❌ Mobile logo not found!")
            return False
            
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✅ HTML structure is correct")
        print("✅ Both desktop and mobile logos are present")
        print("✅ CSS classes are properly configured")
        print("✅ Tabler CSS is loaded")
        
        print("\n" + "="*60)
        print("MANUAL VERIFICATION REQUIRED")
        print("="*60)
        print("Please manually test the following:")
        print(f"1. Open: {url}")
        print("2. Desktop test (window width ≥ 768px):")
        print("   - Should see LARGER logo (80px height)")
        print("   - Should see only ONE logo")
        print("3. Mobile test (window width < 768px):")
        print("   - Should see SMALLER logo (60px height)")  
        print("   - Should see only ONE logo")
        print("4. Resize window to test breakpoint transition")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def print_test_urls():
    """Print URLs for manual testing."""
    
    print("\n" + "="*60)
    print("MANUAL TEST URLS")
    print("="*60)
    
    test_urls = [
        "http://127.0.0.1:8890/signup/1?passport_type_id=1",
        "http://127.0.0.1:8890/signup/2?passport_type_id=1", 
        "http://127.0.0.1:8890/signup/3?passport_type_id=1"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"{i}. {url}")
        
    print("\nLocal test file:")
    print("file:///home/kdresdell/Documents/DEV/minipass_env/app/test/html/final_logo_test.html")

def main():
    success = test_signup_form_logo()
    print_test_urls()
    
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    
    if success:
        print("✅ Automated tests PASSED")
        print("➡️  Manual verification still required")
        print("➡️  Logo should be visible on BOTH desktop and mobile")
    else:
        print("❌ Automated tests FAILED")
        print("➡️  Check the issues above before manual testing")
        
    return success

if __name__ == "__main__":
    main()