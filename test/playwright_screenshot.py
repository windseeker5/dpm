#!/usr/bin/env python3
"""
Take a screenshot of the improved signup form
"""
from playwright.sync_api import sync_playwright
import time

def take_signup_form_screenshot():
    """Take a screenshot of the signup form to verify visual improvements"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1200, 'height': 800})
        page = context.new_page()
        
        try:
            # Navigate to signup form
            page.goto("http://127.0.0.1:8890/signup/1")
            
            # Wait for form to load
            page.wait_for_selector("input[name='name']", timeout=5000)
            
            # Take screenshot
            screenshot_path = "/home/kdresdell/Documents/DEV/minipass_env/app/playwright/signup_form_visual_improvements.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            print(f"✓ Screenshot saved: {screenshot_path}")
            
            # Also take a mobile-sized screenshot
            context_mobile = browser.new_context(viewport={'width': 375, 'height': 812})
            page_mobile = context_mobile.new_page()
            page_mobile.goto("http://127.0.0.1:8890/signup/1")
            page_mobile.wait_for_selector("input[name='name']", timeout=5000)
            
            mobile_screenshot_path = "/home/kdresdell/Documents/DEV/minipass_env/app/playwright/signup_form_mobile_improvements.png"
            page_mobile.screenshot(path=mobile_screenshot_path, full_page=True)
            
            print(f"✓ Mobile screenshot saved: {mobile_screenshot_path}")
            
            context_mobile.close()
            
        except Exception as e:
            print(f"✗ Screenshot failed: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    take_signup_form_screenshot()