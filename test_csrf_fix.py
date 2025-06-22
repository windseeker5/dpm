#!/usr/bin/env python3
"""
Quick test to verify the CSRF fix worked
"""

def test_csrf_token_presence():
    """Test that CSRF token is present in survey form"""
    
    # Read the survey form template
    with open('templates/survey_form.html', 'r') as f:
        content = f.read()
    
    # Check for CSRF token
    csrf_checks = [
        'csrf_token' in content,
        'csrf_token()' in content,
        'name="csrf_token"' in content,
        'value="{{ csrf_token() }}"' in content
    ]
    
    all_passed = all(csrf_checks)
    
    print("🔒 CSRF Token Fix Verification")
    print("=" * 40)
    print(f"✅ CSRF token field present: {'Yes' if csrf_checks[0] else 'No'}")
    print(f"✅ CSRF token function called: {'Yes' if csrf_checks[1] else 'No'}")
    print(f"✅ Proper field name: {'Yes' if csrf_checks[2] else 'No'}")
    print(f"✅ Proper value template: {'Yes' if csrf_checks[3] else 'No'}")
    print()
    
    if all_passed:
        print("🎉 CSRF token is properly configured!")
        print()
        print("Next steps:")
        print("1. Refresh the survey form page")
        print("2. Try submitting the survey again")
        print("3. The 'CSRF token missing' error should be resolved")
    else:
        print("❌ CSRF token configuration issues found")
        
    return all_passed

if __name__ == "__main__":
    test_csrf_token_presence()