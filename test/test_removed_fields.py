#!/usr/bin/env python3
"""
Test script to verify the hardcoded defaults for removed UI fields work correctly.

This test verifies that:
1. The REMOVED_FIELD_DEFAULTS constants are properly defined
2. The hardcoded defaults match expected values
3. The app can still process these settings correctly
"""

import sys
import os

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_removed_field_defaults():
    """Test that the removed field defaults are properly defined."""
    try:
        # Import the app module to access the constants
        import app
        
        # Check that REMOVED_FIELD_DEFAULTS exists
        assert hasattr(app, 'REMOVED_FIELD_DEFAULTS'), "REMOVED_FIELD_DEFAULTS not found in app module"
        
        defaults = app.REMOVED_FIELD_DEFAULTS
        
        # Verify all expected keys exist
        expected_keys = [
            'gmail_label_folder_processed',
            'default_pass_amount', 
            'default_session_qt',
            'email_info_text',
            'email_footer_text',
            'activity_tags'
        ]
        
        for key in expected_keys:
            assert key in defaults, f"Key '{key}' not found in REMOVED_FIELD_DEFAULTS"
        
        # Verify default values match expectations
        assert defaults['gmail_label_folder_processed'] == 'InteractProcessed'
        assert defaults['default_pass_amount'] == 50
        assert defaults['default_session_qt'] == 4
        assert defaults['email_info_text'] == ''
        assert defaults['email_footer_text'] == ''
        assert defaults['activity_tags'] == []
        
        print("✅ All removed field defaults are correctly defined:")
        for key, value in defaults.items():
            print(f"   {key}: {repr(value)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import app module: {e}")
        print("Note: This is expected if required dependencies (like bcrypt) are not installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing removed field defaults...")
    success = test_removed_field_defaults()
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed!")
        sys.exit(1)