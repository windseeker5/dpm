#!/usr/bin/env python3
"""
Test script for the improved chatbot interface
"""
import asyncio
from playwright.async_api import async_playwright
import sys

async def test_chatbot():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("🔍 Testing improved chatbot interface...")
            
            # 1. Login
            print("📝 Logging in...")
            await page.goto("http://127.0.0.1:8890/login")
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_url("**/dashboard")
            print("✅ Login successful")
            
            # 2. Navigate to chatbot
            print("🤖 Navigating to chatbot...")
            await page.goto("http://127.0.0.1:8890/chatbot/")
            await page.wait_for_selector('.welcome-title')
            print("✅ Chatbot page loaded")
            
            # 3. Check search box height
            print("📏 Checking search box height...")
            search_box = await page.query_selector('.message-input-large')
            box_height = await search_box.evaluate('el => window.getComputedStyle(el).height')
            print(f"   Search box height: {box_height}")
            
            # 4. Check model dropdown
            print("📋 Checking model dropdown...")
            dropdown = await page.query_selector('.model-select')
            if dropdown:
                print("✅ Model dropdown found")
                # Get options
                options = await dropdown.evaluate('''el => {
                    const opts = Array.from(el.options);
                    return opts.map(o => ({value: o.value, text: o.text}));
                }''')
                print(f"   Available models: {[opt['text'] for opt in options]}")
            else:
                print("❌ Model dropdown not found")
            
            # 5. Check send button styling
            print("🎨 Checking send button...")
            send_btn = await page.query_selector('.send-button-large')
            btn_bg = await send_btn.evaluate('el => window.getComputedStyle(el).backgroundColor')
            print(f"   Send button background: {btn_bg}")
            
            # 6. Test model selection
            if dropdown:
                print("🔄 Testing model selection...")
                await dropdown.select_option('ollama')
                await page.wait_for_timeout(500)
                # Check LED status
                led = await page.query_selector('.status-led')
                led_color = await led.evaluate('el => window.getComputedStyle(el).backgroundColor')
                print(f"   LED color after selection: {led_color}")
            
            # 7. Test sending a message
            print("💬 Testing message sending...")
            await page.fill('.message-input-large', 'What is our total revenue?')
            await page.click('.send-button-large')
            
            # Wait for response
            await page.wait_for_selector('.message.assistant', timeout=5000)
            response = await page.query_selector('.message.assistant .message-content')
            response_text = await response.text_content()
            print(f"   Response: {response_text[:100]}...")
            
            # 8. Take screenshot
            print("📸 Taking screenshot...")
            await page.screenshot(path='chatbot-improved-test.png', full_page=False)
            print("✅ Screenshot saved as chatbot-improved-test.png")
            
            print("\n🎉 All tests passed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            await page.screenshot(path='chatbot-error.png')
            print("   Error screenshot saved as chatbot-error.png")
            return False
        finally:
            await browser.close()
        
        return True

if __name__ == "__main__":
    success = asyncio.run(test_chatbot())
    sys.exit(0 if success else 1)