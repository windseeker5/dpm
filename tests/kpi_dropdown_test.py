#!/usr/bin/env python3
"""
KPI Dropdown Test using Playwright MCP
=====================================

Test the dropdown behavior in KPI cards on dashboard and activity dashboard pages.
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def test_dashboard_kpi_dropdowns():
    """Test KPI dropdown behavior on main dashboard"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        try:
            print("🚀 Testing KPI Dropdowns on Main Dashboard")
            print("=" * 50)
            
            # Navigate and login
            await page.goto("http://127.0.0.1:8890")
            
            # Login if needed
            if await page.is_visible('input[name="email"]'):
                await page.fill('input[name="email"]', 'kdresdell@gmail.com')
                await page.fill('input[name="password"]', 'admin123')
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                print("✅ Logged in successfully")
            
            # Wait for dashboard to load
            await page.wait_for_selector('.kpi-section', timeout=5000)
            print("✅ Dashboard loaded")
            
            # Take initial screenshot
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/dashboard-initial.png")
            print("📸 Initial dashboard screenshot")
            
            # Find KPI dropdown buttons
            kpi_dropdowns = await page.query_selector_all('.kpi-section [data-bs-toggle="dropdown"]')
            print(f"🔍 Found {len(kpi_dropdowns)} KPI dropdown buttons")
            
            if len(kpi_dropdowns) == 0:
                print("❌ No KPI dropdown buttons found!")
                return False
            
            # Test 1: Open first KPI dropdown
            print("\n🧪 Test 1: Opening first KPI dropdown")
            await kpi_dropdowns[0].click()
            await page.wait_for_timeout(500)
            
            first_menu = await page.query_selector('.dropdown-menu.show')
            if first_menu:
                print("✅ First KPI dropdown opened")
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/dashboard-first-dropdown.png")
            else:
                print("❌ First KPI dropdown failed to open")
                return False
            
            # Test 2: Open second KPI dropdown (should close first)
            if len(kpi_dropdowns) > 1:
                print("\n🧪 Test 2: Opening second KPI dropdown")
                await kpi_dropdowns[1].click()
                await page.wait_for_timeout(500)
                
                open_menus = await page.query_selector_all('.dropdown-menu.show')
                print(f"🔍 Open dropdown menus: {len(open_menus)}")
                
                if len(open_menus) <= 1:
                    print("✅ Only one dropdown open at a time")
                    await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/dashboard-second-dropdown.png")
                else:
                    print("❌ Multiple dropdowns open simultaneously")
                    await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/dashboard-multiple-error.png")
            
            # Test 3: Click outside to close
            print("\n🧪 Test 3: Click outside to close")
            await page.click('body', position={"x": 50, "y": 50})
            await page.wait_for_timeout(500)
            
            open_menus = await page.query_selector_all('.dropdown-menu.show')
            if len(open_menus) == 0:
                print("✅ Click outside closes dropdowns")
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/dashboard-click-outside.png")
            else:
                print("❌ Click outside failed to close dropdowns")
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/dashboard-click-outside-error.png")
            
            # Test 4: Test KPI period selection functionality
            print("\n🧪 Test 4: Test period selection functionality")
            await kpi_dropdowns[0].click()
            await page.wait_for_timeout(300)
            
            period_items = await page.query_selector_all('.dropdown-item.kpi-period-btn')
            if period_items:
                print(f"✅ Found {len(period_items)} period options")
                
                # Click "Last 30 days" if available
                for item in period_items:
                    text = await item.inner_text()
                    if "30 days" in text:
                        await item.click()
                        await page.wait_for_timeout(1000)
                        print("✅ Successfully selected '30 days' period")
                        break
                
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/dashboard-period-selection.png")
            else:
                print("❌ No period selection items found")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/dashboard-error.png")
            return False
        finally:
            await browser.close()

async def test_activity_dashboard_kpi_dropdowns():
    """Test KPI dropdown behavior on activity dashboard"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        try:
            print("\n\n🚀 Testing KPI Dropdowns on Activity Dashboard")
            print("=" * 50)
            
            # Navigate to dashboard first
            await page.goto("http://127.0.0.1:8890")
            
            # Login if needed
            if await page.is_visible('input[name="email"]'):
                await page.fill('input[name="email"]', 'kdresdell@gmail.com')
                await page.fill('input[name="password"]', 'admin123')
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
            
            # Find and click on an activity dashboard link
            activity_links = await page.query_selector_all('a[href*="activity_dashboard"]')
            if not activity_links:
                print("❌ No activity dashboard links found")
                return False
            
            await activity_links[0].click()
            await page.wait_for_load_state('networkidle')
            print("✅ Navigated to activity dashboard")
            
            # Wait for activity dashboard to load
            await page.wait_for_selector('.card', timeout=5000)
            
            # Take initial screenshot
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/activity-dashboard-initial.png")
            print("📸 Initial activity dashboard screenshot")
            
            # Find KPI dropdown buttons on activity dashboard
            activity_kpi_dropdowns = await page.query_selector_all('[data-bs-toggle="dropdown"]')
            kpi_dropdowns = []
            
            # Filter for KPI dropdowns (ones in cards with KPI content)
            for dropdown in activity_kpi_dropdowns:
                card = await dropdown.evaluate('el => el.closest(".card")')
                if card:
                    card_text = await page.evaluate('el => el.textContent.toLowerCase()', card)
                    if any(kpi in card_text for kpi in ['revenue', 'users', 'profit', 'passports']):
                        kpi_dropdowns.append(dropdown)
            
            print(f"🔍 Found {len(kpi_dropdowns)} KPI dropdown buttons on activity dashboard")
            
            if len(kpi_dropdowns) == 0:
                print("❌ No KPI dropdown buttons found on activity dashboard!")
                return False
            
            # Test activity dashboard dropdowns
            print("\n🧪 Test 1: Opening first activity KPI dropdown")
            await kpi_dropdowns[0].click()
            await page.wait_for_timeout(500)
            
            first_menu = await page.query_selector('.dropdown-menu.show')
            if first_menu:
                print("✅ First activity KPI dropdown opened")
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/activity-dashboard-first-dropdown.png")
            else:
                print("❌ First activity KPI dropdown failed to open")
                return False
            
            # Test multiple dropdowns
            if len(kpi_dropdowns) > 1:
                print("\n🧪 Test 2: Opening second activity KPI dropdown")
                await kpi_dropdowns[1].click()
                await page.wait_for_timeout(500)
                
                open_menus = await page.query_selector_all('.dropdown-menu.show')
                print(f"🔍 Open dropdown menus: {len(open_menus)}")
                
                if len(open_menus) <= 1:
                    print("✅ Only one activity dropdown open at a time")
                    await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/activity-dashboard-second-dropdown.png")
                else:
                    print("❌ Multiple activity dropdowns open simultaneously")
                    await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/activity-dashboard-multiple-error.png")
            
            # Test click outside
            print("\n🧪 Test 3: Click outside to close activity dropdown")
            await page.click('body', position={"x": 50, "y": 50})
            await page.wait_for_timeout(500)
            
            open_menus = await page.query_selector_all('.dropdown-menu.show')
            if len(open_menus) == 0:
                print("✅ Click outside closes activity dropdowns")
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/activity-dashboard-click-outside.png")
            else:
                print("❌ Click outside failed to close activity dropdowns")
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/activity-dashboard-click-outside-error.png")
            
            return True
            
        except Exception as e:
            print(f"❌ Activity dashboard test failed: {e}")
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/activity-dashboard-error.png")
            return False
        finally:
            await browser.close()

async def main():
    """Run all dropdown tests"""
    print("🧪 KPI Dropdown Test Suite")
    print("=" * 60)
    
    # Test main dashboard
    dashboard_success = await test_dashboard_kpi_dropdowns()
    
    # Test activity dashboard
    activity_success = await test_activity_dashboard_kpi_dropdowns()
    
    print("\n" + "=" * 60)
    print("🎯 Test Results Summary:")
    print(f"Main Dashboard: {'✅ PASS' if dashboard_success else '❌ FAIL'}")
    print(f"Activity Dashboard: {'✅ PASS' if activity_success else '❌ FAIL'}")
    
    if dashboard_success and activity_success:
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)