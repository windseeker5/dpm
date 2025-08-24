#!/usr/bin/env python3
"""
Test script to verify signup form functionality after hiding passport type selection UI
"""

import requests
import time

def test_signup_functionality():
    base_url = "http://127.0.0.1:8890"
    
    # Test 1: Get signup form with passport type in URL
    print("=== Test 1: Form with passport_type_id in URL ===")
    response = requests.get(f"{base_url}/signup/1?passport_type_id=1")
    print(f"Status: {response.status_code}")
    
    # Check if hidden input is present
    hidden_input_present = 'name="passport_type_id" value="1"' in response.text
    print(f"✅ Hidden passport_type_id input present: {hidden_input_present}")
    
    # Check if registration type selection is hidden
    passport_ui_hidden = 'style="display:none"' in response.text and 'Registration Type' in response.text
    print(f"✅ Passport selection UI hidden: {passport_ui_hidden}")
    
    # Test 2: Form structure verification
    print("\n=== Test 2: Form Structure ===")
    form_has_name_field = 'name="name"' in response.text
    form_has_email_field = 'name="email"' in response.text
    form_has_terms_checkbox = 'name="accept_terms"' in response.text
    
    print(f"✅ Name field present: {form_has_name_field}")
    print(f"✅ Email field present: {form_has_email_field}")
    print(f"✅ Terms checkbox present: {form_has_terms_checkbox}")
    
    # Test 3: Multiple passport types scenario
    print("\n=== Test 3: Multiple Passport Types Scenario ===")
    response_multi = requests.get(f"{base_url}/signup/1")  # Without passport_type_id
    multiple_types_hidden = 'style="display:none"' in response_multi.text and 'Registration Type' in response_multi.text
    print(f"✅ Multiple passport types UI hidden: {multiple_types_hidden}")
    
    return {
        'hidden_input_present': hidden_input_present,
        'passport_ui_hidden': passport_ui_hidden,
        'form_structure_valid': form_has_name_field and form_has_email_field and form_has_terms_checkbox,
        'multiple_types_hidden': multiple_types_hidden
    }

if __name__ == "__main__":
    try:
        results = test_signup_functionality()
        
        print("\n" + "="*50)
        print("FINAL TEST RESULTS")
        print("="*50)
        
        all_tests_pass = all(results.values())
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print("="*50)
        if all_tests_pass:
            print("🎉 ALL TESTS PASSED! The signup form is working correctly.")
            print("📝 Summary:")
            print("   - Passport type selection UI is hidden")
            print("   - Hidden input field functionality is preserved")
            print("   - Form structure remains intact")
            print("   - URL parameter functionality works")
        else:
            print("⚠️  Some tests failed. Please review the results above.")
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")