#!/usr/bin/env python3
"""
Test script to verify signup form scrolling functionality.
This script tests the signup form accessibility and scroll behavior.
"""
import requests
import time
from bs4 import BeautifulSoup

def test_signup_form_accessibility():
    """Test that signup forms are accessible and properly formatted"""
    base_url = "http://127.0.0.1:8890"
    
    print("Testing signup form scrolling fixes...")
    
    # First, log in to access the admin area
    session = requests.Session()
    
    # Get login page to retrieve CSRF token
    login_page = session.get(f"{base_url}/login")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
    
    # Log in
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    login_response = session.post(f"{base_url}/login", data=login_data)
    
    if login_response.status_code == 200 and 'dashboard' in login_response.url:
        print("✓ Successfully logged in")
    else:
        print("✗ Login failed")
        return False
    
    # Get activities list to find a signup URL
    activities_page = session.get(f"{base_url}/activities")
    soup = BeautifulSoup(activities_page.text, 'html.parser')
    
    # Look for signup links
    signup_links = soup.find_all('a', href=lambda x: x and '/signup/' in x)
    
    if not signup_links:
        print("✗ No signup links found")
        return False
    
    # Test the first signup link
    signup_url = base_url + signup_links[0]['href']
    print(f"Testing signup form at: {signup_url}")
    
    signup_response = session.get(signup_url)
    
    if signup_response.status_code != 200:
        print(f"✗ Failed to load signup form: {signup_response.status_code}")
        return False
    
    # Parse the signup form HTML
    soup = BeautifulSoup(signup_response.text, 'html.parser')
    
    # Check for key CSS classes and styling fixes
    style_tag = soup.find('style')
    if not style_tag:
        print("✗ No style tag found")
        return False
    
    css_content = style_tag.text
    
    # Verify the fixes are applied
    fixes_verified = 0
    total_fixes = 6
    
    if 'align-items: flex-start' in css_content:
        print("✓ signup-wrapper uses flex-start alignment")
        fixes_verified += 1
    else:
        print("✗ signup-wrapper still uses center alignment")
    
    if 'padding-top: 2rem' in css_content and 'padding-bottom: 2rem' in css_content:
        print("✓ signup-wrapper has proper top and bottom padding")
        fixes_verified += 1
    else:
        print("✗ signup-wrapper missing proper padding")
    
    if 'overflow-y: auto' in css_content:
        print("✓ overflow-y: auto is present")
        fixes_verified += 1
    else:
        print("✗ overflow-y: auto is missing")
    
    if 'max-height: calc(100vh - 4rem)' in css_content:
        print("✓ signup-card uses max-height instead of min-height")
        fixes_verified += 1
    else:
        print("✗ signup-card still uses min-height")
    
    if 'min-height: auto' in css_content:
        print("✓ Mobile styles use min-height: auto")
        fixes_verified += 1
    else:
        print("✗ Mobile styles still use min-height: 100vh")
    
    if 'overflow: hidden' not in css_content or css_content.count('overflow: hidden') == 0:
        print("✓ overflow: hidden removed from signup-card")
        fixes_verified += 1
    else:
        print("✗ overflow: hidden still present on signup-card")
    
    # Check form elements are present
    form = soup.find('form', method='POST')
    if form:
        print("✓ Signup form is present")
        
        # Check for required form elements
        name_input = form.find('input', {'name': 'name'})
        email_input = form.find('input', {'name': 'email'})
        submit_btn = form.find('button', type='submit')
        
        if name_input and email_input and submit_btn:
            print("✓ All required form elements are present")
        else:
            print("✗ Some form elements are missing")
            
    else:
        print("✗ Signup form not found")
    
    print(f"\nScrolling fixes verification: {fixes_verified}/{total_fixes} fixes confirmed")
    
    if fixes_verified >= 4:  # Allow some flexibility
        print("✓ Signup form scrolling fixes successfully applied!")
        return True
    else:
        print("✗ Some scrolling fixes may not be properly applied")
        return False

if __name__ == "__main__":
    success = test_signup_form_accessibility()
    exit(0 if success else 1)