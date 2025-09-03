#!/usr/bin/env python3
"""
Integration test for content security in the Flask application
Tests that the ContentSanitizer integrates properly with the Flask app
"""

import sys
import os

# Add the parent directory to Python path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_security_integration():
    """Test that ContentSanitizer works in the application context"""
    
    print("Testing ContentSanitizer integration...")
    
    # Test importing the ContentSanitizer from utils
    try:
        from utils import ContentSanitizer
        print("✅ ContentSanitizer imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ContentSanitizer: {e}")
        return False
    
    # Test that bleach is available
    try:
        import bleach
        print("✅ Bleach library available")
    except ImportError as e:
        print(f"❌ Bleach library not available: {e}")
        return False
    
    # Test basic sanitization functionality
    test_cases = [
        {
            'name': 'XSS Script Tag Removal',
            'input': '<p>Hello</p><script>alert("XSS")</script><p>World</p>',
            'expected_not_in': ['<script>', 'alert("XSS")'],
            'expected_in': ['<p>Hello</p>', '<p>World</p>']
        },
        {
            'name': 'Safe HTML Preservation',
            'input': '<p>Hello <strong>world</strong>!</p>',
            'expected_in': ['<p>', '<strong>', 'Hello', 'world']
        },
        {
            'name': 'Malicious URL Rejection',
            'input': 'javascript:alert("XSS")',
            'url_test': True,
            'expected_result': ''
        },
        {
            'name': 'Safe URL Preservation',
            'input': 'https://example.com',
            'url_test': True,
            'expected_result': 'https://example.com'
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        
        if test_case.get('url_test'):
            # Test URL validation
            result = ContentSanitizer.validate_url(test_case['input'])
            if result == test_case['expected_result']:
                print(f"✅ URL validation passed: '{test_case['input']}' -> '{result}'")
            else:
                print(f"❌ URL validation failed: '{test_case['input']}' -> '{result}' (expected '{test_case['expected_result']}')")
                all_passed = False
        else:
            # Test HTML sanitization
            result = ContentSanitizer.sanitize_html(test_case['input'])
            
            # Check items that should NOT be in the result
            if 'expected_not_in' in test_case:
                for item in test_case['expected_not_in']:
                    if item in result:
                        print(f"❌ Found dangerous content '{item}' in result: {result}")
                        all_passed = False
                    else:
                        print(f"✅ Dangerous content '{item}' properly removed")
            
            # Check items that should be in the result
            if 'expected_in' in test_case:
                for item in test_case['expected_in']:
                    if item not in result:
                        print(f"❌ Expected content '{item}' not found in result: {result}")
                        all_passed = False
                    else:
                        print(f"✅ Safe content '{item}' preserved")
    
    # Test template data sanitization
    print(f"\n🧪 Testing: Complete Template Data Sanitization")
    template_data = {
        'subject': 'Test <script>alert("XSS")</script> Subject',
        'title': 'Test <b>Title</b>',
        'intro_text': '<p>Safe <strong>content</strong></p><script>alert("XSS")</script>',
        'cta_url': 'javascript:alert("XSS")',
        'custom_message': '<p>Custom message</p>'
    }
    
    sanitized = ContentSanitizer.sanitize_email_template_data(template_data)
    
    # Check that script tags were removed
    for key, value in sanitized.items():
        if '<script>' in str(value) or 'alert("XSS")' in str(value):
            print(f"❌ Dangerous script content found in {key}: {value}")
            all_passed = False
    
    # Check that safe content is preserved
    if '<p>' in sanitized.get('intro_text', '') and '<strong>' in sanitized.get('intro_text', ''):
        print("✅ Safe HTML tags preserved in intro_text")
    else:
        print(f"❌ Safe HTML tags not preserved in intro_text: {sanitized.get('intro_text', '')}")
        all_passed = False
    
    # Check that malicious URL was rejected
    if sanitized.get('cta_url') == '':
        print("✅ Malicious javascript: URL properly rejected")
    else:
        print(f"❌ Malicious URL not rejected: {sanitized.get('cta_url')}")
        all_passed = False
    
    if all_passed:
        print(f"\n🎉 All security integration tests passed!")
        return True
    else:
        print(f"\n💥 Some security integration tests failed!")
        return False


if __name__ == '__main__':
    success = test_security_integration()
    if not success:
        sys.exit(1)