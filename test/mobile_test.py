#!/usr/bin/env python3
"""
Quick Mobile Dropdown Test
"""
import asyncio
from playwright.async_api import async_playwright

async def mobile_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        try:
            print("📱 Mobile Dropdown Test")
            
            # Login
            await page.goto("http://127.0.0.1:8890")
            
            if await page.is_visible('input[name="email"]'):
                await page.fill('input[name="email"]', 'kdresdell@gmail.com')
                await page.fill('input[name="password"]', 'admin123')
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
            
            await page.wait_for_selector('.kpi-section', timeout=5000)
            
            # Set mobile viewport
            await page.set_viewport_size({"width": 375, "height": 667})
            await page.wait_for_timeout(1000)
            print("📱 Switched to mobile viewport: 375x667")
            
            # Find mobile dropdowns
            mobile_dropdowns = await page.query_selector_all('[data-bs-toggle="dropdown"]')
            print(f"🔍 Found {len(mobile_dropdowns)} dropdowns on mobile")
            
            if mobile_dropdowns:
                # Click first dropdown
                await mobile_dropdowns[0].click()
                await page.wait_for_timeout(1000)
                
                mobile_menu = await page.query_selector('.dropdown-menu.show')
                if mobile_menu:
                    mobile_bbox = await mobile_menu.bounding_box()
                    mobile_viewport = page.viewport_size
                    
                    print(f"Mobile dropdown bounding box: {mobile_bbox}")
                    print(f"Mobile viewport: {mobile_viewport}")
                    
                    # Check if fully within viewport
                    fits_horizontally = (
                        mobile_bbox['x'] >= 0 and 
                        mobile_bbox['x'] + mobile_bbox['width'] <= mobile_viewport['width']
                    )
                    fits_vertically = (
                        mobile_bbox['y'] >= 0 and 
                        mobile_bbox['y'] + mobile_bbox['height'] <= mobile_viewport['height']
                    )
                    
                    if fits_horizontally and fits_vertically:
                        print("✅ Mobile dropdown fits completely within viewport!")
                    else:
                        print(f"❌ Mobile dropdown overflow:")
                        print(f"   Horizontal fit: {fits_horizontally}")
                        print(f"   Vertical fit: {fits_vertically}")
                        print(f"   Right edge: {mobile_bbox['x'] + mobile_bbox['width']} (max: {mobile_viewport['width']})")
                        print(f"   Bottom edge: {mobile_bbox['y'] + mobile_bbox['height']} (max: {mobile_viewport['height']})")
                    
                    await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/mobile-dropdown-test.png")
                    print("📸 Mobile screenshot saved")
                else:
                    print("❌ Mobile dropdown did not open")
            else:
                print("❌ No dropdowns found on mobile")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(mobile_test())