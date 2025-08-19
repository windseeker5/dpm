#!/usr/bin/env python3
"""
Verify that the fixes have been applied correctly to the activity dashboard template
"""

def verify_fixes():
    print("Verifying fixes applied to activity_dashboard.html...")
    
    # Read the template file
    with open('templates/activity_dashboard.html', 'r') as f:
        content = f.read()
    
    # Check for the fixes
    fixes_verified = []
    
    # 1. Check that duplicate CSS has been removed
    github_filter_btn_count = content.count('.github-filter-btn {')
    if github_filter_btn_count == 1:
        fixes_verified.append("✓ Duplicate CSS definitions removed")
    else:
        fixes_verified.append(f"✗ Still has {github_filter_btn_count} CSS definitions for .github-filter-btn")
    
    # 2. Check that cursor: pointer is added
    if 'cursor: pointer' in content:
        fixes_verified.append("✓ Cursor pointer style added")
    else:
        fixes_verified.append("✗ Cursor pointer style missing")
    
    # 3. Check that background is properly set
    if 'background: #e1e4e8' in content:
        fixes_verified.append("✓ Button background style fixed")
    else:
        fixes_verified.append("✗ Button background style not found")
    
    # 4. Check that overly aggressive event prevention is fixed
    aggressive_prevention_count = content.count('stopImmediatePropagation')
    if aggressive_prevention_count <= 1:  # Should only be in one place now
        fixes_verified.append("✓ Overly aggressive event prevention fixed")
    else:
        fixes_verified.append(f"✗ Still has {aggressive_prevention_count} instances of stopImmediatePropagation")
    
    # 5. Check that hash link prevention excludes filter buttons
    if ':not(.github-filter-btn)' in content:
        fixes_verified.append("✓ Hash link prevention excludes filter buttons")
    else:
        fixes_verified.append("✗ Hash link prevention still affects all elements")
    
    # 6. Check that filter functions are present
    if 'function filterPassports(' in content and 'function filterSignups(' in content:
        fixes_verified.append("✓ Filter functions are present")
    else:
        fixes_verified.append("✗ Filter functions missing")
    
    # 7. Check that onclick handlers are present in buttons
    passport_onclick_count = content.count('onclick="filterPassports(')
    signup_onclick_count = content.count('onclick="filterSignups(')
    
    if passport_onclick_count > 0 and signup_onclick_count > 0:
        fixes_verified.append(f"✓ Filter button onclick handlers present ({passport_onclick_count} passport, {signup_onclick_count} signup)")
    else:
        fixes_verified.append("✗ Filter button onclick handlers missing")
    
    print("\nFix Verification Results:")
    print("=" * 50)
    for fix in fixes_verified:
        print(fix)
    
    # Count successful fixes
    successful_fixes = len([fix for fix in fixes_verified if fix.startswith("✓")])
    total_checks = len(fixes_verified)
    
    print(f"\nSummary: {successful_fixes}/{total_checks} fixes verified")
    
    if successful_fixes == total_checks:
        print("\n🎉 All fixes have been successfully applied!")
        print("\nThe filter buttons should now work properly:")
        print("- Buttons have proper styling and appear clickable")
        print("- CSS conflicts have been resolved")
        print("- JavaScript event interference has been fixed")
        print("- Ctrl+K shortcut should work without breaking other functionality")
    else:
        print(f"\n⚠️  {total_checks - successful_fixes} issues still need attention")
    
    return successful_fixes == total_checks

if __name__ == '__main__':
    verify_fixes()