#!/usr/bin/env python3
"""
Screenshot test using webkit2png or similar tools to verify logo visibility.
Since Playwright MCP is not immediately available, using alternative methods.
"""

import subprocess
import os
import time

def test_with_chromium():
    """Test using chromium headless mode to take screenshots."""
    
    url = "http://127.0.0.1:8890/signup/1?passport_type_id=1"
    
    # Test desktop view (1200x800)
    desktop_cmd = [
        "chromium", "--headless", "--disable-gpu", "--no-sandbox",
        f"--window-size=1200,800",
        "--screenshot=/tmp/desktop_logo_test.png",
        url
    ]
    
    # Test mobile view (375x667 - iPhone SE)
    mobile_cmd = [
        "chromium", "--headless", "--disable-gpu", "--no-sandbox", 
        f"--window-size=375,667",
        "--screenshot=/tmp/mobile_logo_test.png",
        url
    ]
    
    try:
        print("Taking desktop screenshot...")
        result = subprocess.run(desktop_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Desktop screenshot saved to /tmp/desktop_logo_test.png")
        else:
            print(f"❌ Desktop screenshot failed: {result.stderr}")
            
        time.sleep(1)
            
        print("Taking mobile screenshot...")
        result = subprocess.run(mobile_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Mobile screenshot saved to /tmp/mobile_logo_test.png")
        else:
            print(f"❌ Mobile screenshot failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Screenshot command timed out")
    except FileNotFoundError:
        print("❌ Chromium not found, trying alternative methods...")
        return False
        
    return True

def test_with_firefox():
    """Test using firefox headless mode."""
    
    url = "http://127.0.0.1:8890/signup/1?passport_type_id=1"
    
    # Firefox headless screenshot
    cmd = [
        "firefox", "--headless", "--screenshot=/tmp/firefox_logo_test.png",
        url
    ]
    
    try:
        print("Taking screenshot with Firefox...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print("✅ Firefox screenshot saved to /tmp/firefox_logo_test.png")
            return True
        else:
            print(f"❌ Firefox screenshot failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Firefox command timed out")
    except FileNotFoundError:
        print("❌ Firefox not found")
        
    return False

def main():
    print("Logo Visibility Screenshot Test")
    print("=" * 40)
    
    success = False
    
    # Try different browsers
    if not success:
        success = test_with_chromium()
        
    if not success:
        success = test_with_firefox()
        
    if not success:
        print("❌ No suitable browser found for screenshots")
        print("Please manually test at: http://127.0.0.1:8890/signup/1?passport_type_id=1")
        print("1. Test on desktop (window width ≥ 768px) - Logo should be visible")
        print("2. Test on mobile (window width < 768px) - Logo should be visible")
        
    return success

if __name__ == "__main__":
    main()