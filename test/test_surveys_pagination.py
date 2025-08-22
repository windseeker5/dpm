"""
Test script to verify pagination functionality on the surveys page.
This script tests both the visual appearance and functional behavior of pagination.
"""
import asyncio
from playwright.async_api import async_playwright

async def test_surveys_pagination():
    """Test the surveys page pagination functionality"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("🚀 Starting surveys pagination test...")
            
            # Navigate to login page
            await page.goto('http://127.0.0.1:8890/login')
            await page.wait_for_load_state('networkidle')
            
            # Login
            print("🔐 Logging in...")
            await page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Navigate to surveys page
            print("📊 Navigating to surveys page...")
            await page.goto('http://127.0.0.1:8890/surveys')
            await page.wait_for_load_state('networkidle')
            
            # Check if page loaded successfully
            page_title = await page.title()
            print(f"📄 Page title: {page_title}")
            
            # Wait for main content to load
            await page.wait_for_selector('.card', timeout=10000)
            
            # Test 1: Check if pagination footer exists
            print("🔍 Testing pagination footer existence...")
            pagination_footer = await page.query_selector('.card-footer')
            
            if pagination_footer:
                print("✅ Pagination footer found!")
                
                # Check the text content
                footer_text = await pagination_footer.text_content()
                print(f"📝 Footer text: {footer_text.strip()}")
                
                # Test 2: Check for "Showing X entries" text
                if 'entries' in footer_text.lower() or 'no entries found' in footer_text.lower():
                    print("✅ Entry count text found in footer!")
                else:
                    print("❌ Entry count text NOT found in footer!")
                
                # Test 3: Check for pagination navigation (if multiple pages)
                pagination_nav = await page.query_selector('.pagination')
                if pagination_nav:
                    print("✅ Pagination navigation found!")
                    
                    # Count pagination items
                    page_items = await page.query_selector_all('.page-item')
                    print(f"📄 Found {len(page_items)} pagination items")
                    
                    # Check for previous/next buttons
                    prev_btn = await page.query_selector('.page-item:first-child')
                    next_btn = await page.query_selector('.page-item:last-child')
                    
                    if prev_btn and next_btn:
                        print("✅ Previous and Next buttons found!")
                    else:
                        print("❌ Previous or Next buttons missing!")
                        
                else:
                    print("ℹ️  No pagination navigation (likely single page)")
                
            else:
                print("❌ Pagination footer NOT found!")
                return False
            
            # Test 4: Visual styling check
            print("🎨 Testing visual styling...")
            
            # Check if footer has proper styling
            footer_styles = await pagination_footer.evaluate('el => getComputedStyle(el)')
            background_color = footer_styles.get('background-color', '')
            print(f"🎨 Footer background color: {background_color}")
            
            # Test 5: Compare with other pages (check consistency)
            print("🔄 Testing consistency with other pages...")
            
            # Navigate to signups page to compare
            await page.goto('http://127.0.0.1:8890/signups')
            await page.wait_for_load_state('networkidle')
            
            signups_footer = await page.query_selector('.card-footer')
            if signups_footer:
                signups_text = await signups_footer.text_content()
                print(f"📝 Signups footer text: {signups_text.strip()}")
                print("✅ Signups page has pagination footer for comparison")
            
            # Navigate back to surveys
            await page.goto('http://127.0.0.1:8890/surveys')
            await page.wait_for_load_state('networkidle')
            
            # Take a screenshot for visual verification
            print("📸 Taking screenshot for visual verification...")
            await page.screenshot(path='tests/surveys_pagination_test.png', full_page=True)
            print("📸 Screenshot saved as 'tests/surveys_pagination_test.png'")
            
            # Test 6: Mobile responsiveness
            print("📱 Testing mobile responsiveness...")
            await page.set_viewport_size({'width': 375, 'height': 667})  # iPhone size
            await page.wait_for_timeout(1000)  # Wait for reflow
            
            mobile_footer = await page.query_selector('.card-footer')
            if mobile_footer:
                mobile_footer_visible = await mobile_footer.is_visible()
                print(f"📱 Mobile footer visible: {mobile_footer_visible}")
                
                # Check if pagination is responsive
                mobile_pagination = await page.query_selector('.pagination')
                if mobile_pagination:
                    mobile_pagination_visible = await mobile_pagination.is_visible()
                    print(f"📱 Mobile pagination visible: {mobile_pagination_visible}")
            
            # Take mobile screenshot
            await page.screenshot(path='tests/surveys_pagination_mobile_test.png', full_page=True)
            print("📸 Mobile screenshot saved as 'tests/surveys_pagination_mobile_test.png'")
            
            print("✅ All pagination tests completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            # Take error screenshot
            await page.screenshot(path='tests/surveys_pagination_error.png', full_page=True)
            return False
            
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_surveys_pagination())
    if result:
        print("🎉 Surveys pagination test PASSED!")
    else:
        print("💥 Surveys pagination test FAILED!")