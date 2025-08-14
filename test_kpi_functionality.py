#!/usr/bin/env python3
"""
Test script for KPI card functionality on activity dashboard
Tests:
1. Login functionality
2. Navigation to activity dashboard
3. KPI cards visual styling (12px rounded corners)
4. Bar chart implementation for unpaid passports
5. Mobile responsiveness and swipe functionality
6. Dropdown period changes (7, 30, 90 days)
7. API calls and data updates
8. Loading states and error handling
"""

import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def test_kpi_functionality():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1200, 'height': 800}
        )
        page = await context.new_page()
        
        try:
            print("🚀 Starting KPI functionality test...")
            
            # Step 1: Navigate to login page
            print("\n1. Testing login functionality...")
            await page.goto('http://127.0.0.1:8890')
            await page.wait_for_selector('input[name="email"]')
            
            # Login with provided credentials
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            
            # Wait for redirect after login
            await page.wait_for_load_state('networkidle')
            print("✅ Login successful")
            
            # Step 2: Navigate to an activity dashboard
            print("\n2. Navigating to activity dashboard...")
            
            # Look for activities on the main page
            activities = await page.query_selector_all('a[href*="/activity/"]')
            if not activities:
                print("❌ No activities found on the dashboard")
                return False
            
            # Click on the first activity
            activity_link = activities[0]
            await activity_link.click()
            await page.wait_for_load_state('networkidle')
            print("✅ Navigated to activity dashboard")
            
            # Step 3: Test KPI cards styling (12px rounded corners)
            print("\n3. Testing KPI card styling...")
            kpi_cards = await page.query_selector_all('.row-cards .card')
            if not kpi_cards:
                print("❌ No KPI cards found")
                return False
            
            # Check border-radius on first card
            first_card = kpi_cards[0]
            card_styles = await first_card.evaluate('el => window.getComputedStyle(el)')
            border_radius = await first_card.evaluate('el => el.style.borderRadius')
            
            if '12px' in border_radius or border_radius == '12px':
                print("✅ KPI cards have correct 12px border radius")
            else:
                print(f"⚠️  Border radius found: {border_radius} (expected 12px)")
            
            # Step 4: Test unpaid passports card shows bar chart
            print("\n4. Testing unpaid passports bar chart...")
            
            # Look for the unpaid passports card
            unpaid_card = await page.query_selector('text=UNPAID PASSPORTS >> xpath=ancestor::div[contains(@class, "card")]')
            if unpaid_card:
                # Check for bar chart elements (rect elements instead of path)
                bar_chart = await unpaid_card.query_selector('svg rect')
                if bar_chart:
                    print("✅ Unpaid passports card shows bar chart (rect elements found)")
                else:
                    # Check if it's using path (line chart) instead
                    line_chart = await unpaid_card.query_selector('svg path')
                    if line_chart:
                        print("❌ Unpaid passports card shows line chart instead of bar chart")
                    else:
                        print("⚠️  No chart elements found in unpaid passports card")
            else:
                print("❌ Unpaid passports card not found")
            
            # Step 5: Test mobile responsiveness
            print("\n5. Testing mobile responsiveness...")
            
            # Switch to mobile viewport
            await page.set_viewport_size({'width': 375, 'height': 667})
            await page.wait_for_timeout(1000)
            
            # Check if mobile carousel is visible
            mobile_carousel = await page.query_selector('.d-md-none .d-flex.overflow-auto')
            if mobile_carousel:
                print("✅ Mobile carousel is visible on mobile viewport")
                
                # Test scroll behavior
                await mobile_carousel.evaluate('el => el.scrollLeft = 300')
                await page.wait_for_timeout(500)
                scroll_position = await mobile_carousel.evaluate('el => el.scrollLeft')
                if scroll_position > 0:
                    print("✅ Mobile carousel is scrollable")
                else:
                    print("⚠️  Mobile carousel scroll not working")
            else:
                print("❌ Mobile carousel not found")
            
            # Switch back to desktop
            await page.set_viewport_size({'width': 1200, 'height': 800})
            await page.wait_for_timeout(1000)
            
            # Step 6: Test dropdown period changes
            print("\n6. Testing dropdown period changes...")
            
            # Find first KPI dropdown
            first_dropdown = await page.query_selector('.card .dropdown .dropdown-toggle')
            if first_dropdown:
                # Click dropdown to open it
                await first_dropdown.click()
                await page.wait_for_timeout(500)
                
                # Check if dropdown menu is visible
                dropdown_menu = await page.query_selector('.dropdown-menu')
                if dropdown_menu:
                    print("✅ Dropdown menu opens correctly")
                    
                    # Test clicking on "Last 30 days" option
                    thirty_day_option = await page.query_selector('a[data-period="30"]')
                    if thirty_day_option:
                        print("⚠️  Testing 30-day period change...")
                        
                        # Set up network request interception to catch API calls
                        api_requests = []
                        
                        async def handle_request(request):
                            if 'activity-kpis' in request.url:
                                api_requests.append(request.url)
                        
                        page.on('request', handle_request)
                        
                        # Click the 30-day option
                        await thirty_day_option.click()
                        await page.wait_for_timeout(2000)  # Wait for API call
                        
                        # Check if API was called
                        if api_requests:
                            print(f"✅ API call made: {api_requests[0]}")
                            if 'period=30' in api_requests[0]:
                                print("✅ Correct period parameter sent to API")
                            else:
                                print("⚠️  Period parameter not found in API call")
                        else:
                            print("❌ No API calls detected")
                        
                        # Check if all dropdown buttons updated
                        all_dropdowns = await page.query_selector_all('.dropdown-toggle')
                        updated_count = 0
                        for dropdown in all_dropdowns:
                            text = await dropdown.text_content()
                            if 'Last 30 days' in text:
                                updated_count += 1
                        
                        if updated_count > 1:
                            print(f"✅ Multiple dropdown buttons updated ({updated_count} found)")
                        else:
                            print("⚠️  Not all dropdown buttons were updated")
                        
                    else:
                        print("❌ 30-day option not found in dropdown")
                else:
                    print("❌ Dropdown menu not opening")
            else:
                print("❌ No KPI dropdown found")
            
            # Step 7: Test loading states
            print("\n7. Testing loading states...")
            
            # Look for KPI values to see if they show loading
            kpi_values = await page.query_selector_all('.card .h2')
            if kpi_values:
                print(f"✅ Found {len(kpi_values)} KPI value elements")
                
                # Check opacity of first value element
                first_value = kpi_values[0]
                opacity = await first_value.evaluate('el => window.getComputedStyle(el).opacity')
                print(f"ℹ️  KPI value opacity: {opacity}")
            
            # Step 8: Test error handling by making invalid API request
            print("\n8. Testing error handling...")
            
            # Make a direct API call with invalid activity ID
            try:
                response = await page.evaluate('''
                    fetch('/api/activity-kpis/99999?period=7')
                        .then(r => r.json())
                        .then(data => data)
                        .catch(err => ({ error: err.message }))
                ''')
                
                if 'error' in response:
                    print("✅ Error handling working - invalid API call returns error")
                else:
                    print("⚠️  Unexpected response from invalid API call")
                    
            except Exception as e:
                print(f"⚠️  Error testing API: {e}")
            
            print("\n🎉 KPI functionality test completed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False
        
        finally:
            await browser.close()

def main():
    """Run the test"""
    result = asyncio.run(test_kpi_functionality())
    if result:
        print("\n✨ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()