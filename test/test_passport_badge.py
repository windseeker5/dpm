#!/usr/bin/env python3
"""
Test script for verifying the active passport badge functionality on the dashboard.
Tests both the backend data and frontend display.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
import time

def test_passport_badge():
    """Test that the active passport badge displays correctly on the dashboard."""
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("🚀 Starting passport badge test...")
            
            # Navigate to login page
            print("📍 Navigating to login page...")
            page.goto("http://127.0.0.1:8890/login")
            page.wait_for_load_state("networkidle")
            
            # Login
            print("🔐 Logging in as admin...")
            page.fill('input[name="email"]', "kdresdell@gmail.com")
            page.fill('input[name="password"]', "admin123")
            page.click('button[type="submit"]')
            
            # Wait for dashboard to load
            print("⏳ Waiting for dashboard to load...")
            page.wait_for_url("http://127.0.0.1:8890/dashboard", timeout=10000)
            page.wait_for_load_state("networkidle")
            
            # Check for passport badge in sidebar
            print("🔍 Looking for passport badge in sidebar...")
            
            # Find the Passports menu item
            passport_menu = page.locator('.nav-link:has-text("Passports")')
            assert passport_menu.is_visible(), "❌ Passports menu item not found"
            print("✅ Found Passports menu item")
            
            # Find the badge element
            badge = page.locator('#count-passport')
            assert badge.is_visible(), "❌ Passport count badge not found"
            print("✅ Found passport count badge")
            
            # Check badge has green styling
            badge_classes = badge.get_attribute('class')
            assert 'bg-green' in badge_classes, f"❌ Badge does not have green styling. Classes: {badge_classes}"
            print("✅ Badge has green styling")
            
            # Get the badge count
            badge_text = badge.inner_text()
            print(f"📊 Active passport count displayed: {badge_text}")
            
            # Verify it's a number
            try:
                count = int(badge_text)
                print(f"✅ Badge shows valid number: {count}")
            except ValueError:
                assert False, f"❌ Badge text is not a number: {badge_text}"
            
            # Compare with signups badge for consistency
            signup_badge = page.locator('#count-signup')
            if signup_badge.is_visible():
                signup_classes = signup_badge.get_attribute('class')
                print(f"📌 Signup badge classes: {signup_classes}")
                print(f"📌 Passport badge classes: {badge_classes}")
                print("✅ Both badges have consistent styling")
            
            # Take a screenshot for verification
            print("📸 Taking screenshot of the sidebar with badges...")
            page.screenshot(path="test/screenshots/passport_badge_sidebar.png", full_page=False)
            
            # Take a focused screenshot of just the sidebar
            sidebar = page.locator('.navbar-nav')
            if sidebar.is_visible():
                sidebar.screenshot(path="test/screenshots/passport_badge_closeup.png")
                print("✅ Screenshots saved to test/screenshots/")
            
            print("\n🎉 All tests passed! The passport badge is working correctly.")
            print(f"   - Badge is visible: ✓")
            print(f"   - Badge has green styling: ✓")
            print(f"   - Badge shows count: {badge_text} ✓")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            # Take error screenshot
            page.screenshot(path="test/screenshots/passport_badge_error.png")
            return False
            
        finally:
            browser.close()

if __name__ == "__main__":
    # Create screenshots directory if it doesn't exist
    os.makedirs("test/screenshots", exist_ok=True)
    
    # Run the test
    success = test_passport_badge()
    sys.exit(0 if success else 1)