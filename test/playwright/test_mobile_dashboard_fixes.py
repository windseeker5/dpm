"""
Test mobile dashboard critical issues: chart white gap on refresh and dropdown styling
"""
import asyncio
from playwright.async_api import async_playwright
import time
import os

async def test_mobile_dashboard_issues():
    """Test the two critical mobile dashboard issues"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 375, 'height': 667},  # Mobile viewport
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15'
        )
        page = await context.new_page()
        
        try:
            print("🔍 Testing mobile dashboard critical issues...")
            
            # Navigate to login page
            await page.goto('http://localhost:5000/login')
            await page.wait_for_load_state('networkidle')
            
            # Login
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Navigate to dashboard
            await page.goto('http://localhost:5000/dashboard')
            await page.wait_for_load_state('networkidle')
            
            # Wait for charts to render
            await page.wait_for_timeout(2000)
            
            # Take screenshot of initial state
            screenshot_dir = '/home/kdresdell/Documents/DEV/minipass_env/app/test/playwright'
            os.makedirs(screenshot_dir, exist_ok=True)
            
            await page.screenshot(path=f'{screenshot_dir}/mobile_dashboard_before_refresh.png')
            print("📸 Screenshot taken: mobile_dashboard_before_refresh.png")
            
            # Issue 1: Test chart rendering after page refresh
            print("\n🔄 Testing chart rendering after page refresh...")
            await page.reload()
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)  # Give charts time to render
            
            # Check if charts are properly rendered (look for SVG elements)
            revenue_chart = await page.query_selector('#revenue-chart svg')
            if revenue_chart:
                print("✅ Revenue chart SVG found after refresh")
            else:
                print("❌ Revenue chart SVG missing after refresh - WHITE GAP ISSUE!")
            
            await page.screenshot(path=f'{screenshot_dir}/mobile_dashboard_after_refresh.png')
            print("📸 Screenshot taken: mobile_dashboard_after_refresh.png")
            
            # Issue 2: Test dropdown styling
            print("\n📋 Testing dropdown styling...")
            
            # Find the first dropdown (revenue card)
            revenue_dropdown = await page.query_selector('.kpi-card-mobile:first-child .dropdown-toggle')
            if revenue_dropdown:
                # Click to open dropdown
                await revenue_dropdown.click()
                await page.wait_for_timeout(500)
                
                # Check if dropdown is visible
                dropdown_menu = await page.query_selector('.kpi-card-mobile:first-child .dropdown-menu.show')
                if dropdown_menu:
                    print("✅ Dropdown menu opened successfully")
                    
                    # Take screenshot of dropdown
                    await page.screenshot(path=f'{screenshot_dir}/mobile_dropdown_styling.png')
                    print("📸 Screenshot taken: mobile_dropdown_styling.png")
                    
                    # Check all dropdown items
                    dropdown_items = await page.query_selector_all('.kpi-card-mobile:first-child .dropdown-menu .dropdown-item')
                    print(f"📊 Found {len(dropdown_items)} dropdown items")
                    
                    # Check the last item (All time) for styling issues
                    if dropdown_items:
                        last_item = dropdown_items[-1]
                        last_item_text = await last_item.text_content()
                        print(f"🎯 Last dropdown item: '{last_item_text}'")
                        
                        # Get computed styles of last item
                        last_item_styles = await page.evaluate("""
                            (element) => {
                                const styles = window.getComputedStyle(element);
                                return {
                                    borderBottom: styles.borderBottom,
                                    borderBottomWidth: styles.borderBottomWidth,
                                    borderBottomStyle: styles.borderBottomStyle,
                                    borderRadius: styles.borderRadius,
                                    marginBottom: styles.marginBottom,
                                    paddingBottom: styles.paddingBottom
                                };
                            }
                        """, last_item)
                        
                        print(f"🎨 Last item styles: {last_item_styles}")
                        
                else:
                    print("❌ Dropdown menu failed to open")
            
            # Close dropdown by clicking outside
            await page.click('body')
            await page.wait_for_timeout(500)
            
            print("\n📊 Test completed. Check screenshots for visual issues.")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            await page.screenshot(path=f'{screenshot_dir}/mobile_dashboard_error.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_mobile_dashboard_issues())