#!/usr/bin/env python3
"""
Visual test for signup form desktop improvements
Tests that visual enhancements don't break form functionality
"""
import requests
import time

def test_signup_form_visual_improvements():
    """Test that signup form loads and has visual improvements applied"""
    base_url = "http://127.0.0.1:8890"
    
    print("Testing signup form visual improvements...")
    
    # Test 1: Form loads correctly
    response = requests.get(f"{base_url}/signup/1")
    print(f"✓ Form loads: {response.status_code == 200}")
    
    # Test 2: Visual improvements are applied
    html = response.text
    
    # Check for Tabler classes
    has_shadow = "shadow" in html
    has_rounded = "rounded-3" in html
    has_large_controls = html.count("form-control-lg") >= 4
    has_better_spacing = html.count("mb-4") >= 8  # Should have many mb-4 classes
    
    print(f"✓ Shadow class applied: {has_shadow}")
    print(f"✓ Rounded class applied: {has_rounded}")
    print(f"✓ Large form controls (4+): {has_large_controls}")
    print(f"✓ Better spacing (mb-4): {has_better_spacing}")
    
    # Test 3: Form structure preserved
    has_name_field = 'name="name"' in html
    has_email_field = 'name="email"' in html
    has_phone_field = 'name="phone"' in html
    has_notes_field = 'name="notes"' in html
    has_terms_field = 'name="accept_terms"' in html
    has_csrf = 'name="csrf_token"' in html
    
    print(f"✓ Name field preserved: {has_name_field}")
    print(f"✓ Email field preserved: {has_email_field}")
    print(f"✓ Phone field preserved: {has_phone_field}")
    print(f"✓ Notes field preserved: {has_notes_field}")
    print(f"✓ Terms field preserved: {has_terms_field}")
    print(f"✓ CSRF protection preserved: {has_csrf}")
    
    # Test 4: Submit button has proper styling
    has_large_button = "btn-lg" in html and "btn-success" in html
    print(f"✓ Submit button properly styled: {has_large_button}")
    
    # Summary
    all_visual_tests_pass = has_shadow and has_rounded and has_large_controls and has_better_spacing
    all_structure_tests_pass = has_name_field and has_email_field and has_phone_field and has_notes_field and has_terms_field and has_csrf
    
    print(f"\n=== SUMMARY ===")
    print(f"Visual improvements applied: {all_visual_tests_pass}")
    print(f"Form functionality preserved: {all_structure_tests_pass}")
    print(f"Overall test result: {'PASS' if all_visual_tests_pass and all_structure_tests_pass else 'FAIL'}")
    
    return all_visual_tests_pass and all_structure_tests_pass

if __name__ == "__main__":
    success = test_signup_form_visual_improvements()
    exit(0 if success else 1)