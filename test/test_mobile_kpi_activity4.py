#!/usr/bin/env python3
"""
Test mobile view KPI cards for activity 4
Check if simplified cards show correct activity-specific data
"""
from playwright.sync_api import sync_playwright
import time

def test_mobile_kpi_activity4():
    """Test KPI cards in mobile view for activity 4"""
    
    with sync_playwright() as p:
        # Launch browser with mobile viewport
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 375, 'height': 812},  # iPhone X size
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
        )
        page = context.new_page()
        
        print("🚀 Testing Mobile View KPI Cards for Activity 4")
        print("=" * 60)
        
        try:
            # Login
            page.goto("http://localhost:5000/login")
            print("✓ Navigated to login page")
            
            page.fill('input[name="email"]', "kdresdell@gmail.com")
            page.fill('input[name="password"]', "admin123")
            page.click('button[type="submit"]')
            print("✓ Logged in successfully")
            
            # Wait for navigation
            page.wait_for_timeout(2000)
            
            # Navigate to activity 4 dashboard
            page.goto("http://localhost:5000/activity-dashboard/4")
            print("✓ Navigated to Activity 4 dashboard")
            print(f"  Viewport: Mobile (375x812)")
            
            # Wait for page to load
            page.wait_for_timeout(3000)
            
            # Capture console messages
            page.on("console", lambda msg: print(f"  Console: {msg.text[:100]}") if "kpi" in msg.text.lower() else None)
            
            # Check what cards are rendered in mobile view
            print("\n📱 MOBILE VIEW ANALYSIS:")
            print("-" * 40)
            
            # Check for simplified cards (mobile view)
            simplified_cards = page.locator('.d-sm-none .card').count()
            desktop_cards = page.locator('.d-none.d-sm-block .card').count()
            
            print(f"  Simplified cards (mobile): {simplified_cards}")
            print(f"  Desktop cards (hidden): {desktop_cards}")
            
            # Get KPI values from mobile cards
            print("\n📊 MOBILE KPI VALUES:")
            
            # Try to find mobile-specific elements
            mobile_revenue = page.locator('.d-sm-none #revenue-value').text_content() if page.locator('.d-sm-none #revenue-value').count() > 0 else "Not found"
            mobile_active = page.locator('.d-sm-none #active-passports-value').text_content() if page.locator('.d-sm-none #active-passports-value').count() > 0 else "Not found"
            mobile_created = page.locator('.d-sm-none #passports-created-value').text_content() if page.locator('.d-sm-none #passports-created-value').count() > 0 else "Not found"
            mobile_pending = page.locator('.d-sm-none #pending-signups-value').text_content() if page.locator('.d-sm-none #pending-signups-value').count() > 0 else "Not found"
            
            # Also check regular IDs in case they're shared
            regular_revenue = page.locator('#revenue-value').text_content() if page.locator('#revenue-value').count() > 0 else "Not found"
            regular_active = page.locator('#active-passports-value').text_content() if page.locator('#active-passports-value').count() > 0 else "Not found"
            regular_created = page.locator('#passports-created-value').text_content() if page.locator('#passports-created-value').count() > 0 else "Not found"
            regular_pending = page.locator('#pending-signups-value').text_content() if page.locator('#pending-signups-value').count() > 0 else "Not found"
            
            print(f"  Mobile Revenue: {mobile_revenue}")
            print(f"  Mobile Active: {mobile_active}")
            print(f"  Mobile Created: {mobile_created}")
            print(f"  Mobile Pending: {mobile_pending}")
            
            print(f"\n  Regular Revenue: {regular_revenue}")
            print(f"  Regular Active: {regular_active}")
            print(f"  Regular Created: {regular_created}")
            print(f"  Regular Pending: {regular_pending}")
            
            # Check JavaScript variables
            print("\n🔍 CHECKING JAVASCRIPT DATA:")
            kpi_data = page.evaluate("() => window.kpiData")
            if kpi_data:
                print("  window.kpiData exists:")
                for key in ['revenue', 'active_users', 'passports_created', 'unpaid_passports']:
                    if key in kpi_data:
                        current = kpi_data[key].get('current', 0)
                        print(f"    {key}: {current}")
            else:
                print("  ❌ window.kpiData is not defined!")
            
            # Check if initialization function exists
            has_init = page.evaluate("() => typeof initializeApexCharts !== 'undefined'")
            print(f"\n  initializeApexCharts function: {'✓ Exists' if has_init else '✗ Missing'}")
            
            # Try to re-initialize
            if has_init:
                print("\n  Attempting to reinitialize charts...")
                page.evaluate("() => initializeApexCharts()")
                page.wait_for_timeout(1000)
                
                # Check values again
                print("\n📊 VALUES AFTER REINITIALIZATION:")
                new_revenue = page.locator('#revenue-value').text_content() if page.locator('#revenue-value').count() > 0 else "Not found"
                new_active = page.locator('#active-passports-value').text_content() if page.locator('#active-passports-value').count() > 0 else "Not found"
                print(f"  Revenue: {new_revenue}")
                print(f"  Active: {new_active}")
            
            # Take screenshot for debugging
            page.screenshot(path="mobile_activity4_kpi.png")
            print("\n📸 Screenshot saved: mobile_activity4_kpi.png")
            
            # Switch to desktop view to compare
            print("\n🖥️ SWITCHING TO DESKTOP VIEW:")
            page.set_viewport_size({"width": 1200, "height": 800})
            page.wait_for_timeout(2000)
            
            desktop_revenue = page.locator('#revenue-value').text_content()
            desktop_active = page.locator('#active-passports-value').text_content()
            print(f"  Desktop Revenue: {desktop_revenue}")
            print(f"  Desktop Active: {desktop_active}")
            
            print("\n" + "=" * 60)
            print("ANALYSIS COMPLETE")
            
            # Keep browser open for manual inspection
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            browser.close()
            print("🏁 Test completed")

if __name__ == "__main__":
    test_mobile_kpi_activity4()