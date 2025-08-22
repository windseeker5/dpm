#!/usr/bin/env python3
"""
Clean Debug Test for Dropdown Issues
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_dropdown():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Capture console messages
        console_logs = []
        def handle_console(msg):
            log_message = f"CONSOLE: {msg.type.upper()}: {msg.text}"
            console_logs.append(log_message)
            print(log_message)
        
        page.on("console", handle_console)
        
        try:
            print("🔍 Clean debug test starting...")
            
            await page.goto("http://127.0.0.1:8890")
            
            if await page.is_visible('input[name="email"]'):
                await page.fill('input[name="email"]', 'kdresdell@gmail.com')
                await page.fill('input[name="password"]', 'admin123')
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                print("✅ Logged in")
            
            await page.wait_for_selector('.kpi-section', timeout=5000)
            print("✅ Dashboard loaded")
            
            # Check dropdown fix availability
            has_dropdown_fix = await page.evaluate("typeof window.dropdownFix !== 'undefined'")
            print(f"Dropdown fix loaded: {has_dropdown_fix}")
            
            # Click first dropdown
            kpi_dropdown = await page.query_selector('.kpi-section [data-bs-toggle="dropdown"]')
            if kpi_dropdown:
                print("🔍 Clicking dropdown...")
                await kpi_dropdown.click()
                await page.wait_for_timeout(1000)
                
                # Analyze dropdown state
                state = await page.evaluate("""() => {
                    const menu = document.querySelector('.dropdown-menu.show');
                    if (!menu) return { found: false };
                    
                    const computed = window.getComputedStyle(menu);
                    const rect = menu.getBoundingClientRect();
                    
                    return {
                        found: true,
                        display: computed.display,
                        opacity: computed.opacity,
                        visibility: computed.visibility,
                        position: computed.position,
                        zIndex: computed.zIndex,
                        width: rect.width,
                        height: rect.height,
                        x: rect.x,
                        y: rect.y
                    };
                }""")
                
                print("Dropdown analysis:")
                for key, value in state.items():
                    print(f"  {key}: {value}")
                
                # Try manual fix
                await page.evaluate("""() => {
                    const menu = document.querySelector('.dropdown-menu.show');
                    if (menu) {
                        menu.style.display = 'block';
                        menu.style.opacity = '1';
                        menu.style.visibility = 'visible';
                        menu.style.position = 'absolute';
                        menu.style.zIndex = '9999';
                        menu.style.backgroundColor = 'white';
                        menu.style.border = '1px solid red';
                        menu.style.padding = '10px';
                        menu.style.minWidth = '160px';
                        console.log('Applied manual fix to dropdown');
                    }
                }""")
                
                await page.wait_for_timeout(1000)
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/clean-debug-result.png")
                print("📸 Screenshot saved")
                
            else:
                print("❌ No dropdown found")
            
            # Print all console logs
            print("\n📝 Console logs:")
            for log in console_logs:
                print(f"  {log}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dropdown())