#!/usr/bin/env python3
"""Check what template variables are available"""

import requests
from bs4 import BeautifulSoup
import re

# Login is not working in script, so let's just check the HTML
response = requests.get('http://127.0.0.1:8890/activity-dashboard/1')

if response.status_code == 200:
    # Look for template errors in HTML comments
    html = response.text
    
    # Check if we're getting a login redirect
    if 'login' in response.url or 'Login' in html[:500]:
        print("Getting redirected to login page")
    
    # Look for any Jinja2 errors
    if 'UndefinedError' in html or 'TemplateError' in html:
        print("Template error found in response!")
        # Extract error message
        error_match = re.search(r'(UndefinedError|TemplateError)[^<]*', html)
        if error_match:
            print(f"Error: {error_match.group(0)}")
    
    # Check for presence of key elements
    print("\nChecking for key elements:")
    print(f"- 'Your Activity Passport' found: {'Your Activity Passport' in html}")
    print(f"- 'github-filter' found: {'github-filter' in html}")
    print(f"- 'filterPassports' function found: {'filterPassports' in html}")
    print(f"- 'passes' variable referenced: {'passes' in html}")
    print(f"- 'all_passports' variable referenced: {'all_passports' in html}")
    
    # Check what's around the filter area
    passport_section = re.search(r'Your Activity Passport.*?</h2>(.*?)<table', html, re.DOTALL)
    if passport_section:
        content = passport_section.group(1)[:500]
        print(f"\nContent after 'Your Activity Passport': {content[:200]}...")
    else:
        print("\n'Your Activity Passport' section not found properly")
else:
    print(f"Failed to load page: {response.status_code}")