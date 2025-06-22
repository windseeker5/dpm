#!/usr/bin/env python3
"""
Test to verify the template datetime issue is fixed
"""

def test_template_fix():
    """Test that the problematic datetime code is removed"""
    
    # Read the activity dashboard template
    with open('templates/activity_dashboard.html', 'r') as f:
        content = f.read()
    
    # Check for problematic patterns
    problematic_patterns = [
        'datetime.now(timezone.utc)',
        'datetime.now(timezone',
        'timezone.utc'
    ]
    
    issues_found = []
    for pattern in problematic_patterns:
        if pattern in content:
            issues_found.append(pattern)
    
    print("🔧 Template DateTime Fix Verification")
    print("=" * 45)
    
    if not issues_found:
        print("✅ No problematic datetime patterns found")
        print("✅ Template should load without errors")
        print()
        print("The activity dashboard should now work properly!")
    else:
        print("❌ Found problematic patterns:")
        for issue in issues_found:
            print(f"  - {issue}")
        print()
        print("These patterns need to be fixed.")
    
    # Check for the fixed pattern
    if 'strftime(\'%m/%d\')' in content:
        print("✅ Fixed date formatting pattern found")
    
    return len(issues_found) == 0

if __name__ == "__main__":
    test_template_fix()