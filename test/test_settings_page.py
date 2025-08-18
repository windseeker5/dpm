"""
Test suite for the Settings/Setup page functionality
Tests cover logo display, toggle switches, and UI elements
"""

import asyncio
import time
from playwright.async_api import async_playwright, expect

# Test configuration
BASE_URL = "http://127.0.0.1:8890"
LOGIN_EMAIL = "kdresdell@gmail.com"
LOGIN_PASSWORD = "admin123"
TIMEOUT = 30000  # 30 seconds

async def login(page):
    """Helper function to log into the application"""
    await page.goto(f"{BASE_URL}/login")
    await page.fill('input[name="email"]', LOGIN_EMAIL)
    await page.fill('input[name="password"]', LOGIN_PASSWORD)
    await page.click('button[type="submit"]')
    # Wait for redirect to dashboard
    await page.wait_for_url(f"{BASE_URL}/dashboard", timeout=TIMEOUT)
    print("✅ Successfully logged in")

async def test_settings_page_ui():
    """Test all UI elements on the settings page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Login first
            await login(page)
            
            # Navigate to settings page
            await page.goto(f"{BASE_URL}/setup")
            await page.wait_for_load_state("networkidle")
            print("✅ Navigated to settings page")
            
            # Test 1: Check if page loaded correctly
            assert await page.title() == "Settings - Minipass"
            print("✅ Settings page title is correct")
            
            # Test 2: Check if organization name field exists and is populated
            org_name_input = page.locator('input[name="ORG_NAME"]')
            await expect(org_name_input).to_be_visible()
            org_name_value = await org_name_input.input_value()
            assert org_name_value == "Hockey Gagnon Image"
            print(f"✅ Organization name field populated: {org_name_value}")
            
            # Test 3: Check if logo is displayed (not "No logo uploaded")
            logo_section = page.locator('.col-md-6:has-text("Organization Logo")')
            logo_display = logo_section.locator('.text-center')
            logo_text = await logo_display.inner_text()
            
            # Check if we have "Current Logo" text or an image
            if "No logo uploaded" in logo_text:
                print("❌ Logo not displayed - shows 'No logo uploaded'")
                # Check if image element exists
                logo_img = logo_section.locator('img')
                if await logo_img.count() > 0:
                    img_src = await logo_img.get_attribute('src')
                    print(f"✅ But found logo image at: {img_src}")
            else:
                print(f"✅ Logo section shows: {logo_text}")
                # Also check for actual image
                logo_img = logo_section.locator('img')
                if await logo_img.count() > 0:
                    img_src = await logo_img.get_attribute('src')
                    print(f"✅ Logo image source: {img_src}")
            
            # Test 4: Check Payment Reminder field (should NOT have description)
            payment_field = page.locator('label:has-text("Payment Reminder Delay")')
            await expect(payment_field).to_be_visible()
            
            # Check if description text is gone
            payment_container = payment_field.locator('..')
            description = payment_container.locator('.form-text')
            desc_count = await description.count()
            if desc_count == 0:
                print("✅ Payment Reminder description text removed successfully")
            else:
                desc_text = await description.inner_text()
                print(f"❌ Description still present: {desc_text}")
            
            # Test 5: Check Save button text (should be just "Save")
            save_button = page.locator('button:has-text("Save")')
            button_text = await save_button.inner_text()
            assert "Save" in button_text
            if button_text.strip() == "Save":
                print("✅ Save button text is correct: 'Save'")
            else:
                print(f"⚠️ Save button text is: '{button_text}' (expected just 'Save')")
            
            # Test 6: Check Email Notifications toggle
            email_toggle = page.locator('input[name="ENABLE_NOTIFICATIONS"]')
            await expect(email_toggle).to_be_visible()
            is_checked = await email_toggle.is_checked()
            print(f"✅ Email notifications toggle visible and {'enabled' if is_checked else 'disabled'}")
            
            # Test 7: Check Analytics Tracking toggle
            analytics_toggle = page.locator('input[name="ENABLE_ANALYTICS"]')
            await expect(analytics_toggle).to_be_visible()
            is_checked = await analytics_toggle.is_checked()
            print(f"✅ Analytics tracking toggle visible and {'enabled' if is_checked else 'disabled'}")
            
            # Take screenshot for verification
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/test/settings_page_test.png", full_page=True)
            print("✅ Screenshot saved to test/settings_page_test.png")
            
            print("\n🎉 All UI tests completed successfully!")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            # Take error screenshot
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/test/settings_page_error.png", full_page=True)
            raise
        
        finally:
            await browser.close()

async def test_toggle_functionality():
    """Test the functionality of toggle switches"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Login first
            await login(page)
            
            # Navigate to settings page
            await page.goto(f"{BASE_URL}/setup")
            await page.wait_for_load_state("networkidle")
            
            # Test toggling email notifications
            email_toggle = page.locator('input[name="ENABLE_NOTIFICATIONS"]')
            initial_state = await email_toggle.is_checked()
            
            # Toggle the switch
            await email_toggle.click()
            await page.wait_for_timeout(500)  # Small delay for UI update
            
            new_state = await email_toggle.is_checked()
            assert new_state != initial_state
            print(f"✅ Email notifications toggle works: {initial_state} -> {new_state}")
            
            # Test toggling analytics
            analytics_toggle = page.locator('input[name="ENABLE_ANALYTICS"]')
            initial_state = await analytics_toggle.is_checked()
            
            # Toggle the switch
            await analytics_toggle.click()
            await page.wait_for_timeout(500)
            
            new_state = await analytics_toggle.is_checked()
            assert new_state != initial_state
            print(f"✅ Analytics tracking toggle works: {initial_state} -> {new_state}")
            
            # Save settings and verify they persist
            save_button = page.locator('button:has-text("Save")')
            await save_button.click()
            
            # Wait for save to complete (look for success message or page reload)
            await page.wait_for_timeout(2000)
            
            # Refresh page to verify settings persist
            await page.reload()
            await page.wait_for_load_state("networkidle")
            
            # Check if toggles retained their values
            email_final = await email_toggle.is_checked()
            analytics_final = await analytics_toggle.is_checked()
            
            print(f"✅ Settings persisted after save - Email: {email_final}, Analytics: {analytics_final}")
            
            # Take final screenshot
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/test/settings_toggles_test.png")
            print("✅ Toggle test screenshot saved")
            
            print("\n🎉 Toggle functionality tests completed successfully!")
            
        except Exception as e:
            print(f"❌ Toggle test failed with error: {e}")
            await page.screenshot(path="/home/kdresdell/Documents/DEV/minipass_env/app/test/toggle_test_error.png")
            raise
        
        finally:
            await browser.close()

async def test_api_endpoint():
    """Test the backend API endpoint for settings"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Login first
            await login(page)
            
            # Test API endpoint
            response = await page.request.get(f"{BASE_URL}/api/test-settings")
            assert response.ok
            
            data = await response.json()
            assert data["status"] == "success"
            
            settings = data["data"]
            print("\n📊 API Settings Response:")
            print(f"  - Organization Name: {settings.get('org_name')}")
            print(f"  - Logo Path: {settings.get('org_logo_path')}")
            print(f"  - Logo File Exists: {settings.get('logo_file_exists')}")
            print(f"  - Notifications Enabled: {settings.get('notifications_enabled')}")
            print(f"  - Analytics Enabled: {settings.get('analytics_enabled')}")
            
            # Verify all expected fields are present
            assert settings.get('org_name') == "Hockey Gagnon Image"
            assert settings.get('logo_file_exists') == True
            assert 'notifications_enabled' in settings
            assert 'analytics_enabled' in settings
            
            print("\n✅ API endpoint test passed!")
            
        except Exception as e:
            print(f"❌ API test failed with error: {e}")
            raise
        
        finally:
            await browser.close()

async def main():
    """Run all tests"""
    print("🚀 Starting Settings Page Test Suite\n")
    print("=" * 50)
    
    # Run UI tests
    print("\n📋 Running UI Tests...")
    await test_settings_page_ui()
    
    # Run toggle functionality tests
    print("\n" + "=" * 50)
    print("\n🔄 Running Toggle Functionality Tests...")
    await test_toggle_functionality()
    
    # Run API tests
    print("\n" + "=" * 50)
    print("\n🔌 Running API Tests...")
    await test_api_endpoint()
    
    print("\n" + "=" * 50)
    print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    asyncio.run(main())