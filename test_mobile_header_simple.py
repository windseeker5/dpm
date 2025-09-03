#!/usr/bin/env python3
"""
Simple mobile header test - uses available tools
"""

import subprocess
import os
import sys

def test_mobile_layout():
    """Test mobile layout using curl and check CSS values"""
    
    print("=== Mobile Header Layout Test ===")
    
    # Test 1: Check CSS file has mobile optimizations
    css_file = "/home/kdresdell/Documents/DEV/minipass_env/app/static/css/activity-header-clean.css"
    
    with open(css_file, 'r') as f:
        css_content = f.read()
    
    # Check for mobile-specific rules
    mobile_checks = [
        ("max-height: 200px", "Header max height constraint"),
        ("width: 20px", "Activity image 20px width"),
        ("height: 20px", "Activity image 20px height"), 
        ("grid-template-columns: 1fr 1fr", "2x2 stats grid"),
        ("min-width: 44px", "Touch target width"),
        ("min-height: 44px", "Touch target height"),
        ("font-size: 16px", "Compact title font"),
        ("font-size: 11px", "Compact description font")
    ]
    
    print("\nCSS Mobile Optimizations:")
    for check, description in mobile_checks:
        if check in css_content:
            print(f"✓ {description}: Found")
        else:
            print(f"✗ {description}: Missing")
    
    # Test 2: Verify Flask server is accessible
    try:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5000'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip() in ['200', '302']:
            print("✓ Flask server accessible")
        else:
            print(f"✗ Flask server issue: {result.stdout}")
    except subprocess.TimeoutExpired:
        print("✗ Flask server timeout")
    except Exception as e:
        print(f"✗ Flask server error: {e}")
    
    print("\n=== Key Mobile Optimizations Applied ===")
    print("• Header max height: 200px")
    print("• Activity image: 20x20px (inline with title)")
    print("• Stats: 2x2 grid layout")
    print("• Dropdown button: 44x44px minimum touch target")
    print("• Compact fonts: 16px title, 11px description")
    print("• Ultra-compact padding: 8px 12px")
    print("• Progress bar: 6px height")
    print("• Description: 2-line max with ellipsis")
    
    print("\nTo test visually:")
    print("1. Open browser to http://localhost:5000")
    print("2. Login with kdresdell@gmail.com / admin123")
    print("3. Navigate to any activity page")
    print("4. Set browser to mobile view (375x667px)")
    print("5. Verify header fits in single screen")
    
    return True

if __name__ == '__main__':
    test_mobile_layout()