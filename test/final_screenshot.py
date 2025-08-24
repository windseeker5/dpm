#!/usr/bin/env python3
"""
Take final screenshots of logo fix for documentation.
"""

import subprocess
import time
import os

def take_screenshot(url, filename, width=1200, height=800):
    """Take a screenshot using Firefox headless mode."""
    
    screenshot_path = f"/home/kdresdell/Documents/DEV/minipass_env/app/playwright/{filename}"
    
    # Use Firefox to take screenshot
    cmd = [
        "firefox", 
        "--headless", 
        f"--window-size={width},{height}",
        f"--screenshot={screenshot_path}",
        url
    ]
    
    try:
        print(f"Taking screenshot: {filename} ({width}x{height})")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            if os.path.exists(screenshot_path):
                print(f"✅ Screenshot saved: {screenshot_path}")
                return True
            else:
                print(f"❌ Screenshot file not created: {screenshot_path}")
        else:
            print(f"❌ Screenshot failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Screenshot timed out")
    except FileNotFoundError:
        print("❌ Firefox not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return False

def main():
    print("Taking final screenshots of logo fix...")
    
    url = "http://127.0.0.1:8890/signup/1?passport_type_id=1"
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Desktop view
    success1 = take_screenshot(
        url, 
        f"logo_fix_desktop_{timestamp}.png",
        width=1200, 
        height=800
    )
    
    time.sleep(2)
    
    # Mobile view  
    success2 = take_screenshot(
        url,
        f"logo_fix_mobile_{timestamp}.png", 
        width=375,
        height=667
    )
    
    if success1 or success2:
        print("\n✅ Screenshots taken successfully!")
        print("Screenshots saved in: /home/kdresdell/Documents/DEV/minipass_env/app/playwright/")
    else:
        print("\n❌ No screenshots could be taken")
        print("Please test manually at: http://127.0.0.1:8890/signup/1?passport_type_id=1")

if __name__ == "__main__":
    main()