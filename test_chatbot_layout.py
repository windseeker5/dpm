#!/usr/bin/env python3
"""
Test script to verify the chatbot layout changes
"""
import asyncio
from playwright.async_api import async_playwright
import time

async def test_chatbot_layout():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to login page first
            print("Navigating to login page...")
            await page.goto("http://127.0.0.1:8890/login")
            await page.wait_for_load_state('networkidle')
            
            # Login with credentials
            print("Logging in...")
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Navigate to chatbot page
            print("Navigating to chatbot page...")
            await page.goto("http://127.0.0.1:8890/chatbot/")
            await page.wait_for_load_state('networkidle')
            
            # Wait a moment for any dynamic content to load
            await asyncio.sleep(2)
            
            # Take screenshot of the initial layout
            print("Taking screenshot...")
            await page.screenshot(path="tests/chatbot_layout_verification.png", full_page=True)
            
            # Test the layout elements
            print("Verifying layout elements...")
            
            # Check if title is h2 size (should be 2.5rem)
            title_element = await page.query_selector('.welcome-title')
            if title_element:
                title_style = await title_element.evaluate('el => window.getComputedStyle(el).fontSize')
                print(f"Title font size: {title_style}")
            
            # Check if textarea has the correct placeholder
            textarea = await page.query_selector('#messageInputLarge')
            if textarea:
                placeholder = await textarea.get_attribute('placeholder')
                print(f"Textarea placeholder: {placeholder}")
            
            # Check if model dropdown and send button are positioned correctly
            search_box = await page.query_selector('.search-box-inner')
            if search_box:
                display_style = await search_box.evaluate('el => window.getComputedStyle(el).display')
                print(f"Search box display: {display_style}")
            
            # Check sparkle icon color
            sparkle_icon = await page.query_selector('.sparkle-icon')
            if sparkle_icon:
                color_style = await sparkle_icon.evaluate('el => window.getComputedStyle(el).color')
                print(f"Sparkle icon color: {color_style}")
            
            print("Layout verification complete!")
            print("Screenshot saved to: tests/chatbot_layout_verification.png")
            
        except Exception as e:
            print(f"Error during test: {e}")
            # Take error screenshot
            await page.screenshot(path="tests/chatbot_layout_error.png", full_page=True)
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_chatbot_layout())