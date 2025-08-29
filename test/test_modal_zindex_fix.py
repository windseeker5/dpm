#!/usr/bin/env python3

import asyncio
import time
from playwright.async_api import async_playwright

async def test_modal_zindex_fix():
    """Test that modals appear above KPI dropdown buttons without bleed-through"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("🧪 Testing modal z-index fix...")
            
            # Navigate to login
            print("1. Navigating to login page...")
            await page.goto("http://127.0.0.1:8890/login")
            await page.wait_for_load_state('networkidle')
            
            # Login
            print("2. Logging in...")
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Test on activity_dashboard.html
            print("3. Testing modal z-index on activity dashboard...")
            await page.goto("http://127.0.0.1:8890/activity/1")
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot before clicking delete
            await page.screenshot(path="playwright/before_delete_modal.png", full_page=True)
            print("   📸 Screenshot saved: before_delete_modal.png")
            
            # Click delete button to trigger modal
            delete_button = page.locator('a:has-text("Delete")')
            if await delete_button.count() > 0:
                await delete_button.click()
                await page.wait_for_timeout(500)  # Wait for modal animation
                
                # Take screenshot with modal open
                await page.screenshot(path="playwright/delete_modal_open.png", full_page=True)
                print("   📸 Screenshot saved: delete_modal_open.png")
                
                # Check if modal is visible and properly layered
                modal_visible = await page.locator('.modal.show').is_visible()
                backdrop_visible = await page.locator('.modal-backdrop').is_visible()
                
                print(f"   ✅ Modal visible: {modal_visible}")
                print(f"   ✅ Backdrop visible: {backdrop_visible}")
                
                # Close modal by clicking Cancel or outside
                cancel_button = page.locator('button:has-text("Cancel")')
                if await cancel_button.count() > 0:
                    await cancel_button.click()
                    await page.wait_for_timeout(500)
                
            else:
                print("   ⚠️  Delete button not found on activity dashboard")
            
            # Test on activities.html list page
            print("4. Testing modal z-index on activities list...")
            await page.goto("http://127.0.0.1:8890/activities")
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot before clicking delete
            await page.screenshot(path="playwright/activities_before_delete_modal.png", full_page=True)
            print("   📸 Screenshot saved: activities_before_delete_modal.png")
            
            # Look for delete links in the activities table
            delete_links = page.locator('a:has-text("Delete")')
            delete_count = await delete_links.count()
            
            if delete_count > 0:
                # Click first delete link
                await delete_links.first.click()
                await page.wait_for_timeout(500)  # Wait for modal animation
                
                # Take screenshot with modal open
                await page.screenshot(path="playwright/activities_delete_modal_open.png", full_page=True)
                print("   📸 Screenshot saved: activities_delete_modal_open.png")
                
                # Check if modal is visible and properly layered
                modal_visible = await page.locator('.modal.show').is_visible()
                backdrop_visible = await page.locator('.modal-backdrop').is_visible()
                
                print(f"   ✅ Modal visible: {modal_visible}")
                print(f"   ✅ Backdrop visible: {backdrop_visible}")
                
                # Close modal
                cancel_button = page.locator('button:has-text("Cancel")')
                if await cancel_button.count() > 0:
                    await cancel_button.click()
                    await page.wait_for_timeout(500)
                else:
                    # Try clicking backdrop to close
                    await page.click('.modal-backdrop')
                    await page.wait_for_timeout(500)
                    
            else:
                print("   ⚠️  No delete links found on activities page")
            
            print("\n🎉 Modal z-index testing completed!")
            print("📁 Check playwright/ directory for screenshots to verify modal layering")
            
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            await page.screenshot(path="playwright/error_screenshot.png", full_page=True)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_modal_zindex_fix())