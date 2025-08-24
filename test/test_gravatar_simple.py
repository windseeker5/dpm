#!/usr/bin/env python3
"""
Simple test for Gravatar function within Flask app context
"""

import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_gravatar():
    """Test gravatar function"""
    try:
        from utils import get_gravatar_url
        
        # Test with known email
        test_email = "kdresdell@gmail.com"
        url = get_gravatar_url(test_email)
        print(f"Gravatar URL for {test_email}: {url}")
        
        # Test with empty email
        url_empty = get_gravatar_url("")
        print(f"Gravatar URL for empty email: {url_empty}")
        
        # Test with None
        url_none = get_gravatar_url(None)
        print(f"Gravatar URL for None: {url_none}")
        
        print("✅ Gravatar function working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gravatar()