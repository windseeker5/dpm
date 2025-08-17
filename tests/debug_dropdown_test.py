#!/usr/bin/env python3
"""
Debug Dropdown Test - Get console output and detailed debugging
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_dropdown_issues():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Capture console messages
        def handle_console(msg):
            print(f"CONSOLE: {msg.type.upper()}: {msg.text}")
        
        page.on("console", handle_console)
        
        try:
            print("🔍 Debug test - checking console output...")
            
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
            
            # Check if dropdown fix is available
            dropdown_fix_available = await page.evaluate("typeof window.dropdownFix !== 'undefined'")\n            print(f"Dropdown fix available: {dropdown_fix_available}")
            
            # Get debug info
            if dropdown_fix_available:
                debug_info = await page.evaluate("window.dropdownFix.debug()")
                print("Debug info logged to console")
            
            # Find first KPI dropdown and click it
            kpi_dropdown = await page.query_selector('.kpi-section [data-bs-toggle="dropdown"]')
            if not kpi_dropdown:
                print("❌ No KPI dropdown found")
                return
            
            print("🔍 Clicking first dropdown...")
            await kpi_dropdown.click()
            await page.wait_for_timeout(1000)
            
            # Force visibility using our function
            if dropdown_fix_available:
                await page.evaluate("window.dropdownFix.forceVisibility()")
                print("✅ Called forceVisibility function")
            
            # Check dropdown state
            dropdown_state = await page.evaluate("""() => {
                const menu = document.querySelector('.dropdown-menu.show');
                if (!menu) return { found: false };
                
                const styles = window.getComputedStyle(menu);
                const rect = menu.getBoundingClientRect();
                
                return {
                    found: true,
                    hasShowClass: menu.classList.contains('show'),
                    styles: {
                        display: styles.display,
                        opacity: styles.opacity,
                        visibility: styles.visibility,
                        position: styles.position,
                        top: styles.top,
                        left: styles.left,
                        zIndex: styles.zIndex,
                        transform: styles.transform
                    },
                    inlineStyles: {
                        display: menu.style.display,
                        opacity: menu.style.opacity,
                        visibility: menu.style.visibility,
                        position: menu.style.position,
                        top: menu.style.top,
                        left: menu.style.left,
                        zIndex: menu.style.zIndex
                    },
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    offsetParent: menu.offsetParent ? menu.offsetParent.tagName : null
                };
            }""")
            
            print("Dropdown state analysis:")
            print(f"  Found: {dropdown_state.get('found', False)}")
            if dropdown_state.get('found'):
                print(f"  Has show class: {dropdown_state.get('hasShowClass', False)}")
                print(f"  Computed styles: {dropdown_state.get('styles', {})}")
                print(f"  Inline styles: {dropdown_state.get('inlineStyles', {})}")
                print(f"  Bounding box: {dropdown_state.get('boundingBox', {})}")
                print(f"  Offset parent: {dropdown_state.get('offsetParent', 'None')}")
            
            # Take screenshot
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/debug-dropdown-state.png")
            print("📸 Debug screenshot saved")
            
            # Try to manually fix the dropdown
            manual_fix_result = await page.evaluate("""() => {
                const menu = document.querySelector('.dropdown-menu.show');
                if (!menu) return 'No menu found';
                
                // Apply all possible fixes
                menu.style.display = 'block';
                menu.style.opacity = '1';
                menu.style.visibility = 'visible';
                menu.style.position = 'absolute';
                menu.style.top = '100%';
                menu.style.left = '0';
                menu.style.zIndex = '9999';
                menu.style.transform = 'none';
                menu.style.pointerEvents = 'auto';
                menu.style.backgroundColor = 'white';
                menu.style.border = '1px solid #ccc';
                menu.style.borderRadius = '4px';
                menu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
                menu.style.minWidth = '160px';
                menu.style.padding = '5px 0';
                
                const rect = menu.getBoundingClientRect();
                return `Fixed: ${rect.width}x${rect.height} at ${rect.x},${rect.y}`;
            }""")
            
            print(f"Manual fix result: {manual_fix_result}")
            
            # Take another screenshot after manual fix
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/debug-dropdown-manual-fix.png")
            print("📸 Manual fix screenshot saved")
            
            # Wait a bit more to see if it appears
            await page.wait_for_timeout(2000)
            
            # Final check
            final_visible = await page.query_selector('.dropdown-menu.show')
            is_visible = await final_visible.is_visible() if final_visible else False
            print(f"Final visibility check: {is_visible}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/debug-error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dropdown_issues())