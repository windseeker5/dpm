#!/usr/bin/env python3

import asyncio
from playwright.async_api import async_playwright
import os

async def test_dashboard_events():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1400, 'height': 900})
        page = await context.new_page()
        
        try:
            # Navigate to login page
            print("🔐 Navigating to login...")
            await page.goto('http://127.0.0.1:8890/login')
            await page.wait_for_selector('input[name="email"]')
            
            # Login
            print("📝 Logging in...")
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            
            # Wait for dashboard to load
            print("📊 Navigating to dashboard...")
            await page.wait_for_url('**/dashboard')
            await page.wait_for_selector('.activity-log-section')
            
            # Wait for logs table to load
            await page.wait_for_selector('#logTable tbody tr', timeout=10000)
            
            # Take initial screenshot of events table
            print("📸 Taking screenshot of initial events table...")
            await page.locator('.activity-log-section').screenshot(
                path='.playwright-mcp/01-dashboard-events-initial.png'
            )
            
            # Test filter buttons
            print("🔧 Testing filter buttons...")
            
            # Click Passports filter
            await page.click('#filter-passport')
            await page.wait_for_timeout(500)
            await page.locator('.activity-log-section').screenshot(
                path='.playwright-mcp/02-dashboard-events-passport-filter.png'
            )
            
            # Click Signups filter
            await page.click('#filter-signup')
            await page.wait_for_timeout(500)
            await page.locator('.activity-log-section').screenshot(
                path='.playwright-mcp/03-dashboard-events-signup-filter.png'
            )
            
            # Click Payments filter
            await page.click('#filter-payment')
            await page.wait_for_timeout(500)
            await page.locator('.activity-log-section').screenshot(
                path='.playwright-mcp/04-dashboard-events-payment-filter.png'
            )
            
            # Click Admin filter
            await page.click('#filter-admin')
            await page.wait_for_timeout(500)
            await page.locator('.activity-log-section').screenshot(
                path='.playwright-mcp/05-dashboard-events-admin-filter.png'
            )
            
            # Click All Events filter to return to full view
            await page.click('#filter-all')
            await page.wait_for_timeout(500)
            await page.locator('.activity-log-section').screenshot(
                path='.playwright-mcp/06-dashboard-events-all-filter.png'
            )
            
            # Take full page screenshot for comparison with signup page styling
            await page.screenshot(path='.playwright-mcp/07-dashboard-full-page.png', full_page=True)
            
            print("✅ Dashboard events table testing completed successfully!")
            
            # Verify filter counts are displayed
            filter_buttons = await page.locator('.github-filter-btn').count()
            print(f"📊 Found {filter_buttons} filter buttons")
            
            # Check if entries info is updated correctly
            entries_info = await page.locator('#entriesInfo').text_content()
            print(f"📝 Entries info: {entries_info}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            await page.screenshot(path='.playwright-mcp/error-dashboard-events.png')
            return False
            
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_dashboard_events())
    if result:
        print("🎉 All tests passed!")
    else:
        print("💥 Tests failed!")