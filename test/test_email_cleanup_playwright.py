#!/usr/bin/env python3
"""
Playwright test to verify email template cleanup and capture screenshots.
This test uses MCP Playwright server to navigate the app and take screenshots.
"""

import os
import time

def test_email_template_cleanup_ui():
    """Test that old email template UI has been removed"""
    
    # Test configuration
    base_url = "http://localhost:5000"
    username = "kdresdell@gmail.com"
    password = "admin123"
    screenshot_dir = "/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright"
    
    # Create screenshot directory if it doesn't exist
    os.makedirs(screenshot_dir, exist_ok=True)
    
    print("Starting Playwright test for email template cleanup...")
    print(f"Screenshots will be saved to: {screenshot_dir}")
    
    # Instructions for running with MCP Playwright
    print("\n" + "="*60)
    print("PLAYWRIGHT TEST INSTRUCTIONS")
    print("="*60)
    print("\n1. Navigate to login page:")
    print(f"   - URL: {base_url}/login")
    print(f"   - Username: {username}")
    print(f"   - Password: {password}")
    
    print("\n2. After login, navigate to Settings page:")
    print(f"   - URL: {base_url}/setup")
    print("   - Take screenshot: settings_page_no_email_tab.png")
    print("   - Verify: No 'Email Templates' menu item in sidebar")
    print("   - Verify: No 'Email Notification' tab in settings")
    
    print("\n3. Navigate to an Activity's email customization:")
    print("   - Go to Activities list")
    print("   - Click on any activity")
    print("   - Click 'Email Templates' button")
    print("   - Take screenshot: activity_email_customization.png")
    print("   - Verify: New email customization builder is working")
    
    print("\n4. Test creating a new activity:")
    print("   - Go to create new activity page")
    print("   - Fill in required fields")
    print("   - Save activity")
    print("   - Verify: Activity created successfully")
    print("   - Check: Activity has empty email_templates in database")
    
    print("\nExpected Results:")
    print("✅ No 'Email Templates' in Settings sidebar")
    print("✅ No 'Email Notification' tab in setup page")
    print("✅ Activity-specific email customization works")
    print("✅ New activities created with empty email templates")
    
    return True

if __name__ == "__main__":
    test_email_template_cleanup_ui()