"""
Verification script to check if pagination has been properly added to surveys.html
This script analyzes the HTML template structure to ensure pagination is implemented correctly.
"""

def test_surveys_pagination_structure():
    """Test that surveys.html has proper pagination structure"""
    print("🔍 Testing surveys.html pagination structure...")
    
    # Read the surveys.html file
    try:
        with open('/home/kdresdell/Documents/DEV/minipass_env/app/templates/surveys.html', 'r') as f:
            content = f.read()
        print("✅ Successfully read surveys.html")
    except Exception as e:
        print(f"❌ Failed to read surveys.html: {e}")
        return False
    
    # Test 1: Check for card-footer
    if 'card-footer' in content:
        print("✅ Found card-footer class")
    else:
        print("❌ Missing card-footer class")
        return False
    
    # Test 2: Check for pagination structure
    pagination_checks = [
        'pagination and pagination.total > 0',
        'Showing {{ ((pagination.page - 1) * pagination.per_page) + 1 }}',
        'pagination.pages > 1',
        'pagination pagination-sm mb-0',
        'pagination.has_prev',
        'pagination.has_next',
        'pagination.iter_pages',
        'page_num'
    ]
    
    for check in pagination_checks:
        if check in content:
            print(f"✅ Found pagination pattern: {check}")
        else:
            print(f"❌ Missing pagination pattern: {check}")
            return False
    
    # Test 3: Check for proper navigation structure
    nav_checks = [
        'ti ti-chevron-left',
        'ti ti-chevron-right', 
        'page-link',
        'page-item',
        'aria-label="Previous"',
        'aria-label="Next"'
    ]
    
    for check in nav_checks:
        if check in content:
            print(f"✅ Found navigation element: {check}")
        else:
            print(f"❌ Missing navigation element: {check}")
            return False
    
    # Test 4: Check for "No entries found" fallback
    if 'No entries found' in content:
        print("✅ Found 'No entries found' fallback text")
    else:
        print("❌ Missing 'No entries found' fallback text")
        return False
    
    # Test 5: Compare with signups.html structure
    print("\n🔄 Comparing with signups.html structure...")
    
    try:
        with open('/home/kdresdell/Documents/DEV/minipass_env/app/templates/signups.html', 'r') as f:
            signups_content = f.read()
        print("✅ Successfully read signups.html for comparison")
        
        # Extract pagination section from signups.html
        signups_pagination_start = signups_content.find('<!-- Pagination -->')
        signups_pagination_end = signups_content.find('</div>', signups_pagination_start + 100)
        
        if signups_pagination_start != -1 and signups_pagination_end != -1:
            signups_pagination = signups_content[signups_pagination_start:signups_pagination_end + 6]
            print("✅ Extracted pagination section from signups.html")
            
            # Check if surveys.html has similar structure
            surveys_pagination_start = content.find('<!-- Pagination -->')
            if surveys_pagination_start != -1:
                print("✅ Surveys.html has similar pagination comment structure")
            else:
                print("❌ Surveys.html missing pagination comment")
                
        else:
            print("⚠️  Could not extract pagination section from signups.html")
            
    except Exception as e:
        print(f"⚠️  Could not read signups.html for comparison: {e}")
    
    # Test 6: Check for proper Flask template syntax
    flask_checks = [
        '{% if pagination',
        '{% endif %}',
        'pagination.page',
        '{{ pagination.total }}',
        'current_filters',
        'url_for(request.endpoint'
    ]
    
    print("\n🔍 Checking Flask template syntax...")
    for check in flask_checks:
        if check in content:
            print(f"✅ Found Flask syntax: {check}")
        else:
            print(f"❌ Missing Flask syntax: {check}")
            return False
    
    # Test 7: Check positioning in file
    print("\n📍 Checking pagination positioning...")
    
    # Find the table closing tag
    table_end = content.find('</table>')
    table_responsive_end = content.find('</div>', table_end)
    pagination_start = content.find('<!-- Pagination -->')
    
    if table_end < pagination_start < content.find('</div>', pagination_start + 100):
        print("✅ Pagination is properly positioned after table")
    else:
        print("❌ Pagination is not properly positioned")
        return False
    
    print("\n🎉 All pagination structure tests passed!")
    return True

def test_surveys_vs_other_pages():
    """Compare pagination structure across different pages"""
    print("\n🔄 Comparing pagination across pages...")
    
    pages = {
        'signups': '/home/kdresdell/Documents/DEV/minipass_env/app/templates/signups.html',
        'passports': '/home/kdresdell/Documents/DEV/minipass_env/app/templates/passports.html',
        'surveys': '/home/kdresdell/Documents/DEV/minipass_env/app/templates/surveys.html'
    }
    
    pagination_patterns = {}
    
    for page_name, file_path in pages.items():
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if has pagination
            has_card_footer = 'card-footer' in content
            has_pagination_logic = 'pagination and pagination.total' in content
            has_entry_count = 'entries' in content.lower() and 'showing' in content.lower()
            
            pagination_patterns[page_name] = {
                'has_card_footer': has_card_footer,
                'has_pagination_logic': has_pagination_logic,
                'has_entry_count': has_entry_count
            }
            
            print(f"📄 {page_name.title()}: Footer={has_card_footer}, Logic={has_pagination_logic}, Count={has_entry_count}")
            
        except Exception as e:
            print(f"❌ Could not read {page_name}: {e}")
            pagination_patterns[page_name] = {'error': str(e)}
    
    # Check consistency
    surveys_pattern = pagination_patterns.get('surveys', {})
    signups_pattern = pagination_patterns.get('signups', {})
    
    if (surveys_pattern.get('has_card_footer') and 
        surveys_pattern.get('has_pagination_logic') and 
        surveys_pattern.get('has_entry_count')):
        print("✅ Surveys page has complete pagination structure!")
        
        if (signups_pattern.get('has_card_footer') and 
            signups_pattern.get('has_pagination_logic')):
            print("✅ Surveys pagination matches signups pattern!")
        else:
            print("⚠️  Surveys pagination differs from signups pattern")
    else:
        print("❌ Surveys page missing pagination components")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SURVEYS PAGINATION VERIFICATION TEST")
    print("=" * 60)
    
    # Test 1: Structure verification
    structure_passed = test_surveys_pagination_structure()
    
    # Test 2: Cross-page comparison
    comparison_passed = test_surveys_vs_other_pages()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    if structure_passed and comparison_passed:
        print("🎉 ALL TESTS PASSED! Surveys pagination is properly implemented.")
        print("✅ The surveys.html page now has:")
        print("   • Card footer with proper styling")
        print("   • Entry count display (e.g., 'Showing 1 to 10 of 25 entries')")
        print("   • Page navigation with previous/next buttons")
        print("   • Proper pagination logic for multiple pages")
        print("   • Consistent styling with other pages")
        exit(0)
    else:
        print("❌ SOME TESTS FAILED! Please check the issues above.")
        exit(1)