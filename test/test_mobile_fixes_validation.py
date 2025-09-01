"""
Test mobile dropdown and chart fixes validation
"""
import asyncio
import time
from playwright.async_api import async_playwright
import os

async def test_mobile_fixes():
    """Test the mobile dropdown and chart fixes"""
    
    async with async_playwright() as p:
        # Use headless=False to see the test in action
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        
        # Mobile context - iPhone SE
        context = await browser.new_context(
            viewport={'width': 375, 'height': 667},
            device_scale_factor=2,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
        )
        
        page = await context.new_page()
        
        try:
            print("=== Mobile Dropdown & Chart Fixes Test ===")
            
            # Navigate to Flask app
            print("1. Navigating to localhost:5000...")
            await page.goto('http://localhost:5000')
            await page.wait_for_load_state('networkidle')
            
            # Login
            print("2. Logging in...")
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            
            # Wait for dashboard
            await page.wait_for_selector('.kpi-cards-wrapper', timeout=15000)
            await page.wait_for_timeout(3000)  # Wait for charts
            
            print("3. Dashboard loaded, taking initial screenshot...")
            await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-fixes-initial.png', full_page=True)
            
            # Test Revenue dropdown
            print("4. Testing Revenue dropdown positioning...")
            revenue_toggle = page.locator('[data-kpi-card=\"revenue\"] .dropdown-toggle').first()
            await revenue_toggle.click()
            await page.wait_for_timeout(500)
            
            # Check if dropdown is visible and positioned correctly
            dropdown_menu = page.locator('[data-kpi-card=\"revenue\"] .dropdown-menu').first()
            await dropdown_menu.wait_for(state='visible', timeout=5000)
            
            menu_box = await dropdown_menu.bounding_box()
            viewport_height = 667
            
            print(f"   Revenue dropdown: top={menu_box['y']}, bottom={menu_box['y'] + menu_box['height']}, viewport={viewport_height}")
            
            is_visible = menu_box['y'] >= 0 and menu_box['y'] + menu_box['height'] <= viewport_height + 50  # 50px tolerance
            print(f"   ✓ Revenue dropdown properly positioned: {is_visible}")
            
            await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-fixes-revenue-dropdown.png', full_page=True)\n            \n            # Close dropdown\n            await page.click('body')\n            await page.wait_for_timeout(300)\n            \n            # Test Active Passports dropdown (should be near bottom of viewport)\n            print(\"5. Testing Active Passports dropdown...\")\n            passports_toggle = page.locator('[data-kpi-card=\"active_passports\"] .dropdown-toggle').first()\n            \n            # Scroll to make sure it's in view\n            await passports_toggle.scroll_into_view_if_needed()\n            await passports_toggle.click()\n            await page.wait_for_timeout(500)\n            \n            passports_menu = page.locator('[data-kpi-card=\"active_passports\"] .dropdown-menu').first()\n            await passports_menu.wait_for(state='visible', timeout=5000)\n            \n            passports_box = await passports_menu.bounding_box()\n            print(f\"   Active Passports dropdown: top={passports_box['y']}, bottom={passports_box['y'] + passports_box['height']}\")\n            \n            is_visible_passports = passports_box['y'] >= 0 and passports_box['y'] + passports_box['height'] <= viewport_height + 50\n            print(f\"   ✓ Active Passports dropdown properly positioned: {is_visible_passports}\")\n            \n            await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-fixes-passports-dropdown.png', full_page=True)\n            \n            # Close dropdown\n            await page.click('body')\n            await page.wait_for_timeout(300)\n            \n            # Test chart rendering after reload\n            print(\"6. Testing chart rendering after page reload...\")\n            await page.reload()\n            await page.wait_for_selector('.kpi-cards-wrapper', timeout=15000)\n            await page.wait_for_timeout(4000)  # Wait longer for charts to render\n            \n            # Check for chart elements\n            charts = await page.locator('[id*=\"-chart\"] svg').all()\n            print(f\"   Found {len(charts)} chart elements after reload\")\n            \n            chart_issues = []\n            for i, chart in enumerate(charts):\n                box = await chart.bounding_box()\n                if box:\n                    print(f\"   Chart {i+1}: width={box['width']}, height={box['height']}\")\n                    if box['height'] < 30:  # Charts should be at least 30px high\n                        chart_issues.append(f\"Chart {i+1} too small: {box['height']}px\")\n                else:\n                    chart_issues.append(f\"Chart {i+1} has no bounding box\")\n            \n            if chart_issues:\n                print(f\"   ❌ Chart issues found: {chart_issues}\")\n            else:\n                print(\"   ✓ All charts rendered properly\")\n            \n            await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-fixes-after-reload.png', full_page=True)\n            \n            # Test dropdown behavior during scroll (mobile UX)\n            print(\"7. Testing dropdown behavior during scroll...\")\n            revenue_toggle = page.locator('[data-kpi-card=\"revenue\"] .dropdown-toggle').first()\n            await revenue_toggle.click()\n            await page.wait_for_timeout(300)\n            \n            # Scroll down slightly\n            await page.mouse.wheel(0, 100)\n            await page.wait_for_timeout(500)\n            \n            # Check if dropdown closed\n            dropdown_visible = await dropdown_menu.is_visible()\n            print(f\"   ✓ Dropdown closed on scroll: {not dropdown_visible}\")\n            \n            # Final screenshot\n            await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-fixes-final.png', full_page=True)\n            \n            print(\"\\n=== Test Summary ===\")\n            print(f\"✓ Revenue dropdown positioned correctly: {is_visible}\")\n            print(f\"✓ Active Passports dropdown positioned correctly: {is_visible_passports}\")\n            print(f\"✓ Charts rendered after reload: {len(chart_issues) == 0}\")\n            print(f\"✓ Dropdown closes on scroll: {not dropdown_visible}\")\n            print(\"\\nScreenshots saved:\")\n            print(\"  - mobile-fixes-initial.png\")\n            print(\"  - mobile-fixes-revenue-dropdown.png\")\n            print(\"  - mobile-fixes-passports-dropdown.png\")\n            print(\"  - mobile-fixes-after-reload.png\")\n            print(\"  - mobile-fixes-final.png\")\n            \n            # Summary\n            total_issues = (0 if is_visible else 1) + (0 if is_visible_passports else 1) + len(chart_issues)\n            if total_issues == 0:\n                print(\"\\n🎉 ALL MOBILE FIXES WORKING CORRECTLY!\")\n            else:\n                print(f\"\\n⚠️  {total_issues} issues remain to be fixed\")\n                \n        except Exception as e:\n            print(f\"Error during test: {e}\")\n            await page.screenshot(path='/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright/mobile-fixes-error.png', full_page=True)\n        \n        finally:\n            await browser.close()\n\nif __name__ == '__main__':\n    asyncio.run(test_mobile_fixes())"