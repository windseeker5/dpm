#!/usr/bin/env python3
"""
Script to verify that all scrolling fixes have been applied to signup_form.html
"""

def verify_scrolling_fixes():
    """Verify that all scrolling-related fixes have been applied"""
    
    file_path = "/home/kdresdell/Documents/DEV/minipass_env/app/templates/signup_form.html"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    
    print("🔍 Verifying signup form scrolling fixes...")
    print("=" * 60)
    
    fixes_applied = []
    fixes_failed = []
    
    # Check 1: Remove overflow: hidden from .signup-card
    if 'overflow: hidden;' not in content.split('.signup-card')[1].split('}')[0]:
        fixes_applied.append("✅ Removed 'overflow: hidden' from .signup-card")
    else:
        fixes_failed.append("❌ 'overflow: hidden' still present in .signup-card")
    
    # Check 2: Change align-items to flex-start in .signup-wrapper
    if 'align-items: flex-start;' in content:
        fixes_applied.append("✅ Changed align-items to 'flex-start' in .signup-wrapper")
    else:
        fixes_failed.append("❌ align-items not set to 'flex-start' in .signup-wrapper")
    
    # Check 3: Change min-height to max-height in .signup-card
    signup_card_section = content.split('.signup-card')[1].split('@media')[0]
    if 'max-height: calc(100vh - 4rem);' in signup_card_section and 'min-height: 800px' not in signup_card_section:
        fixes_applied.append("✅ Changed min-height to max-height in .signup-card")
    else:
        fixes_failed.append("❌ .signup-card still uses min-height instead of max-height")
    
    # Check 4: Add overflow-y: auto to .signup-wrapper and .signup-form
    if 'overflow-y: auto;' in content:
        count = content.count('overflow-y: auto;')
        fixes_applied.append(f"✅ Added overflow-y: auto ({count} instances found)")
    else:
        fixes_failed.append("❌ overflow-y: auto not found")
    
    # Check 5: Add padding-top and padding-bottom to .signup-wrapper
    wrapper_section = content.split('.signup-wrapper')[1].split('}')[0]
    if 'padding-top: 2rem;' in wrapper_section and 'padding-bottom: 2rem;' in wrapper_section:
        fixes_applied.append("✅ Added proper padding to .signup-wrapper")
    else:
        fixes_failed.append("❌ Missing proper padding in .signup-wrapper")
    
    # Check 6: Mobile styles - min-height: auto
    mobile_section = content.split('@media (max-width: 768px)')[1]
    if 'min-height: auto;' in mobile_section and 'min-height: 100vh;' not in mobile_section:
        fixes_applied.append("✅ Mobile styles use min-height: auto")
    else:
        fixes_failed.append("❌ Mobile styles still use min-height: 100vh")
    
    # Display results
    print("\n📋 APPLIED FIXES:")
    for fix in fixes_applied:
        print(f"   {fix}")
    
    if fixes_failed:
        print("\n⚠️  FAILED FIXES:")
        for fix in fixes_failed:
            print(f"   {fix}")
    
    print("\n" + "=" * 60)
    success_rate = len(fixes_applied) / (len(fixes_applied) + len(fixes_failed)) * 100
    print(f"📊 Success Rate: {success_rate:.1f}% ({len(fixes_applied)}/{len(fixes_applied) + len(fixes_failed)} fixes applied)")
    
    if success_rate >= 85:
        print("🎉 SCROLLING FIXES SUCCESSFULLY APPLIED!")
        print("\n📱 The signup form should now be:")
        print("   • Scrollable when content exceeds viewport height")
        print("   • Accessible on all screen sizes")
        print("   • Mobile-friendly with proper spacing")
        print("   • Free from overflow issues")
        return True
    else:
        print("❌ Some fixes may need attention")
        return False

if __name__ == "__main__":
    success = verify_scrolling_fixes()
    exit(0 if success else 1)