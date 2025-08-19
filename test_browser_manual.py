#!/usr/bin/env python3

"""
Simple script to open the activity dashboard for manual testing of AJAX filtering
"""

import webbrowser
import os

def open_test_page():
    print("Opening activity dashboard for manual testing...")
    
    # Activity dashboard URL (you can change the ID if needed)
    test_urls = [
        "http://127.0.0.1:8890/login",  # Login first
        "http://127.0.0.1:8890/dashboard",  # Then dashboard
    ]
    
    print("URLs to test:")
    for i, url in enumerate(test_urls, 1):
        print(f"{i}. {url}")
    
    print("\nLogin credentials:")
    print("Email: kdresdell@gmail.com")
    print("Password: admin123")
    
    print("\nManual test steps:")
    print("1. Login using the credentials above")
    print("2. Navigate to an activity dashboard")
    print("3. Test filter buttons (passport and signup filters)")
    print("4. Check browser dev tools Network tab for AJAX requests")
    print("5. Verify that tables update without page reload")
    print("6. Check that URL updates with filter parameters")
    
    # Open login page
    webbrowser.open(test_urls[0])
    
    return test_urls

if __name__ == "__main__":
    urls = open_test_page()
    print(f"\nBrowser should now be open to: {urls[0]}")
    print("Follow the manual test steps above.")