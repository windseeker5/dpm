"""
Test mobile dropdown issues on dashboard - reproducing user-reported problems
"""
import asyncio
from playwright.async_api import async_playwright
import json
import os

async def test_mobile_dropdown_issues():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        
        # Mobile viewport - iPhone SE dimensions as specified
        context = await browser.new_context(
            viewport={'width': 375, 'height': 667},
            device_scale_factor=2,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
        )
        
        page = await context.new_page()
        
        # Navigate to Flask app
        await page.goto('http://localhost:5000')
        
        print("1. Testing mobile dropdown visibility issues...")
        
        # Wait for login form
        await page.wait_for_selector('input[name="email"]')
        
        # Login
        await page.fill('input[name="email"]', 'kdresdell@gmail.com')
        await page.fill('input[name="password"]', 'admin123')
        await page.click('button[type="submit"]')
        
        # Wait for dashboard to load
        await page.wait_for_selector('.kpi-cards-wrapper', timeout=10000)
        await page.wait_for_timeout(2000)  # Wait for charts to load
        
        # Take initial screenshot
        await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-initial-state.png', full_page=True)
        print("✓ Initial mobile dashboard screenshot taken")
        
        # Test dropdown positioning issues
        print("2. Testing Revenue dropdown behavior...")
        
        # Find revenue card dropdown
        revenue_dropdown = page.locator('[data-kpi-card="revenue"] .dropdown-toggle').first()
        await revenue_dropdown.wait_for(state='visible')
        
        # Click to open dropdown
        await revenue_dropdown.click()
        await page.wait_for_timeout(500)  # Wait for dropdown animation
        
        # Check if dropdown menu is visible and get its position
        dropdown_menu = page.locator('[data-kpi-card="revenue"] .dropdown-menu').first()
        await dropdown_menu.wait_for(state='visible')
        
        # Get dropdown menu bounding box
        menu_box = await dropdown_menu.bounding_box()
        viewport_height = 667
        
        print(f"   Dropdown menu position: top={menu_box['y']}, bottom={menu_box['y'] + menu_box['height']}")
        print(f"   Viewport height: {viewport_height}")
        
        if menu_box['y'] + menu_box['height'] > viewport_height:
            print("   ❌ ISSUE: Dropdown extends below viewport!")
        else:
            print("   ✓ Dropdown fits within viewport")
        
        # Take screenshot of open dropdown
        await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-revenue-dropdown-open.png', full_page=True)
        
        # Close dropdown by clicking elsewhere
        await page.click('body')
        await page.wait_for_timeout(500)
        
        # Test Active Passports dropdown
        print("3. Testing Active Passports dropdown behavior...")
        
        active_passports_dropdown = page.locator('[data-kpi-card="active_passports"] .dropdown-toggle').first()
        await active_passports_dropdown.scroll_into_view_if_needed()
        await active_passports_dropdown.click()
        await page.wait_for_timeout(500)
        
        # Get Active Passports dropdown menu position
        active_menu = page.locator('[data-kpi-card="active_passports"] .dropdown-menu').first()
        await active_menu.wait_for(state='visible')
        
        active_menu_box = await active_menu.bounding_box()
        print(f"   Active Passports dropdown position: top={active_menu_box['y']}, bottom={active_menu_box['y'] + active_menu_box['height']}")
        
        if active_menu_box['y'] + active_menu_box['height'] > viewport_height:
            print("   ❌ ISSUE: Active Passports dropdown extends below viewport!")
        else:
            print("   ✓ Active Passports dropdown fits within viewport")
        
        await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-active-passports-dropdown-open.png', full_page=True)
        
        # Close dropdown
        await page.click('body')
        await page.wait_for_timeout(500)
        
        print("4. Testing chart white gap issue after page reload...")
        
        # Reload page to test chart rendering issue
        await page.reload()
        await page.wait_for_selector('.kpi-cards-wrapper', timeout=10000)
        await page.wait_for_timeout(3000)  # Wait longer for charts to fully load
        
        # Take screenshot after reload to check for white gaps
        await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-after-reload.png', full_page=True)
        print("✓ After reload screenshot taken")
        
        # Check for any chart elements that might have white gaps
        chart_elements = await page.locator('.apexcharts-svg').all()
        print(f"   Found {len(chart_elements)} chart elements")
        
        for i, chart in enumerate(chart_elements):
            box = await chart.bounding_box()
            if box:
                print(f"   Chart {i+1}: width={box['width']}, height={box['height']}")
        
        print("5. Testing dropdown z-index stacking...")
        
        # Test if dropdowns appear above other elements
        revenue_dropdown = page.locator('[data-kpi-card="revenue"] .dropdown-toggle').first()
        await revenue_dropdown.click()
        await page.wait_for_timeout(500)
        
        # Get z-index of dropdown menu
        dropdown_menu = page.locator('[data-kpi-card="revenue"] .dropdown-menu').first()
        z_index = await dropdown_menu.evaluate('element => getComputedStyle(element).zIndex')
        print(f"   Revenue dropdown z-index: {z_index}")
        
        # Check if dropdown is properly positioned
        menu_box = await dropdown_menu.bounding_box()
        card_box = await page.locator('[data-kpi-card="revenue"] .card').first().bounding_box()
        
        print(f"   Card position: top={card_box['y']}")
        print(f"   Menu position: top={menu_box['y']}")
        
        # Take final screenshot with dropdown open
        await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-final-dropdown-test.png', full_page=True)
        
        print("6. Test results summary:")
        print("   - All screenshots saved to /test/playwright/ directory")
        print("   - Check screenshots for visual issues:")
        print("     * mobile-revenue-dropdown-open.png - Revenue dropdown positioning")
        print("     * mobile-active-passports-dropdown-open.png - Active Passports dropdown")
        print("     * mobile-after-reload.png - Chart white gap issue")
        print("     * mobile-final-dropdown-test.png - Z-index stacking")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_mobile_dropdown_issues())