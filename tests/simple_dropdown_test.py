#!/usr/bin/env python3
"""
Simple Dropdown Test - Check current issues
"""
import asyncio
from playwright.async_api import async_playwright

async def test_current_issues():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        try:
            print("🔍 Testing current dropdown issues...")
            
            # Navigate and login
            await page.goto("http://127.0.0.1:8890")
            
            if await page.is_visible('input[name="email"]'):
                await page.fill('input[name="email"]', 'kdresdell@gmail.com')
                await page.fill('input[name="password"]', 'admin123')
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                print("✅ Logged in")
            
            # Wait for dashboard
            await page.wait_for_selector('.kpi-section', timeout=5000)
            print("✅ Dashboard loaded")
            
            # Screenshot initial state
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/issue-test-1-initial.png")
            
            # Find first KPI dropdown
            kpi_dropdown = await page.query_selector('.kpi-section [data-bs-toggle="dropdown"]')
            if not kpi_dropdown:
                print("❌ No KPI dropdown found")
                return
            
            print("🔍 Testing first dropdown open...")
            await kpi_dropdown.click()
            await page.wait_for_timeout(1000)
            
            # Check if dropdown opened
            dropdown_menu = await page.query_selector('.dropdown-menu.show')
            if dropdown_menu:
                print("✅ First dropdown opened successfully")
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/issue-test-2-first-open.png")
                
                # Check if it's visible
                is_visible = await dropdown_menu.is_visible()
                print(f"Dropdown visible: {is_visible}")
                
                # Get position info
                bbox = await dropdown_menu.bounding_box()
                print(f"Dropdown position: {bbox}")
            else:
                print("❌ First dropdown failed to open")
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/issue-test-2-first-fail.png")
                return
            
            # Test second dropdown
            print("🔍 Testing second dropdown...")
            kpi_dropdowns = await page.query_selector_all('.kpi-section [data-bs-toggle="dropdown"]')
            if len(kpi_dropdowns) > 1:
                await kpi_dropdowns[1].click()
                await page.wait_for_timeout(1000)
                
                open_menus = await page.query_selector_all('.dropdown-menu.show')
                print(f"Open menus after second click: {len(open_menus)}")
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/issue-test-3-second-click.png")
            
            # Test clicking outside
            print("🔍 Testing click outside...")
            await page.click('body', position={"x": 100, "y": 100})
            await page.wait_for_timeout(1000)
            
            open_menus_after_outside = await page.query_selector_all('.dropdown-menu.show')
            print(f"Open menus after outside click: {len(open_menus_after_outside)}")
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/issue-test-4-outside-click.png")
            
            # Test escape key
            print("🔍 Testing escape key...")
            # Open dropdown first
            await kpi_dropdowns[0].click()
            await page.wait_for_timeout(500)
            
            # Press escape
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            
            open_menus_after_escape = await page.query_selector_all('.dropdown-menu.show')
            print(f"Open menus after escape: {len(open_menus_after_escape)}")
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/issue-test-5-escape.png")
            
            print("✅ Test completed")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/issue-test-error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_current_issues())