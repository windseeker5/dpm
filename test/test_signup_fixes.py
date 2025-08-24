#!/usr/bin/env python3
"""
Test script to verify signup form fixes and thank you page functionality.
"""
import time
from playwright.sync_api import Playwright, sync_playwright, expect

def test_signup_form_fixes():
    """Test the signup form visual fixes and thank you page."""
    
    with sync_playwright() as playwright:
        # Launch browser
        browser = playwright.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            viewport={'width': 1200, 'height': 800}
        )
        page = context.new_page()
        
        try:
            print("🚀 Starting signup form tests...")
            
            # Navigate to login page
            page.goto("http://127.0.0.1:8890/login")
            page.wait_for_load_state("networkidle")
            
            # Login as admin
            print("🔐 Logging in as admin...")
            page.fill("input[name='email']", "kdresdell@gmail.com")
            page.fill("input[name='password']", "admin123")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            
            # Navigate to dashboard to find an activity
            page.goto("http://127.0.0.1:8890/dashboard")
            page.wait_for_load_state("networkidle")
            
            # Look for activities on the page
            activity_links = page.locator("a[href*='/signup/']").all()
            
            if not activity_links:
                print("❌ No signup links found on dashboard. Let's check activities page...")
                page.goto("http://127.0.0.1:8890/activities")
                page.wait_for_load_state("networkidle")
                activity_links = page.locator("a[href*='/signup/']").all()
            
            if activity_links:
                print(f"📋 Found {len(activity_links)} activity signup links")
                # Click the first signup link
                activity_links[0].click()
                page.wait_for_load_state("networkidle")
                
                # Take screenshot of signup form
                print("📸 Taking screenshot of signup form...")
                page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/playwright/signup_form_desktop.png")
                
                # Test 1: Check if organization logo is visible on desktop
                logo_desktop = page.locator("img[alt='Logo'].d-md-block")
                if logo_desktop.is_visible():
                    print("✅ Organization logo is visible on desktop")
                else:
                    print("❌ Organization logo is NOT visible on desktop")
                
                # Test 2: Check if activity title uses Anton font
                title_element = page.locator(".signup-title")
                if title_element.is_visible():
                    font_family = title_element.evaluate("el => window.getComputedStyle(el).fontFamily")
                    if "Anton" in font_family:
                        print("✅ Activity title uses Anton font")
                    else:
                        print(f"❌ Activity title font is: {font_family} (should include Anton)")
                else:
                    print("❌ Activity title not found")
                
                # Test 3: Check if price/sessions icons are black (no color classes)
                price_icon = page.locator("#pricing-info i.ti-currency-dollar")
                sessions_icon = page.locator("#pricing-info i.ti-ticket")
                
                if price_icon.is_visible():
                    price_classes = price_icon.get_attribute("class")
                    if "text-success" not in price_classes:
                        print("✅ Price icon color class removed (no text-success)")
                    else:
                        print("❌ Price icon still has text-success class")
                
                if sessions_icon.is_visible():
                    sessions_classes = sessions_icon.get_attribute("class")
                    if "text-primary" not in sessions_classes:
                        print("✅ Sessions icon color class removed (no text-primary)")
                    else:
                        print("❌ Sessions icon still has text-primary class")
                
                # Test 4: Fill out and submit the form to test thank you page
                print("📝 Filling out signup form...")
                page.fill("input[name='name']", "Test User")
                page.fill("input[name='email']", "test@example.com")
                page.fill("input[name='phone']", "+1 (514) 123-4567")
                page.fill("textarea[name='notes']", "Test signup for verification")
                page.check("input[name='accept_terms']")
                
                # Submit the form
                print("📤 Submitting signup form...")
                page.click("button[type='submit']")
                page.wait_for_load_state("networkidle")
                
                # Check if we're redirected to thank you page
                current_url = page.url
                if "/signup/thank-you/" in current_url:
                    print("✅ Successfully redirected to thank you page")
                    
                    # Take screenshot of thank you page
                    print("📸 Taking screenshot of thank you page...")
                    page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/playwright/thank_you_page_desktop.png")
                    
                    # Check thank you page elements
                    if page.locator(".thank-you-title").is_visible():
                        print("✅ Thank you title is visible")
                    else:
                        print("❌ Thank you title not found")
                    
                    if page.locator(".activity-name").is_visible():
                        activity_name = page.locator(".activity-name").inner_text()
                        print(f"✅ Activity name displayed: {activity_name}")
                    else:
                        print("❌ Activity name not displayed")
                    
                    if page.locator(".success-icon").is_visible():
                        print("✅ Success icon animation is present")
                    else:
                        print("❌ Success icon not found")
                    
                    if page.locator(".btn-home").is_visible():
                        print("✅ Return home button is present")
                    else:
                        print("❌ Return home button not found")
                    
                else:
                    print(f"❌ Not redirected to thank you page. Current URL: {current_url}")
                
                # Test mobile view
                print("📱 Testing mobile view...")
                page.set_viewport_size({"width": 375, "height": 667})
                page.reload()
                page.wait_for_load_state("networkidle")
                
                # Take mobile screenshot
                page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/playwright/thank_you_page_mobile.png")
                print("📸 Mobile screenshot taken")
                
            else:
                print("❌ No signup links found. Please create an activity first.")
        
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/playwright/error_screenshot.png")
        
        finally:
            print("🔚 Closing browser...")
            browser.close()

if __name__ == "__main__":
    test_signup_form_fixes()