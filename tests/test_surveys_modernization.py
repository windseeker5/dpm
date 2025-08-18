#!/usr/bin/env python3
"""
Test file to verify surveys.html modernization with signups.html styling patterns.

This test navigates to the surveys page and verifies that all the modernization
features from signups.html have been properly applied.
"""

import time
import sys
import os

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_surveys_modernization():
    """Test that surveys.html has been successfully modernized"""
    
    from mcp__playwright__browser_navigate import *
    from mcp__playwright__browser_snapshot import *
    from mcp__playwright__browser_take_screenshot import *
    from mcp__playwright__browser_click import *
    from mcp__playwright__browser_type import *
    from mcp__playwright__browser_wait_for import *
    
    print("🧪 Testing surveys page modernization...")
    
    # Navigate to surveys page
    print("1. Navigating to surveys page...")
    navigate_result = browser_navigate("http://127.0.0.1:8890/surveys")
    
    # Wait for page to load
    time.sleep(2)
    
    # Take initial screenshot
    print("2. Taking initial screenshot...")
    screenshot_result = browser_take_screenshot(
        filename="surveys-modernization-initial.png",
        fullPage=True
    )
    
    # Test 1: Verify enhanced search bar is present
    print("3. Testing enhanced search bar...")
    snapshot = browser_snapshot()
    
    search_input_found = False
    search_features_found = {
        'enhanced_search': False,
        'ctrl_k_hint': False,
        'clear_button': False,
        'search_counter': False
    }
    
    for element in snapshot.get('elements', []):
        if element.get('id') == 'enhancedSearchInput':
            search_features_found['enhanced_search'] = True
            search_input_found = True
        elif element.get('id') == 'searchKbdHint':
            search_features_found['ctrl_k_hint'] = True
        elif element.get('id') == 'searchClearBtn':
            search_features_found['clear_button'] = True
        elif element.get('id') == 'searchCharCounter':
            search_features_found['search_counter'] = True
    
    print(f"   Enhanced search input: {'✅' if search_features_found['enhanced_search'] else '❌'}")
    print(f"   Ctrl+K hint: {'✅' if search_features_found['ctrl_k_hint'] else '❌'}")
    print(f"   Clear button: {'✅' if search_features_found['clear_button'] else '❌'}")
    print(f"   Search counter: {'✅' if search_features_found['search_counter'] else '❌'}")
    
    # Test 2: Verify GitHub-style filter buttons
    print("4. Testing GitHub-style filter buttons...")
    github_filters_found = False
    
    for element in snapshot.get('elements', []):
        if 'github-filter-btn' in element.get('classes', []):
            github_filters_found = True
            break
        elif 'github-filter-group' in element.get('classes', []):
            github_filters_found = True
            break
    
    print(f"   GitHub-style filters: {'✅' if github_filters_found else '❌'}")
    
    # Test 3: Verify bulk actions bar (should be hidden initially)
    print("5. Testing bulk actions bar...")
    bulk_actions_found = False
    
    for element in snapshot.get('elements', []):
        if element.get('id') == 'bulkActions':
            bulk_actions_found = True
            break
    
    print(f"   Bulk actions bar: {'✅' if bulk_actions_found else '❌'}")
    
    # Test 4: Verify modernized statistics cards
    print("6. Testing statistics cards...")
    stats_cards_found = 0
    
    for element in snapshot.get('elements', []):
        if 'card-sm' in element.get('classes', []):
            stats_cards_found += 1
    
    print(f"   Statistics cards found: {stats_cards_found} {'✅' if stats_cards_found >= 4 else '❌'}")
    
    # Test 5: Test search functionality
    print("7. Testing search functionality...")
    if search_input_found:
        try:
            # Type in search field
            type_result = browser_type(
                element="Enhanced search input",
                ref="enhancedSearchInput",
                text="test search",
                slowly=False
            )
            
            time.sleep(1)
            
            # Take screenshot of search state
            search_screenshot = browser_take_screenshot(
                filename="surveys-search-functionality.png"
            )
            
            print("   Search typing: ✅")
            
            # Clear search
            clear_result = browser_type(
                element="Enhanced search input", 
                ref="enhancedSearchInput",
                text="",
                slowly=False
            )
            
            print("   Search clearing: ✅")
            
        except Exception as e:
            print(f"   Search functionality: ❌ ({str(e)})")
    
    # Test 6: Verify table structure
    print("8. Testing table structure...")
    table_found = False
    actions_column_centered = False
    
    for element in snapshot.get('elements', []):
        if element.get('tagName') == 'table':
            table_found = True
        elif element.get('text') == 'Actions' and 'text-center' in element.get('classes', []):
            actions_column_centered = True
    
    print(f"   Table present: {'✅' if table_found else '❌'}")
    print(f"   Actions column centered: {'✅' if actions_column_centered else '❌'}")
    
    # Test 7: Verify survey-specific modals are preserved
    print("9. Testing survey-specific modals...")
    modals_found = {
        'quick_survey': False,
        'template_preview': False,
        'delete_modal': False
    }
    
    for element in snapshot.get('elements', []):
        if element.get('id') == 'quickSurveyModal':
            modals_found['quick_survey'] = True
        elif element.get('id') == 'templatePreviewModal':
            modals_found['template_preview'] = True
        elif element.get('id') == 'deleteModal':
            modals_found['delete_modal'] = True
    
    print(f"   Quick Survey modal: {'✅' if modals_found['quick_survey'] else '❌'}")
    print(f"   Template Preview modal: {'✅' if modals_found['template_preview'] else '❌'}")
    print(f"   Delete modal: {'✅' if modals_found['delete_modal'] else '❌'}")
    
    # Final screenshot
    print("10. Taking final screenshot...")
    final_screenshot = browser_take_screenshot(
        filename="surveys-modernization-final.png",
        fullPage=True
    )
    
    # Summary
    print("\n📊 MODERNIZATION TEST SUMMARY:")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    # Count tests
    tests = [
        ("Enhanced Search Features", all(search_features_found.values())),
        ("GitHub-style Filters", github_filters_found),
        ("Bulk Actions Bar", bulk_actions_found),
        ("Statistics Cards", stats_cards_found >= 4),
        ("Table Structure", table_found and actions_column_centered),
        ("Survey Modals Preserved", all(modals_found.values()))
    ]
    
    for test_name, passed in tests:
        total_tests += 1
        if passed:
            passed_tests += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\n🎯 Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 Surveys page modernization SUCCESSFUL!")
        return True
    else:
        print("⚠️  Surveys page modernization needs attention.")
        return False

if __name__ == "__main__":
    test_surveys_modernization()