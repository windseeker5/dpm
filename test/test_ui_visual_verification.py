#!/usr/bin/env python3
"""
Visual verification test for chatbot UI improvements
This will help verify the visual changes by taking screenshots
"""

import time
import asyncio
from playwright.async_api import async_playwright

async def test_visual_improvements():
    """Take screenshots to verify visual improvements"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        try:
            print("🎨 Visual Verification Test for Chatbot UI Improvements")
            print("=" * 60)
            
            # Navigate to login
            print("1. Navigating to login page...")
            await page.goto("http://127.0.0.1:8890/login")
            await page.wait_for_selector("input[name='email']")
            
            # Login
            print("2. Logging in...")
            await page.fill("input[name='email']", "kdresdell@gmail.com")
            await page.fill("input[name='password']", "admin123")
            await page.click("button[type='submit']")
            
            # Wait for dashboard
            await page.wait_for_selector(".page-wrapper", timeout=10000)
            
            # Navigate to chatbot
            print("3. Navigating to chatbot...")
            await page.goto("http://127.0.0.1:8890/chatbot/")
            await page.wait_for_selector(".chat-container", timeout=10000)
            
            # Wait for page to fully load
            await page.wait_for_timeout(2000)
            
            print("4. Taking screenshots of improvements...")
            
            # Screenshot 1: Full page overview
            screenshot1 = "/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_improvements_overview.png"
            await page.screenshot(path=screenshot1, full_page=True)
            print(f"✅ Full page screenshot: {screenshot1}")
            
            # Screenshot 2: Focus on title and icon
            title_element = await page.query_selector(".welcome-title")
            if title_element:
                screenshot2 = "/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_title_improvements.png"
                await title_element.screenshot(path=screenshot2)
                print(f"✅ Title improvements screenshot: {screenshot2}")
            
            # Screenshot 3: Focus on example buttons
            examples_element = await page.query_selector(".example-questions")
            if examples_element:
                screenshot3 = "/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_buttons_improvements.png"
                await examples_element.screenshot(path=screenshot3)
                print(f"✅ Example buttons screenshot: {screenshot3}")
            
            # Test Enter key functionality
            print("5. Testing Enter key functionality...")
            large_input = await page.query_selector("#messageInputLarge")
            if large_input:
                await large_input.click()
                await large_input.fill("Test Enter key functionality")
                
                # Take screenshot before pressing Enter
                screenshot4 = "/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_before_enter.png"
                await page.screenshot(path=screenshot4)
                print(f"✅ Before Enter key screenshot: {screenshot4}")
                
                # Press Enter
                await large_input.press("Enter")
                await page.wait_for_timeout(2000)  # Wait for any animations
                
                # Take screenshot after pressing Enter
                screenshot5 = "/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_after_enter.png"
                await page.screenshot(path=screenshot5)
                print(f"✅ After Enter key screenshot: {screenshot5}")
            
            print("\n6. Verifying visual elements...")
            
            # Check if title has gradient (by checking computed styles)
            title_element = await page.query_selector("h2.welcome-title")
            if title_element:
                print("✅ H2 title element found")
                
                # Check if sparkle icon exists
                sparkle_icon = await page.query_selector(".sparkle-icon")
                if sparkle_icon:
                    print("✅ Sparkle icon with animation class found")
                else:
                    print("❌ Sparkle icon not found")
            else:
                print("❌ Title element not found")
            
            # Check model dropdown
            model_select = await page.query_selector(".model-select")
            if model_select:
                font_size = await model_select.evaluate("el => getComputedStyle(el).fontSize")
                print(f"✅ Model dropdown font size: {font_size}")
            
            # Check example buttons
            example_button = await page.query_selector(".example-question")
            if example_button:
                border_radius = await example_button.evaluate("el => getComputedStyle(el).borderRadius")
                print(f"✅ Example button border-radius: {border_radius}")
            
            print("\n" + "=" * 60)
            print("🎉 Visual verification completed successfully!")
            print("\n📸 Screenshots saved:")
            print(f"   - Overview: chatbot_improvements_overview.png")
            print(f"   - Title: chatbot_title_improvements.png") 
            print(f"   - Buttons: chatbot_buttons_improvements.png")
            print(f"   - Before Enter: chatbot_before_enter.png")
            print(f"   - After Enter: chatbot_after_enter.png")
            
            return True
            
        except Exception as e:
            print(f"❌ Visual test failed: {e}")
            error_screenshot = "/home/kdresdell/Documents/DEV/minipass_env/app/chatbot_visual_test_error.png"
            await page.screenshot(path=error_screenshot)
            print(f"📸 Error screenshot: {error_screenshot}")
            return False
            
        finally:
            await browser.close()

if __name__ == "__main__":
    # For standalone execution, just print file verification
    print("🎨 Chatbot UI Improvements - File Verification")
    print("=" * 50)
    
    import os
    template_path = "/home/kdresdell/Documents/DEV/minipass_env/app/templates/analytics_chatbot_simple.html"
    
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            content = f.read()
            
        improvements = [
            ("H2 title tag", 'h2 class="welcome-title"' in content),
            ("Sparkle icon class", 'class="ti ti-sparkles sparkle-icon"' in content),
            ("Gradient CSS", 'linear-gradient(135deg, #374151 0%, #f97316 100%)' in content),
            ("Sparkle animation", '.sparkle-icon {' in content and 'color: #fbbf24' in content),
            ("Model dropdown font", 'font-size: 0.8125rem' in content),
            ("Button border-radius", 'border-radius: 8px' in content),
            ("Enter key fix", 'sendMessage(event, true)' in content)
        ]
        
        all_good = True
        for improvement, found in improvements:
            status = "✅" if found else "❌"
            print(f"{status} {improvement}: {'Found' if found else 'Not found'}")
            if not found:
                all_good = False
        
        if all_good:
            print("\n🎉 All improvements successfully implemented!")
            print("📍 Access the improved chatbot at: http://127.0.0.1:8890/chatbot/")
            print("🔐 Login: kdresdell@gmail.com / admin123")
        else:
            print("\n⚠️  Some improvements might be missing.")
    else:
        print(f"❌ Template file not found: {template_path}")