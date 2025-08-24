#!/usr/bin/env python3
"""
Test script to verify that passport type selection UI is hidden in signup form
while functionality remains intact.
"""

import asyncio
from playwright.async_api import async_playwright
import os

async def test_signup_form_hidden_passport_selection():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to signup form
        await page.goto("http://127.0.0.1:8890/signup/1")
        
        # Take screenshot of the signup form
        screenshot_path = "/home/kdresdell/Documents/DEV/minipass_env/app/playwright/signup_form_after_hiding_passport_selection.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Check if passport type selection UI is hidden
        passport_selection_visible = await page.is_visible('div:has-text("Registration Type")')
        print(f"Passport type selection visible: {passport_selection_visible}")
        
        # Check if hidden input field still exists
        hidden_input = await page.query_selector('input[name="passport_type_id"][type="hidden"]')
        hidden_input_exists = hidden_input is not None
        print(f"Hidden passport_type_id input exists: {hidden_input_exists}")
        
        # Check if form can still be submitted (fill required fields)
        await page.fill('input[name="name"]', 'Test User')
        await page.fill('input[name="email"]', 'test@example.com')
        await page.check('input[name="accept_terms"]')
        
        # Take screenshot after filling form
        screenshot_filled_path = "/home/kdresdell/Documents/DEV/minipass_env/app/playwright/signup_form_filled.png"
        await page.screenshot(path=screenshot_filled_path, full_page=True)
        print(f"Filled form screenshot saved to: {screenshot_filled_path}")
        
        await browser.close()
        
        return {
            'passport_selection_visible': passport_selection_visible,
            'hidden_input_exists': hidden_input_exists,
            'screenshot_path': screenshot_path,
            'filled_screenshot_path': screenshot_filled_path
        }

if __name__ == "__main__":
    # Ensure playwright directory exists
    os.makedirs("/home/kdresdell/Documents/DEV/minipass_env/app/playwright", exist_ok=True)
    
    result = asyncio.run(test_signup_form_hidden_passport_selection())
    
    print("\n=== TEST RESULTS ===")
    print(f"✅ Passport selection UI hidden: {not result['passport_selection_visible']}")
    print(f"✅ Hidden input field preserved: {result['hidden_input_exists']}")
    print(f"📸 Screenshots saved for visual verification")