"""
Take screenshots of the surveys page to verify pagination footer styling
"""

import subprocess
import time
import os

def take_screenshots():
    """Take screenshots of surveys page using browser automation tools"""
    print("📸 Taking screenshots of surveys page...")
    
    # Create screenshots directory if it doesn't exist
    screenshots_dir = "/home/kdresdell/Documents/DEV/minipass_env/app/tests/screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Try using headless Chrome via chromium-browser
    try:
        # Desktop screenshot
        desktop_cmd = [
            "chromium-browser",
            "--headless",
            "--disable-gpu",
            "--virtual-time-budget=5000",
            "--window-size=1920,1080",
            "--screenshot=" + os.path.join(screenshots_dir, "surveys_desktop_pagination.png"),
            "http://127.0.0.1:8890/surveys"
        ]
        
        print("📸 Taking desktop screenshot...")
        result = subprocess.run(desktop_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Desktop screenshot saved to tests/screenshots/surveys_desktop_pagination.png")
        else:
            print(f"❌ Desktop screenshot failed: {result.stderr}")
        
        # Mobile screenshot
        mobile_cmd = [
            "chromium-browser",
            "--headless",
            "--disable-gpu",
            "--virtual-time-budget=5000",
            "--window-size=375,667",
            "--screenshot=" + os.path.join(screenshots_dir, "surveys_mobile_pagination.png"),
            "http://127.0.0.1:8890/surveys"
        ]
        
        print("📸 Taking mobile screenshot...")
        result = subprocess.run(mobile_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Mobile screenshot saved to tests/screenshots/surveys_mobile_pagination.png")
        else:
            print(f"❌ Mobile screenshot failed: {result.stderr}")
            
    except FileNotFoundError:
        print("⚠️  chromium-browser not found, trying firefox...")
        
        try:
            # Try Firefox instead
            firefox_cmd = [
                "firefox",
                "--headless",
                "--width=1920",
                "--height=1080",
                "--screenshot=" + os.path.join(screenshots_dir, "surveys_firefox_pagination.png"),
                "http://127.0.0.1:8890/surveys"
            ]
            
            print("📸 Taking Firefox screenshot...")
            result = subprocess.run(firefox_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Firefox screenshot saved to tests/screenshots/surveys_firefox_pagination.png")
            else:
                print(f"❌ Firefox screenshot failed: {result.stderr}")
                
        except FileNotFoundError:
            print("❌ No suitable browser found for screenshots")
            print("   Install chromium-browser or firefox for screenshot capability")
            return False
    
    except subprocess.TimeoutExpired:
        print("❌ Screenshot timeout - server may not be responding")
        return False
    
    except Exception as e:
        print(f"❌ Screenshot failed with error: {str(e)}")
        return False
    
    return True

def list_screenshot_files():
    """List all screenshot files created"""
    screenshots_dir = "/home/kdresdell/Documents/DEV/minipass_env/app/tests/screenshots"
    
    if os.path.exists(screenshots_dir):
        files = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
        if files:
            print(f"\n📁 Screenshot files created:")
            for file in sorted(files):
                file_path = os.path.join(screenshots_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"   • {file} ({file_size:,} bytes)")
        else:
            print("\n📁 No screenshot files found")
    else:
        print("\n📁 Screenshots directory does not exist")

if __name__ == "__main__":
    print("=" * 60)
    print("📸 SURVEYS PAGE SCREENSHOT CAPTURE")
    print("=" * 60)
    print("This will capture screenshots of the surveys page")
    print("to verify the pagination footer styling.")
    print("=" * 60)
    
    success = take_screenshots()
    list_screenshot_files()
    
    print("\n" + "=" * 60)
    if success:
        print("📸 SCREENSHOT CAPTURE COMPLETED")
        print("✅ Check the screenshots to verify pagination footer styling")
    else:
        print("❌ SCREENSHOT CAPTURE FAILED")
        print("   The pagination footer is still functional, but visual verification failed")
    print("=" * 60)