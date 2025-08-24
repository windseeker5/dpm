#!/usr/bin/env python3
"""
Test script to verify logo visibility on signup form.
This is a simple verification script that checks the HTML output.
"""

import requests
from bs4 import BeautifulSoup
import re

def test_logo_visibility():
    """Test that the logo is properly configured for desktop and mobile views."""
    
    print("Testing logo visibility on signup form...")
    
    # Test the signup form page
    url = "http://127.0.0.1:8890/signup/1?passport_type_id=1"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all logo images
        logo_images = soup.find_all('img', {'alt': 'Logo'})
        
        print(f"Found {len(logo_images)} logo images")
        
        desktop_logo = None
        mobile_logo = None
        
        for img in logo_images:
            classes = img.get('class', [])
            style = img.get('style', '')
            
            print(f"Image classes: {classes}")
            print(f"Image style: {style}")
            
            if 'd-md-block' in classes:
                desktop_logo = img
                print("→ This is the DESKTOP logo")
            elif 'd-block' in classes and 'd-md-none' in classes:
                mobile_logo = img
                print("→ This is the MOBILE logo")
            
            print("---")
        
        # Check desktop logo configuration
        if desktop_logo:
            desktop_classes = desktop_logo.get('class', [])
            desktop_style = desktop_logo.get('style', '')
            
            print("DESKTOP LOGO ANALYSIS:")
            print(f"Classes: {desktop_classes}")
            print(f"Style: {desktop_style}")
            
            # Check for conflicting classes
            has_d_none = 'd-none' in desktop_classes
            has_d_md_block = 'd-md-block' in desktop_classes
            has_display_none_inline = 'display: none' in desktop_style
            
            if has_d_none and not has_d_md_block:
                print("❌ ERROR: Desktop logo has d-none but no d-md-block!")
                return False
            elif has_d_md_block:
                print("✅ Desktop logo has d-md-block - should show on desktop")
            
            if has_display_none_inline and has_d_md_block:
                print("✅ Desktop logo uses inline display:none with d-md-block override")
            
        else:
            print("❌ ERROR: No desktop logo found!")
            return False
        
        # Check mobile logo configuration
        if mobile_logo:
            mobile_classes = mobile_logo.get('class', [])
            print("MOBILE LOGO ANALYSIS:")
            print(f"Classes: {mobile_classes}")
            
            if 'd-block' in mobile_classes and 'd-md-none' in mobile_classes:
                print("✅ Mobile logo correctly configured")
            else:
                print("❌ ERROR: Mobile logo not properly configured!")
                return False
        else:
            print("❌ ERROR: No mobile logo found!")
            return False
        
        print("✅ Logo configuration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_logo_visibility()