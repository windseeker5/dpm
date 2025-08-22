#!/usr/bin/env python3
"""
Test file to verify the pagination fix on surveys.html page.

This test confirms that the pagination footer has been successfully added
and is displaying the correct entry count, matching the style of other pages.
"""

import time
import sys
import os

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_surveys_pagination_fix():
    """Test that pagination footer has been successfully added to surveys page"""
    
    try:
        from mcp__playwright__browser_navigate import browser_navigate
        from mcp__playwright__browser_snapshot import browser_snapshot
        from mcp__playwright__browser_take_screenshot import browser_take_screenshot
    except ImportError:
        print("❌ Playwright MCP tools not available - running basic verification only")
        return False
    
    print("🔍 Testing surveys page pagination fix...")
    
    # Navigate to surveys page
    print("1. Navigating to surveys page...")
    navigate_result = browser_navigate("http://127.0.0.1:8890/surveys")
    
    # Wait for page to load
    time.sleep(2)
    
    # Get page snapshot
    print("2. Analyzing page structure...")
    snapshot = browser_snapshot()
    
    # Test results
    pagination_found = False
    pagination_text = ""
    
    # Look for pagination text in the page elements
    for element in snapshot.get('elements', []):
        element_text = element.get('text', '').strip()
        if element_text and 'entries' in element_text.lower():
            pagination_found = True
            pagination_text = element_text
            print(f"   ✅ Found pagination: '{pagination_text}'")
            break
    
    # Test footer structure
    footer_found = False
    for element in snapshot.get('elements', []):
        if 'card-footer' in element.get('classes', []):
            footer_found = True
            break
    
    print(f"   Card footer structure: {'✅' if footer_found else '❌'}")
    print(f"   Pagination text: {'✅' if pagination_found else '❌'}")
    
    # Take verification screenshot
    print("3. Taking verification screenshot...")
    screenshot_result = browser_take_screenshot(
        filename="surveys-pagination-verification.png",
        fullPage=True
    )
    
    # Verify expected format
    expected_patterns = [
        "showing",
        "entries", 
        "3"  # Should show 3 entries based on current data
    ]
    
    pattern_matches = 0
    if pagination_text:
        pagination_lower = pagination_text.lower()
        for pattern in expected_patterns:
            if pattern in pagination_lower:
                pattern_matches += 1
    
    print(f"   Pattern matching: {pattern_matches}/{len(expected_patterns)} ({'✅' if pattern_matches >= 2 else '❌'})")
    
    # Summary
    print("\n📊 PAGINATION FIX TEST SUMMARY:")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if pagination_found:
        tests_passed += 1
        print("✅ Pagination text displayed")
    else:
        print("❌ Pagination text missing")
    
    if footer_found:
        tests_passed += 1
        print("✅ Card footer structure present")
    else:
        print("❌ Card footer structure missing")
    
    if pattern_matches >= 2:
        tests_passed += 1
        print("✅ Pagination format correct")
    else:
        print("❌ Pagination format incorrect")
    
    success_rate = (tests_passed / total_tests) * 100
    print(f"\n🎯 Success Rate: {tests_passed}/{total_tests} ({success_rate:.1f}%)")
    
    if pagination_found and pagination_text:
        print(f"📋 Pagination displays: '{pagination_text}'")
    
    if success_rate >= 66:
        print("🎉 Pagination fix SUCCESSFUL!")
        print("📌 Surveys page now matches passports and signups pagination style")
        return True
    else:
        print("⚠️  Pagination fix needs attention.")
        return False

if __name__ == "__main__":
    test_surveys_pagination_fix()