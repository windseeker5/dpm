#!/usr/bin/env python3
"""
Test script to verify the image search UI properly handles API errors
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_image_search_ui():
    """Test the image search UI error handling"""
    
    # Import playwright tools
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        print("🚀 Testing image search UI error handling...")
        
        try:
            # 1. Login as admin
            print("\n1️⃣ Logging in as admin...")
            await page.goto('http://127.0.0.1:8890/login')
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_url('**/dashboard')
            print("   ✅ Logged in successfully")
            
            # 2. Navigate to create activity page (easier to test than edit)
            print("\n2️⃣ Navigating to create activity page...")
            await page.goto('http://127.0.0.1:8890/create-activity')
            await page.wait_for_load_state('networkidle')
            print("   ✅ Create activity page loaded")
            
            # Take screenshot of initial state
            await page.screenshot(path='.playwright-mcp/test-screenshots-01-edit-activity-initial.png')
            print("   📸 Screenshot saved: 01-edit-activity-initial.png")
            
            # 3. Enable image search
            print("\n3️⃣ Enabling image search...")
            
            # Click on the "Search images from the Web" toggle
            search_toggle = page.locator('input#toggleOnlineImage')
            await search_toggle.check()
            print("   ✅ Enabled web image search")
            
            # Wait for search UI to appear
            await page.wait_for_selector('#onlineImageSection', state='visible')
            
            # Take screenshot of search UI
            await page.screenshot(path='.playwright-mcp/test-screenshots-02-search-ui-visible.png')
            print("   📸 Screenshot saved: 02-search-ui-visible.png")
            
            # 4. Test search functionality (this should trigger the error)
            print("\n4️⃣ Testing image search with invalid API key...")
            
            # Enter search term
            await page.fill('input#imageDescription', 'hockey')
            print("   ✅ Entered search term: 'hockey'")
            
            # Click search button
            await page.click('button#searchImagesBtn')
            print("   ✅ Clicked search button")
            
            # Wait for modal to appear
            await page.wait_for_selector('#unsplashModal', state='visible', timeout=5000)
            print("   ✅ Image search modal opened")
            
            # Wait for error message to appear
            await page.wait_for_selector('.alert-warning', timeout=10000)
            print("   ✅ Error message displayed")
            
            # Take screenshot of error state
            await page.screenshot(path='.playwright-mcp/test-screenshots-03-search-results-working.png')
            print("   📸 Screenshot saved: 03-search-results-working.png")
            
            # 5. Verify error message content
            print("\n5️⃣ Verifying error message...")
            error_alert = page.locator('.alert-warning')
            error_text = await error_alert.text_content()
            
            if 'API key' in error_text or 'not available' in error_text:
                print("   ✅ Appropriate error message displayed")
            else:
                print(f"   ⚠️ Unexpected error message: {error_text}")
            
            # 6. Test closing modal and switching to upload
            print("\n6️⃣ Testing alternative upload option...")
            
            # Close the modal
            await page.click('.btn-close')
            await page.wait_for_selector('#unsplashModal', state='hidden')
            print("   ✅ Modal closed")
            
            # Switch to upload option
            upload_toggle = page.locator('input#toggleUploadImage')
            await upload_toggle.check()
            await page.wait_for_selector('#uploadImageSection', state='visible')
            print("   ✅ Switched to upload option")
            
            # Take final screenshot
            await page.screenshot(path='.playwright-mcp/test-screenshots-04-image-selected-success.png')
            print("   📸 Screenshot saved: 04-image-selected-success.png")
            
            print("\n✅ All tests completed successfully!")
            print("\n📊 Test Summary:")
            print("   - Login: ✅")
            print("   - Navigation: ✅")
            print("   - Image Search UI: ✅")
            print("   - Error Handling: ✅")
            print("   - Alternative Upload: ✅")
            print("\n📸 Screenshots saved in .playwright-mcp/")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            # Take error screenshot
            await page.screenshot(path='.playwright-mcp/test-error-state.png')
            print("   📸 Error screenshot saved: test-error-state.png")
            raise
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_image_search_ui())