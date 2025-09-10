#!/usr/bin/env python3
"""
Test script to diagnose email template issues and take screenshots
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def test_email_templates():
    """Test email template functionality and take screenshots"""
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            
            print("🔍 Testing Email Templates Functionality...")
            
            # Navigate to login page
            await page.goto("http://localhost:5000/login")
            await page.wait_for_load_state("networkidle")
            
            # Login
            await page.fill('input[name="email"]', "kdresdell@gmail.com")
            await page.fill('input[name="password"]', "admin123")
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle")
            
            # Navigate to a specific activity's email templates
            # Let's try activity 4 first
            await page.goto("http://localhost:5000/activity/4/email-templates")
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot of current state
            await page.screenshot(path=".playwright-mcp/email-templates-current-state.png")
            print("📷 Screenshot saved: email-templates-current-state.png")
            
            # Check if template cards are visible
            template_cards = await page.locator('.template-item').count()
            print(f"📊 Found {template_cards} template cards")
            
            # Check if any customize buttons are visible
            customize_buttons = await page.locator('.customize-btn').count()
            print(f"🔧 Found {customize_buttons} customize buttons")
            
            if customize_buttons > 0:
                print("🎯 Testing customize button click...")
                
                # Click on the first customize button
                await page.locator('.customize-btn').first.click()
                await page.wait_for_timeout(2000)
                
                # Check if modal opened
                modal_visible = await page.locator('#customizeModal').is_visible()
                print(f"🪟 Modal visible: {modal_visible}")
                
                if modal_visible:
                    # Take screenshot of modal
                    await page.screenshot(path=".playwright-mcp/email-templates-modal-open.png")
                    print("📷 Screenshot saved: email-templates-modal-open.png")
                    
                    # Check for form fields in modal
                    subject_field = await page.locator('input[id*="subject"]').count()
                    title_field = await page.locator('input[id*="title"]').count()
                    textarea_fields = await page.locator('textarea.template-textarea').count()
                    
                    print(f"📝 Form fields found:")
                    print(f"   Subject fields: {subject_field}")
                    print(f"   Title fields: {title_field}")
                    print(f"   Textarea fields: {textarea_fields}")
                    
                    # Test input functionality
                    if subject_field > 0:
                        subject_input = page.locator('input[id*="subject"]').first
                        await subject_input.fill("Test Subject Input")
                        value = await subject_input.input_value()
                        print(f"✅ Subject input test: '{value}'")
                    
                    if title_field > 0:
                        title_input = page.locator('input[id*="title"]').first  
                        await title_input.fill("Test Title Input")
                        value = await title_input.input_value()
                        print(f"✅ Title input test: '{value}'")
                    
                    # Close modal
                    await page.locator('#customizeModal .btn-close').click()
                    await page.wait_for_timeout(1000)
                else:
                    print("❌ Modal did not open - checking for errors")
                    
            else:
                print("❌ No customize buttons found")
                
            # Check for JavaScript errors
            page.on('console', lambda msg: print(f"🔍 Console: {msg.text}"))
            page.on('pageerror', lambda error: print(f"❌ Page Error: {error}"))
            
            # Final screenshot
            await page.screenshot(path=".playwright-mcp/email-templates-final-state.png", full_page=True)
            print("📷 Final screenshot saved: email-templates-final-state.png")
            
            await browser.close()
            print("✅ Test completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_templates())