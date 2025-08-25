#!/usr/bin/env python3
"""Simple test to capture screenshots of the activity header."""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime

def test_activity_header():
    """Test the activity header and take screenshots."""
    
    # Setup Chrome options
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Create driver
    driver = webdriver.Chrome(options=options)
    
    try:
        # Login
        print("Logging in...")
        driver.get("http://127.0.0.1:8890/login")
        driver.find_element(By.NAME, "email").send_keys("kdresdell@gmail.com")
        driver.find_element(By.NAME, "password").send_keys("admin123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        
        # Navigate to activity
        print("Navigating to activity 1...")
        driver.get("http://127.0.0.1:8890/activity/1")
        time.sleep(2)
        
        # Desktop view
        print("\n=== Desktop View (1920x1080) ===")
        driver.set_window_size(1920, 1080)
        time.sleep(1)
        
        # Check for elements
        try:
            header = driver.find_element(By.CLASS_NAME, "activity-header-clean")
            print("✓ Found activity-header-clean")
            
            # Check for badge
            try:
                badge = driver.find_element(By.CLASS_NAME, "badge-active")
                print(f"✓ Found Active badge: {badge.text}")
            except:
                print("✗ Active badge not found")
            
            # Check for revenue progress
            try:
                progress = driver.find_element(By.CLASS_NAME, "revenue-progress-container")
                print("✓ Found revenue progress container")
                
                # Get progress bar width
                bar = driver.find_element(By.CLASS_NAME, "progress-bar-fill")
                style = bar.get_attribute("style")
                print(f"✓ Progress bar style: {style}")
            except:
                print("✗ Revenue progress not found")
            
            # Check for image
            try:
                image = driver.find_element(By.CLASS_NAME, "activity-image")
                src = image.get_attribute("src")
                print(f"✓ Found activity image: {src}")
            except:
                print("✗ Activity image not found")
            
        except Exception as e:
            print(f"✗ activity-header-clean not found: {e}")
            # Try to find what's on the page
            print("\nChecking page content...")
            page_source = driver.page_source
            if "activity-header-modern" in page_source:
                print("Found: activity-header-modern (old version)")
            if "activity-header" in page_source:
                print("Found: some activity-header class")
            if "Ligue Hockey" in page_source:
                print("Found: Activity content (Ligue Hockey)")
        
        # Take desktop screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop_path = f"/home/kdresdell/Documents/DEV/minipass_env/app/playwright/activity_header_desktop_{timestamp}.png"
        driver.save_screenshot(desktop_path)
        print(f"\nDesktop screenshot saved: {desktop_path}")
        
        # Mobile view
        print("\n=== Mobile View (390x844) ===")
        driver.set_window_size(390, 844)
        time.sleep(1)
        
        # Take mobile screenshot
        mobile_path = f"/home/kdresdell/Documents/DEV/minipass_env/app/playwright/activity_header_mobile_{timestamp}.png"
        driver.save_screenshot(mobile_path)
        print(f"Mobile screenshot saved: {mobile_path}")
        
    finally:
        driver.quit()
        print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_activity_header()