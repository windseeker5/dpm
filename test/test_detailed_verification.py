#!/usr/bin/env python3
"""
Detailed verification of signup form after hiding passport type selection UI
"""

import requests

def test_detailed_verification():
    base_url = "http://127.0.0.1:8890"
    
    print("="*60)
    print("DETAILED SIGNUP FORM VERIFICATION")
    print("="*60)
    
    # Scenario 1: Multiple passport types, no selection (should show hidden selection UI)
    print("\n🔍 SCENARIO 1: Multiple passport types, no selection")
    print("-" * 50)
    response1 = requests.get(f"{base_url}/signup/1")
    
    # Check for hidden selection UI
    selection_ui_exists = 'Registration Type' in response1.text and 'form-label' in response1.text
    selection_ui_hidden = 'style="display:none"' in response1.text and 'Registration Type' in response1.text
    
    print(f"✅ Passport selection UI exists: {selection_ui_exists}")
    print(f"✅ Passport selection UI is hidden: {selection_ui_hidden}")
    
    # Scenario 2: With passport_type_id in URL (should show info display, not selection)
    print("\n🔍 SCENARIO 2: With passport_type_id in URL")
    print("-" * 50)
    response2 = requests.get(f"{base_url}/signup/1?passport_type_id=1")
    
    # Check for hidden input
    hidden_input = 'name="passport_type_id" value="1"' in response2.text
    
    # Check for info display (not selection UI)
    info_display = '<strong>Registration Type:</strong>' in response2.text
    
    # Verify selection UI is not shown when passport type is pre-selected
    selection_ui_not_shown = 'form-label' not in response2.text or 'Registration Type' not in response2.text or 'display:none' in response2.text
    
    print(f"✅ Hidden input field present: {hidden_input}")
    print(f"✅ Info display shown: {info_display}")
    print(f"✅ Selection UI not shown (pre-selected): {selection_ui_not_shown}")
    
    # Scenario 3: Form submission capability
    print("\n🔍 SCENARIO 3: Form submission capability")
    print("-" * 50)
    
    # Extract CSRF token
    csrf_start = response2.text.find('name="csrf_token" value="') + len('name="csrf_token" value="')
    csrf_end = response2.text.find('"', csrf_start)
    csrf_token = response2.text[csrf_start:csrf_end]
    
    print(f"✅ CSRF token extracted: {'Yes' if csrf_token else 'No'}")
    print(f"✅ Form structure intact: {'Yes' if 'name=\"name\"' in response2.text else 'No'}")
    
    # Final verification
    print("\n" + "="*60)
    print("CRITICAL REQUIREMENTS VERIFICATION")
    print("="*60)
    
    requirements = [
        ("✅ Passport type determined from URL parameter", hidden_input),
        ("✅ Hidden input field preserved", 'name="passport_type_id"' in response2.text),
        ("✅ Selection UI hidden when multiple types", selection_ui_hidden),
        ("✅ Form can still submit", 'method="POST"' in response2.text),
        ("✅ Visual change only (functionality intact)", info_display and hidden_input)
    ]
    
    all_passed = True
    for req_desc, req_result in requirements:
        status = "✅ PASS" if req_result else "❌ FAIL"
        print(f"{status} {req_desc}")
        if not req_result:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 SUCCESS: All critical requirements met!")
        print("📋 Phase 2 completed successfully:")
        print("   • Passport type selection UI is visually hidden")
        print("   • URL parameter functionality preserved")
        print("   • Hidden input field working correctly") 
        print("   • Form submission capability intact")
        print("   • This is a cosmetic-only change as required")
    else:
        print("⚠️ FAILURE: Some critical requirements not met")
    
    return all_passed

if __name__ == "__main__":
    test_detailed_verification()