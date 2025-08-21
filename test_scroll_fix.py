#!/usr/bin/env python3
"""
Test script to verify scroll position preservation when clicking filter buttons
Tests the fix for the issue where users are "resurrected at the top" of the page
"""

import time
import sys
import json

# Test configuration
BASE_URL = "http://127.0.0.1:8890"
LOGIN_EMAIL = "kdresdell@gmail.com"
LOGIN_PASSWORD = "admin123"
ACTIVITY_ID = 1

def test_scroll_preservation():
    """Test that scroll position is preserved when clicking filter buttons"""
    
    print("=" * 60)
    print("SCROLL POSITION PRESERVATION TEST")
    print("=" * 60)
    
    # Navigate to login page
    print("\n1. Navigating to login page...")
    mcp__playwright__browser_navigate(url=f"{BASE_URL}/login")
    time.sleep(2)
    
    # Login
    print("2. Logging in...")
    mcp__playwright__browser_type(
        element="Email input field",
        ref="input[name='email']",
        text=LOGIN_EMAIL
    )
    mcp__playwright__browser_type(
        element="Password input field", 
        ref="input[name='password']",
        text=LOGIN_PASSWORD,
        submit=True
    )
    time.sleep(3)
    
    # Navigate to activity dashboard
    print(f"3. Navigating to activity dashboard {ACTIVITY_ID}...")
    mcp__playwright__browser_navigate(url=f"{BASE_URL}/activity-dashboard/{ACTIVITY_ID}")
    time.sleep(3)
    
    # Get initial scroll position
    print("4. Checking initial scroll position...")
    initial_scroll = mcp__playwright__browser_evaluate(
        function="() => window.scrollY || document.documentElement.scrollTop || 0"
    )
    print(f"   Initial scroll position: {initial_scroll}px")
    
    # Scroll down to filter buttons (approximately 800-1000px down)
    print("5. Scrolling down to filter buttons...")
    target_scroll = 900
    mcp__playwright__browser_evaluate(
        function=f"() => window.scrollTo(0, {target_scroll})"
    )
    time.sleep(1)
    
    # Verify we scrolled
    before_click_scroll = mcp__playwright__browser_evaluate(
        function="() => window.scrollY || document.documentElement.scrollTop || 0"
    )
    print(f"   Scrolled to position: {before_click_scroll}px")
    
    # Take screenshot before clicking
    print("6. Taking screenshot before clicking filter...")
    mcp__playwright__browser_take_screenshot(
        filename="before_filter_click.png",
        fullPage=False
    )
    
    # Click the "Unpaid" filter button
    print("7. Clicking 'Unpaid' filter button...")
    try:
        # First try to find the unpaid filter button
        button_exists = mcp__playwright__browser_evaluate(
            function="""() => {
                const btn = document.querySelector('#filter-unpaid');
                if (btn) {
                    console.log('Found unpaid button:', btn.href);
                    return true;
                }
                return false;
            }"""
        )
        
        if button_exists:
            mcp__playwright__browser_click(
                element="Unpaid filter button",
                ref="#filter-unpaid"
            )
        else:
            # Fallback: try to find button by link text
            mcp__playwright__browser_click(
                element="Unpaid filter button",
                ref="a:has-text('Unpaid')"
            )
    except Exception as e:
        print(f"   Error clicking filter: {e}")
        print("   Trying alternative selector...")
        mcp__playwright__browser_click(
            element="Unpaid filter link",
            ref="[href*='passport_filter=unpaid']"
        )
    
    print("   Waiting for page to reload...")
    time.sleep(4)
    
    # Get scroll position after page reload
    print("8. Checking scroll position after filter click...")
    after_click_scroll = mcp__playwright__browser_evaluate(
        function="() => window.scrollY || document.documentElement.scrollTop || 0"
    )
    print(f"   Scroll position after reload: {after_click_scroll}px")
    
    # Check if there's stored scroll data in sessionStorage
    stored_data = mcp__playwright__browser_evaluate(
        function="""() => {
            const filterData = sessionStorage.getItem('filterScrollData');
            const filterPos = sessionStorage.getItem('filterScrollPosition');
            return {
                data: filterData ? JSON.parse(filterData) : null,
                position: filterPos
            };
        }"""
    )
    
    if stored_data and stored_data.get('data'):
        print(f"   Stored scroll data found: {stored_data['data'].get('position')}px")
    
    # Take screenshot after clicking
    print("9. Taking screenshot after filter click...")
    mcp__playwright__browser_take_screenshot(
        filename="after_filter_click.png",
        fullPage=False
    )
    
    # Analyze results
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    scroll_difference = abs(after_click_scroll - before_click_scroll)
    
    if after_click_scroll < 100:
        print("❌ FAILED: User was 'resurrected at the top' of the page!")
        print(f"   Before click: {before_click_scroll}px")
        print(f"   After click: {after_click_scroll}px")
        print("   The scroll position was NOT preserved.")
        success = False
    elif scroll_difference < 200:
        print("✅ SUCCESS: Scroll position was preserved!")
        print(f"   Before click: {before_click_scroll}px")
        print(f"   After click: {after_click_scroll}px")
        print(f"   Difference: {scroll_difference}px (acceptable)")
        success = True
    else:
        print("⚠️  PARTIAL: Scroll position changed significantly")
        print(f"   Before click: {before_click_scroll}px")
        print(f"   After click: {after_click_scroll}px")
        print(f"   Difference: {scroll_difference}px")
        success = False
    
    # Check console for any errors
    print("\n10. Checking console for errors...")
    console_messages = mcp__playwright__browser_console_messages()
    errors = [msg for msg in console_messages if 'error' in msg.get('type', '').lower()]
    if errors:
        print(f"   Found {len(errors)} console errors")
        for error in errors[:3]:  # Show first 3 errors
            print(f"   - {error.get('text', '')[:100]}")
    else:
        print("   No console errors found")
    
    print("\n" + "=" * 60)
    
    return success

if __name__ == "__main__":
    try:
        # Initialize browser
        print("Initializing browser...")
        mcp__playwright__browser_navigate(url="about:blank")
        
        # Run the test
        success = test_scroll_preservation()
        
        # Close browser
        print("\nClosing browser...")
        mcp__playwright__browser_close()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        try:
            mcp__playwright__browser_close()
        except:
            pass
        sys.exit(1)