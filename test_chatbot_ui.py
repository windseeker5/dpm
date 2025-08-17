#!/usr/bin/env python3
"""
Test script to view the chatbot UI and take a screenshot
"""
from playwright.sync_api import sync_playwright
import time

def test_chatbot_ui():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Go to login page
            print("Navigating to login page...")
            page.goto("http://127.0.0.1:8890/login")
            
            # Login with admin credentials
            print("Logging in...")
            page.fill('input[name="email"]', 'kdresdell@gmail.com')
            page.fill('input[name="password"]', 'admin123')
            page.click('button[type="submit"]')
            
            # Wait for redirect to dashboard
            page.wait_for_url("**/dashboard", timeout=5000)
            print("Login successful!")
            
            # Navigate to chatbot
            print("Navigating to chatbot...")
            page.goto("http://127.0.0.1:8890/chatbot/")
            
            # Wait for page to load
            page.wait_for_selector('.chat-wrapper', timeout=10000)
            print("Chatbot page loaded!")
            
            # Check for status indicator
            status_indicator = page.query_selector('.status-indicator')
            if status_indicator:
                print("✓ Status indicator found")
                
            # Check for model dropdown
            model_selector = page.query_selector('#modelSelector')
            if model_selector:
                options = page.query_selector_all('#modelSelector option')
                print(f"✓ Model selector found with {len(options)} options")
                for i, option in enumerate(options):
                    text = option.inner_text()
                    value = option.get_attribute('value')
                    print(f"  {i+1}. {text} (value: {value})")
            
            # Take a screenshot
            print("Taking screenshot...")
            page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_ui_fixed.png", full_page=True)
            print("Screenshot saved to chatbot_ui_fixed.png")
            
            # Test status indicator states
            print("Testing status indicator states...")
            page.evaluate("demoStatusLED()")
            time.sleep(2)
            
            # Wait a bit to see the changes
            time.sleep(3)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_chatbot_ui()