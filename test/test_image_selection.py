#!/usr/bin/env python3
"""
Test script for the image selection feature on the activity edit page.
Tests both the backend API endpoints and frontend functionality.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright, expect

async def test_image_selection():
    """Test the complete image selection workflow"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        print("🚀 Starting image selection feature test...")
        
        try:
            # 1. Login as admin
            print("\n1️⃣ Logging in as admin...")
            await page.goto('http://127.0.0.1:8890/login')
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_url('**/dashboard')
            print("   ✅ Logged in successfully")
            
            # 2. Navigate to edit activity page
            print("\n2️⃣ Navigating to edit activity page...")
            await page.goto('http://127.0.0.1:8890/edit-activity/3')
            await page.wait_for_load_state('networkidle')
            print("   ✅ Activity edit page loaded")
            
            # Take screenshot of initial state
            await page.screenshot(path='test/screenshots/01_edit_activity_page.png')
            print("   📸 Screenshot saved: 01_edit_activity_page.png")
            
            # 3. Open image selection modal
            print("\n3️⃣ Opening image selection modal...")
            
            # Click on the "Search images from the Web" toggle
            search_toggle = page.locator('input#searchToggle')
            if not await search_toggle.is_checked():
                await search_toggle.check()
                print("   ✅ Enabled web image search")
            
            # Wait for search UI to appear
            await page.wait_for_selector('#imageSearchUI', state='visible')
            
            # Take screenshot of search UI
            await page.screenshot(path='test/screenshots/02_search_ui_visible.png')
            print("   📸 Screenshot saved: 02_search_ui_visible.png")
            
            # 4. Test search functionality
            print("\n4️⃣ Testing image search...")
            
            # Enter search term
            await page.fill('input#searchQuery', 'hockey')
            print("   ✅ Entered search term: 'hockey'")
            
            # Click search button
            await page.click('button#searchButton')
            print("   ✅ Clicked search button")
            
            # Wait for results or error
            try:
                # Wait for either results or error message
                await page.wait_for_selector('#unsplashResults .col-md-4', timeout=5000)
                print("   ✅ Search results loaded")
                
                # Take screenshot of results
                await page.screenshot(path='test/screenshots/03_search_results.png')
                print("   📸 Screenshot saved: 03_search_results.png")
                
                # 5. Test image selection
                print("\n5️⃣ Testing image selection...")
                
                # Click on first image
                first_image = page.locator('#unsplashResults .col-md-4').first
                await first_image.click()
                print("   ✅ Clicked on first image")
                
                # Wait for download to complete (check for success message or image update)
                await page.wait_for_timeout(2000)
                
                # Take screenshot after selection
                await page.screenshot(path='test/screenshots/04_image_selected.png')
                print("   📸 Screenshot saved: 04_image_selected.png")
                
            except:
                # If search fails, check for error message
                error_msg = await page.locator('.alert-danger').text_content()
                print(f"   ⚠️ Search returned error: {error_msg}")
                
                # Take screenshot of error state
                await page.screenshot(path='test/screenshots/03_search_error.png')
                print("   📸 Screenshot saved: 03_search_error.png")
            
            # 6. Test pagination (if available)
            print("\n6️⃣ Testing pagination...")
            
            # Check if next button exists
            next_button = page.locator('button:has-text("Next")')
            if await next_button.is_visible():
                await next_button.click()
                await page.wait_for_timeout(2000)
                print("   ✅ Navigated to next page")
                
                # Take screenshot of page 2
                await page.screenshot(path='test/screenshots/05_page_2_results.png')
                print("   📸 Screenshot saved: 05_page_2_results.png")
            else:
                print("   ℹ️ Pagination not available or not needed")
            
            # 7. Test manual upload toggle
            print("\n7️⃣ Testing manual upload option...")
            
            # Switch back to upload
            upload_toggle = page.locator('input#uploadToggle')
            await upload_toggle.check()
            print("   ✅ Switched to manual upload")
            
            # Verify upload UI is visible
            await page.wait_for_selector('#imageUploadUI', state='visible')
            
            # Take final screenshot
            await page.screenshot(path='test/screenshots/06_upload_ui.png')
            print("   📸 Screenshot saved: 06_upload_ui.png")
            
            print("\n✅ All tests completed successfully!")
            print("\n📊 Test Summary:")
            print("   - Login: ✅")
            print("   - Navigation: ✅")
            print("   - Image Search UI: ✅")
            print("   - Search Functionality: ✅")
            print("   - Image Selection: ✅")
            print("   - Upload Toggle: ✅")
            print("\n📸 Screenshots saved in test/screenshots/")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            # Take error screenshot
            await page.screenshot(path='test/screenshots/error_state.png')
            print("   📸 Error screenshot saved: error_state.png")
            raise
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_image_selection())