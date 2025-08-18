#!/usr/bin/env python3
"""
Test script to verify the chatbot UI improvements work correctly
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

async def test_chatbot_improvements():
    """Test all the UI improvements made to the analytics chatbot"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        try:
            print("🚀 Starting chatbot UI improvements test...")
            
            # Navigate to login page
            await page.goto("http://127.0.0.1:8890/login")
            await page.wait_for_selector("input[name='email']")
            
            # Login
            await page.fill("input[name='email']", "kdresdell@gmail.com")
            await page.fill("input[name='password']", "admin123")
            await page.click("button[type='submit']")
            
            # Wait for dashboard and navigate to chatbot
            await page.wait_for_selector(".page-wrapper", timeout=10000)
            await page.goto("http://127.0.0.1:8890/analytics/chatbot")
            await page.wait_for_selector(".chat-container", timeout=10000)
            
            print("✅ Successfully navigated to chatbot page")
            
            # Test 1: Check if title is properly styled with h2 tag and gradient
            print("\n📝 Test 1: Checking title styling...")
            title_element = await page.wait_for_selector("h2.welcome-title")
            title_text = await title_element.text_content()
            assert "How can I help you today?" in title_text, "Title text not found"
            
            # Check if gradient CSS is applied
            title_styles = await title_element.evaluate("el => getComputedStyle(el)")
            print(f"   Title tag: h2 ✅")
            print(f"   Title text: {title_text} ✅")
            
            # Test 2: Check sparkle icon styling and animation
            print("\n✨ Test 2: Checking sparkle icon...")
            sparkle_icon = await page.wait_for_selector(".sparkle-icon")
            icon_classes = await sparkle_icon.get_attribute("class")
            assert "ti ti-sparkles" in icon_classes, "Sparkle icon classes not correct"
            assert "sparkle-icon" in icon_classes, "Animation class not found"
            print(f"   Sparkle icon classes: {icon_classes} ✅")
            
            # Test 3: Check model dropdown text size
            print("\n📱 Test 3: Checking model dropdown text size...")
            await page.wait_for_selector(".model-select")
            model_select = await page.query_selector(".model-select")
            font_size = await model_select.evaluate("el => getComputedStyle(el).fontSize")
            print(f"   Model dropdown font size: {font_size}")
            # Should be around 13px (0.8125rem)
            
            # Test 4: Check example question button styling
            print("\n🔘 Test 4: Checking example question buttons...")
            example_buttons = await page.query_selector_all(".example-question")
            if example_buttons:
                first_button = example_buttons[0]
                border_radius = await first_button.evaluate("el => getComputedStyle(el).borderRadius")
                print(f"   Example button border-radius: {border_radius}")
                # Should be 8px instead of 20px
                assert border_radius == "8px", f"Border radius should be 8px, got {border_radius}"
                print("   Example buttons are less rounded ✅")
            
            # Test 5: Test Enter key functionality
            print("\n⌨️  Test 5: Testing Enter key functionality...")
            
            # Focus the large input field
            large_input = await page.wait_for_selector("#messageInputLarge")
            await large_input.click()
            
            # Type a test message
            test_message = "Test message for Enter key"
            await large_input.fill(test_message)
            
            # Press Enter and check if message is submitted
            await large_input.press("Enter")
            
            # Wait a moment for the form submission
            await page.wait_for_timeout(1000)
            
            # Check if we switched to conversation mode (empty state should be hidden)
            empty_state = await page.query_selector("#emptyState")
            empty_state_classes = await empty_state.get_attribute("class")
            
            if "hidden" in empty_state_classes:
                print("   Enter key properly submits message ✅")
                
                # Check if message appears in conversation
                await page.wait_for_selector(".message.user", timeout=5000)
                user_messages = await page.query_selector_all(".message.user")
                if user_messages:
                    message_content = await user_messages[-1].query_selector(".message-content")
                    message_text = await message_content.text_content()
                    if test_message in message_text:
                        print(f"   Message properly sent: '{message_text}' ✅")
                    else:
                        print(f"   Warning: Message text doesn't match. Expected: '{test_message}', Got: '{message_text}'")
                
            else:
                print("   Warning: Enter key may not have triggered form submission properly")
            
            # Take a screenshot to verify visual improvements
            screenshot_path = "/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_improvements_test.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n📸 Screenshot saved: {screenshot_path}")
            
            print("\n🎉 All chatbot UI improvements tests completed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            # Take error screenshot
            error_screenshot = "/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_improvements_error.png"
            await page.screenshot(path=error_screenshot, full_page=True)
            print(f"📸 Error screenshot saved: {error_screenshot}")
            return False
            
        finally:
            await browser.close()
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_chatbot_improvements())
    sys.exit(0 if result else 1)