#!/usr/bin/env python3
"""
Test script to verify settings button alignment changes.
Takes a screenshot of the settings page to verify both buttons are right-aligned.
"""
import time
from playwright.sync_api import sync_playwright

def test_settings_button_alignment():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1440, 'height': 900}
        )
        page = context.new_page()
        
        try:
            # Navigate to login page first
            page.goto("http://127.0.0.1:8890/login")
            page.wait_for_load_state('networkidle')
            
            # Login with test credentials
            page.fill('input[name="email"]', 'kdresdell@gmail.com')
            page.fill('input[name="password"]', 'admin123')
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            
            # Navigate to settings page
            page.goto("http://127.0.0.1:8890/setup")
            page.wait_for_load_state('networkidle')
            
            # Wait a moment for all elements to load
            time.sleep(2)
            
            # Take screenshot of the full page
            screenshot_path = "/home/kdresdell/Documents/DEV/minipass_env/app/playwright/settings_button_alignment.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot saved to: {screenshot_path}")
            
            # Check if both buttons exist and are visible
            save_button = page.locator('button:has-text("Save All Settings")')
            add_button = page.locator('button:has-text("Add New Admin")')
            
            if save_button.is_visible():
                print("✅ 'Save All Settings' button is visible")
            else:
                print("❌ 'Save All Settings' button is NOT visible")
                
            if add_button.is_visible():
                print("✅ 'Add New Admin' button is visible")
            else:
                print("❌ 'Add New Admin' button is NOT visible")
            
            # Get button positions to verify right alignment
            save_button_box = save_button.bounding_box()
            add_button_box = add_button.bounding_box()
            viewport_width = 1440
            
            print(f"📊 Viewport width: {viewport_width}px")
            if save_button_box:
                save_right_edge = save_button_box['x'] + save_button_box['width']
                print(f"📊 'Save All Settings' button right edge: {save_right_edge}px")
                print(f"📊 Distance from right edge: {viewport_width - save_right_edge}px")
                
            if add_button_box:
                add_right_edge = add_button_box['x'] + add_button_box['width']
                print(f"📊 'Add New Admin' button right edge: {add_right_edge}px")
                print(f"📊 Distance from right edge: {viewport_width - add_right_edge}px")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_settings_button_alignment()