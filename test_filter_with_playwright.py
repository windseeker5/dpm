#!/usr/bin/env python3
"""
Test the activity dashboard filter functionality using Playwright for full browser automation
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def test_filter_functionality_browser():
    """Test filter functionality with full browser automation"""
    
    print("🧪 ACTIVITY DASHBOARD FILTER TEST (Browser Automation)")
    print("=" * 65)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable network monitoring
        network_requests = []
        
        def handle_request(request):
            if 'activity-dashboard-data' in request.url:
                network_requests.append({
                    'url': request.url,
                    'method': request.method
                })
                print(f"   📡 AJAX Request: {request.method} {request.url}")
        
        page.on("request", handle_request)
        
        try:
            # Step 1: Login
            print("\n1. Logging in...")
            await page.goto("http://127.0.0.1:8890/login")
            await page.wait_for_load_state('networkidle')
            
            # Fill login form
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            current_url = page.url
            if 'login' in current_url:
                print("   ❌ Login failed - still on login page")
                return
            else:
                print("   ✅ Login successful")
            
            # Step 2: Navigate to activity dashboard
            print("\n2. Navigating to activity dashboard...")
            await page.goto("http://127.0.0.1:8890/activity-dashboard/1")
            await page.wait_for_load_state('networkidle')
            
            final_url = page.url
            if 'activity-dashboard' in final_url:
                print("   ✅ Activity dashboard loaded")
            else:
                print(f"   ❌ Redirected to: {final_url}")
                return
            
            # Step 3: Check for filter buttons
            print("\n3. Checking for filter buttons...")
            
            # Check passport filter buttons
            passport_buttons = await page.query_selector_all('button[onclick*="filterPassports"]')
            print(f"   ✅ Found {len(passport_buttons)} passport filter buttons")
            
            # Check signup filter buttons
            signup_buttons = await page.query_selector_all('button[onclick*="filterSignups"]')
            print(f"   ✅ Found {len(signup_buttons)} signup filter buttons")
            
            # Check for specific button IDs
            button_ids = ['filter-all', 'filter-unpaid', 'filter-paid', 'filter-active',
                         'signup-filter-all', 'signup-filter-unpaid', 'signup-filter-paid', 
                         'signup-filter-pending', 'signup-filter-approved']
            
            found_buttons = []
            for button_id in button_ids:
                button = await page.query_selector(f'#{button_id}')
                if button:
                    found_buttons.append(button_id)
                    
            print(f"   ✅ Found button IDs: {found_buttons}")
            
            # Step 4: Test clicking filter buttons
            print("\n4. Testing filter button clicks...")
            
            if len(passport_buttons) > 0:
                print("   Testing passport filters...")
                for i, button in enumerate(passport_buttons[:3]):  # Test first 3 buttons
                    button_text = await button.inner_text()
                    print(f"   📱 Clicking: {button_text.strip()}")
                    
                    # Clear previous requests
                    network_requests.clear()
                    
                    await button.click()
                    await page.wait_for_timeout(2000)  # Wait for AJAX
                    
                    if network_requests:
                        print(f"      ✅ AJAX request made: {network_requests[0]['url']}")
                    else:
                        print("      ❌ No AJAX request detected")
            
            if len(signup_buttons) > 0:
                print("   Testing signup filters...")
                for i, button in enumerate(signup_buttons[:3]):  # Test first 3 buttons
                    button_text = await button.inner_text()
                    print(f"   📱 Clicking: {button_text.strip()}")
                    
                    # Clear previous requests
                    network_requests.clear()
                    
                    await button.click()
                    await page.wait_for_timeout(2000)  # Wait for AJAX
                    
                    if network_requests:
                        print(f"      ✅ AJAX request made: {network_requests[0]['url']}")
                    else:
                        print("      ❌ No AJAX request detected")
            
            # Step 5: Check JavaScript functions exist
            print("\n5. Checking JavaScript functions...")
            
            # Test if filterPassports function exists
            passport_fn_exists = await page.evaluate("typeof filterPassports === 'function'")
            print(f"   filterPassports function: {'✅ Exists' if passport_fn_exists else '❌ Missing'}")
            
            # Test if filterSignups function exists
            signup_fn_exists = await page.evaluate("typeof filterSignups === 'function'")
            print(f"   filterSignups function: {'✅ Exists' if signup_fn_exists else '❌ Missing'}")
            
            # Step 6: Check URL updates
            print("\n6. Testing URL updates...")
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            if 'passport_filter' in current_url or 'signup_filter' in current_url:
                print("   ✅ URL contains filter parameters")
            else:
                print("   ⚠️  URL does not contain filter parameters")
            
            # Step 7: Check table structure
            print("\n7. Checking table structure...")
            tables = await page.query_selector_all('table')
            print(f"   ✅ Found {len(tables)} tables on page")
            
            tbody_elements = await page.query_selector_all('tbody')
            print(f"   ✅ Found {len(tbody_elements)} tbody elements")
            
            # Take a screenshot for verification
            await page.screenshot(path=".playwright-mcp/filter-test-final.png", full_page=True)
            print("   📸 Screenshot saved: .playwright-mcp/filter-test-final.png")
            
        except Exception as e:
            print(f"   ❌ Error during test: {e}")
            await page.screenshot(path=".playwright-mcp/filter-test-error.png", full_page=True)
            
        finally:
            await browser.close()
    
    print("\n✅ BROWSER TEST COMPLETE")
    print(f"   Total AJAX requests detected: {len([r for r in network_requests if r])}")
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("   If filter buttons are found but no AJAX requests are made:")
    print("   - Check JavaScript console for errors")
    print("   - Verify onclick handlers are properly attached")
    print("   - Check if functions are defined in global scope")
    print("   If no filter buttons found:")
    print("   - Check if you're on the correct activity dashboard")
    print("   - Verify the activity has passports/signups to show filters")

if __name__ == "__main__":
    asyncio.run(test_filter_functionality_browser())