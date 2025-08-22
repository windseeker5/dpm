#!/usr/bin/env python3
"""
Test script to verify the analytics chatbot fixes are working properly.
Tests the critical issues reported by the user.
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def test_chatbot_fixes():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1200, 'height': 800}
        )
        page = await context.new_page()
        
        print("🔍 Testing Analytics Chatbot Fixes...")
        
        try:
            # Navigate to login page
            await page.goto('http://127.0.0.1:8890/login')
            await page.wait_for_load_state('networkidle')
            
            # Login
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Navigate to analytics chatbot
            await page.goto('http://127.0.0.1:8890/analytics-chatbot-simple')
            await page.wait_for_load_state('networkidle')
            
            # Test 1: Check title styling and size
            print("✅ Test 1: Checking title styling...")
            title_element = await page.locator('.welcome-title').first
            title_styles = await title_element.evaluate('el => window.getComputedStyle(el)')
            font_size = await title_element.evaluate('el => window.getComputedStyle(el).fontSize')
            print(f"   Title font size: {font_size}")
            
            # Test 2: Check sparkle icon size and color
            print("✅ Test 2: Checking sparkle icon...")
            sparkle_icon = await page.locator('.sparkle-icon').first
            icon_color = await sparkle_icon.evaluate('el => window.getComputedStyle(el).color')
            icon_size = await sparkle_icon.evaluate('el => window.getComputedStyle(el).fontSize')
            print(f"   Sparkle icon color: {icon_color}")
            print(f"   Sparkle icon size: {icon_size}")
            
            # Test 3: Check model dropdown position (top-left)
            print("✅ Test 3: Checking model dropdown position...")
            model_dropdown = await page.locator('.model-dropdown').first
            dropdown_position = await model_dropdown.evaluate('''
                el => {
                    const rect = el.getBoundingClientRect();
                    const parent = el.parentElement.getBoundingClientRect();
                    return {
                        top: rect.top - parent.top,
                        left: rect.left - parent.left
                    };
                }
            ''')
            print(f"   Model dropdown position: top={dropdown_position['top']}px, left={dropdown_position['left']}px")
            
            # Test 4: Check placeholder position (should be in textarea, bottom of search box)
            print("✅ Test 4: Checking placeholder position...")
            textarea = await page.locator('#messageInputLarge').first
            placeholder = await textarea.get_attribute('placeholder')
            print(f"   Placeholder text: {placeholder}")
            
            # Test 5: Test example button functionality (CRITICAL FIX)
            print("✅ Test 5: Testing example button functionality...")
            
            # Take screenshot before clicking
            await page.screenshot(path='tests/chatbot-fixes-before-click.png')
            
            # Click the first example button
            first_example = await page.locator('.example-question').first
            example_text = await first_example.text_content()
            print(f"   Clicking example: {example_text}")
            
            # Monitor textarea value changes
            initial_value = await textarea.input_value()
            print(f"   Textarea value before click: '{initial_value}'")
            
            await first_example.click()
            await page.wait_for_timeout(1000)  # Wait for any JavaScript to execute
            
            final_value = await textarea.input_value()
            print(f"   Textarea value after click: '{final_value}'")
            
            # Check if the textarea was populated
            if final_value and final_value.strip() == example_text.strip():
                print("   ✅ Example button WORKS - textarea populated correctly!")
            else:
                print("   ❌ Example button FAILED - textarea not populated")
                
            # Take screenshot after clicking
            await page.screenshot(path='tests/chatbot-fixes-after-click.png')
            
            # Test 6: Check model dropdown height
            print("✅ Test 6: Checking model dropdown height...")
            model_select = await page.locator('.model-select').first
            select_height = await model_select.evaluate('el => el.offsetHeight')
            print(f"   Model select height: {select_height}px")
            
            # Test 7: Test all example buttons
            print("✅ Test 7: Testing all example buttons...")
            example_buttons = await page.locator('.example-question').all()
            
            for i, button in enumerate(example_buttons):
                button_text = await button.text_content()
                print(f"   Testing button {i+1}: {button_text}")
                
                # Clear textarea first
                await textarea.fill('')
                await page.wait_for_timeout(500)
                
                # Click button
                await button.click()
                await page.wait_for_timeout(1000)
                
                # Check if populated
                value = await textarea.input_value()
                if value and value.strip() == button_text.strip():
                    print(f"     ✅ Button {i+1} works correctly")
                else:
                    print(f"     ❌ Button {i+1} failed - expected '{button_text}', got '{value}'")
            
            # Take final screenshot
            await page.screenshot(path='tests/chatbot-fixes-final.png')
            
            print("\n🎉 All tests completed!")
            print("📸 Screenshots saved:")
            print("   - tests/chatbot-fixes-before-click.png")
            print("   - tests/chatbot-fixes-after-click.png") 
            print("   - tests/chatbot-fixes-final.png")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            await page.screenshot(path='tests/chatbot-fixes-error.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_chatbot_fixes())