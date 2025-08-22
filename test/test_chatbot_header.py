#!/usr/bin/env python3
"""
Test script to view the chatbot UI header and status indicator
"""
from playwright.sync_api import sync_playwright
import time

def test_chatbot_header():
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
            
            # Check the header area specifically
            header = page.query_selector('.chat-header')
            if header:
                print("✓ Chat header found")
                
                # Check model selector
                model_selector = page.query_selector('#modelSelector')
                if model_selector:
                    print("✓ Model selector found")
                    selected_value = model_selector.input_value()
                    print(f"  Selected model: {selected_value}")
                    
                # Check status indicator
                status_indicator = page.query_selector('.status-indicator')
                status_dot = page.query_selector('.status-dot')
                if status_indicator and status_dot:
                    print("✓ Status indicator found")
                    title = status_indicator.get_attribute('title')
                    dot_classes = status_dot.get_attribute('class')
                    print(f"  Status tooltip: {title}")
                    print(f"  Dot classes: {dot_classes}")
            
            # Take a screenshot focusing on the header
            print("Taking header screenshot...")
            header_element = page.query_selector('.chat-header')
            if header_element:
                header_element.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_header_fixed.png")
                print("Header screenshot saved!")
            
            # Test the model selector by changing selection
            print("Testing model selector...")
            model_selector = page.query_selector('#modelSelector')
            if model_selector:
                # Get all options
                options = page.query_selector_all('#modelSelector option')
                print(f"Available models: {len(options)}")
                
                if len(options) > 1:
                    # Select the second option
                    second_option_value = options[1].get_attribute('value')
                    page.select_option('#modelSelector', second_option_value)
                    print(f"Changed to model: {second_option_value}")
                    
                    # Wait a bit for status check
                    time.sleep(2)
                    
                    # Check status after model change
                    status_indicator = page.query_selector('.status-indicator')
                    if status_indicator:
                        title = status_indicator.get_attribute('title')
                        print(f"Status after model change: {title}")
            
            # Take final screenshot
            page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_final_test.png", full_page=True)
            print("Final screenshot saved!")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_chatbot_header()