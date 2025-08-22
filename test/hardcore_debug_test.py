#!/usr/bin/env python3
"""
Hardcore Debug Test - Extreme debugging and manual fixes
"""
import asyncio
from playwright.async_api import async_playwright

async def hardcore_debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=3000)
        page = await browser.new_page()
        
        try:
            print("🔧 Hardcore debugging mode - extreme measures")
            
            await page.goto("http://127.0.0.1:8890")
            
            if await page.is_visible('input[name="email"]'):
                await page.fill('input[name="email"]', 'kdresdell@gmail.com')
                await page.fill('input[name="password"]', 'admin123')
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                print("✅ Logged in")
            
            await page.wait_for_selector('.kpi-section', timeout=5000)
            print("✅ Dashboard loaded")
            
            # Step 1: Analyze all CSS rules affecting dropdown-menu
            css_analysis = await page.evaluate("""() => {
                const menu = document.querySelector('.dropdown-menu');
                if (!menu) return 'No dropdown menu found';
                
                const computed = window.getComputedStyle(menu);
                const allRules = [];
                
                // Get all stylesheets
                for (let sheet of document.styleSheets) {
                    try {
                        for (let rule of sheet.cssRules) {
                            if (rule.selectorText && rule.selectorText.includes('dropdown-menu')) {
                                allRules.push({
                                    selector: rule.selectorText,
                                    cssText: rule.cssText,
                                    specificity: rule.selectorText.split(' ').length
                                });
                            }
                        }
                    } catch (e) {
                        // Cross-origin or other error
                    }
                }
                
                return {
                    computedDisplay: computed.display,
                    rules: allRules.slice(0, 10), // First 10 rules
                    totalRules: allRules.length
                };
            }""")
            
            print("CSS Analysis:")
            print(f"  Computed display: {css_analysis.get('computedDisplay', 'unknown')}")
            print(f"  Total dropdown-menu rules found: {css_analysis.get('totalRules', 0)}")
            
            # Click dropdown to open it
            kpi_dropdown = await page.query_selector('.kpi-section [data-bs-toggle="dropdown"]')
            if kpi_dropdown:
                print("🔍 Opening dropdown...")
                await kpi_dropdown.click()
                await page.wait_for_timeout(1000)
                
                # Step 2: Extreme manual intervention
                print("🚨 Applying extreme manual fixes...")
                
                extreme_fix_result = await page.evaluate("""() => {
                    const menu = document.querySelector('.dropdown-menu.show');
                    if (!menu) return 'No dropdown menu with show class found';
                    
                    // Log current state
                    const beforeState = {
                        display: window.getComputedStyle(menu).display,
                        visibility: window.getComputedStyle(menu).visibility,
                        opacity: window.getComputedStyle(menu).opacity,
                        classes: Array.from(menu.classList),
                        innerHTML: menu.innerHTML.substring(0, 100)
                    };
                    
                    // Extreme fix 1: Remove all classes and re-add
                    menu.className = '';
                    menu.classList.add('dropdown-menu', 'show');
                    
                    // Extreme fix 2: Set all possible style properties
                    menu.style.cssText = `
                        display: block !important;
                        opacity: 1 !important;
                        visibility: visible !important;
                        position: absolute !important;
                        top: 100% !important;
                        left: 0 !important;
                        z-index: 99999 !important;
                        background-color: white !important;
                        border: 2px solid red !important;
                        padding: 10px !important;
                        min-width: 200px !important;
                        max-width: 300px !important;
                        height: auto !important;
                        margin: 0 !important;
                        transform: none !important;
                        clip: none !important;
                        overflow: visible !important;
                        color: black !important;
                        font-size: 14px !important;
                    `;
                    
                    // Extreme fix 3: Create entirely new dropdown menu
                    const newMenu = document.createElement('div');
                    newMenu.style.cssText = `
                        position: absolute !important;
                        top: 100% !important;
                        left: 0 !important;
                        z-index: 99999 !important;
                        background-color: yellow !important;
                        border: 3px solid red !important;
                        padding: 20px !important;
                        min-width: 200px !important;
                        color: black !important;
                        font-size: 16px !important;
                        font-weight: bold !important;
                    `;
                    newMenu.innerHTML = `
                        <div style="padding: 10px; border-bottom: 1px solid black;">Last 7 days</div>
                        <div style="padding: 10px; border-bottom: 1px solid black;">Last 30 days</div>
                        <div style="padding: 10px;">Last 90 days</div>
                    `;
                    
                    // Append to dropdown parent
                    const dropdown = menu.closest('.dropdown');
                    if (dropdown) {
                        dropdown.appendChild(newMenu);
                    }
                    
                    const afterState = {
                        display: window.getComputedStyle(menu).display,
                        visibility: window.getComputedStyle(menu).visibility,
                        opacity: window.getComputedStyle(menu).opacity,
                        position: menu.getBoundingClientRect()
                    };
                    
                    return {
                        beforeState,
                        afterState,
                        newMenuCreated: !!newMenu.parentElement
                    };
                }""")
                
                print("Extreme fix results:")
                print(f"  Before display: {extreme_fix_result.get('beforeState', {}).get('display', 'unknown')}")
                print(f"  After display: {extreme_fix_result.get('afterState', {}).get('display', 'unknown')}")
                print(f"  New menu created: {extreme_fix_result.get('newMenuCreated', False)}")
                
                # Take screenshot after extreme fixes
                await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/tests/hardcore-debug-result.png")
                print("📸 Extreme fix screenshot saved")
                
                # Wait to see results
                await page.wait_for_timeout(3000)
                
            else:
                print("❌ No dropdown found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(hardcore_debug())