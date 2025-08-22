#!/usr/bin/env python3

"""
Test script to validate the sidebar modifications
- Remove section titles "Main" and "Tools"
- Remove Style Guide and Components menu items
- Add close button for mobile view
"""

import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

def test_sidebar_modifications():
    """Test the sidebar modifications on desktop and mobile"""
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🧪 Testing sidebar modifications...")
        
        # Navigate to the login page
        driver.get("http://127.0.0.1:8890/login")
        time.sleep(2)
        
        # Login
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        
        email_field.send_keys("kdresdell@gmail.com")
        password_field.send_keys("admin123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for dashboard to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "minipass-sidebar"))
        )
        
        print("✅ Logged in successfully")
        
        # Test 1: Check that section titles are removed
        print("\n📋 Test 1: Checking section titles are removed...")
        
        main_title_elements = driver.find_elements(By.XPATH, "//div[@class='nav-section-title'][text()='Main']")
        tools_title_elements = driver.find_elements(By.XPATH, "//div[@class='nav-section-title'][text()='Tools']")
        
        if len(main_title_elements) == 0:
            print("✅ 'Main' section title successfully removed")
        else:
            print("❌ 'Main' section title still present")
            
        if len(tools_title_elements) == 0:
            print("✅ 'Tools' section title successfully removed")
        else:
            print("❌ 'Tools' section title still present")
        
        # Test 2: Check that Style Guide and Components menu items are removed
        print("\n📋 Test 2: Checking menu items are removed...")
        
        style_guide_elements = driver.find_elements(By.XPATH, "//span[@class='nav-text'][text()='Style Guide']")
        components_elements = driver.find_elements(By.XPATH, "//span[@class='nav-text'][text()='Components']")
        
        if len(style_guide_elements) == 0:
            print("✅ Style Guide menu item successfully removed")
        else:
            print("❌ Style Guide menu item still present")
            
        if len(components_elements) == 0:
            print("✅ Components menu item successfully removed")
        else:
            print("❌ Components menu item still present")
        
        # Test 3: Check that remaining menu items are still present
        print("\n📋 Test 3: Checking remaining menu items are present...")
        
        dashboard_element = driver.find_elements(By.XPATH, "//span[@class='nav-text'][text()='Dashboard']")
        activities_element = driver.find_elements(By.XPATH, "//span[@class='nav-text'][text()='Activities']")
        signups_element = driver.find_elements(By.XPATH, "//span[@class='nav-text'][text()='Signups']")
        passports_element = driver.find_elements(By.XPATH, "//span[@class='nav-text'][text()='Passports']")
        surveys_element = driver.find_elements(By.XPATH, "//span[@class='nav-text'][text()='Surveys']")
        ai_analytics_element = driver.find_elements(By.XPATH, "//span[@class='nav-text'][text()='AI Analytics']")
        settings_element = driver.find_elements(By.XPATH, "//span[@class='nav-text'][text()='Settings']")
        
        remaining_items = {
            'Dashboard': len(dashboard_element) > 0,
            'Activities': len(activities_element) > 0,
            'Signups': len(signups_element) > 0,
            'Passports': len(passports_element) > 0,
            'Surveys': len(surveys_element) > 0,
            'AI Analytics': len(ai_analytics_element) > 0,
            'Settings': len(settings_element) > 0
        }
        
        for item, present in remaining_items.items():
            if present:
                print(f"✅ {item} menu item is present")
            else:
                print(f"❌ {item} menu item is missing")
        
        # Test 4: Take desktop screenshot
        print("\n📋 Test 4: Taking desktop screenshot...")
        driver.save_screenshot("/home/kdresdell/Documents/DEV/minipass_env/app/.playwright-mcp/sidebar-modifications-desktop.png")
        print("✅ Desktop screenshot saved")
        
        # Test 5: Test mobile view and close button
        print("\n📋 Test 5: Testing mobile view and close button...")
        
        # Switch to mobile viewport
        driver.set_window_size(375, 667)
        time.sleep(1)
        
        # Look for the mobile menu toggle button
        mobile_toggle = driver.find_element(By.ID, "sidebarToggle")
        print("✅ Mobile menu toggle button found")
        
        # Click to open sidebar
        mobile_toggle.click()
        time.sleep(0.5)
        
        # Check if sidebar is visible
        sidebar = driver.find_element(By.ID, "sidebar")
        if "show" in sidebar.get_attribute("class"):
            print("✅ Sidebar opens on mobile")
        else:
            print("❌ Sidebar doesn't open on mobile")
        
        # Look for the close button
        close_button_elements = driver.find_elements(By.ID, "sidebarClose")
        if len(close_button_elements) > 0:
            print("✅ Close button found in sidebar")
            
            # Test close button functionality
            close_button = close_button_elements[0]
            close_button.click()
            time.sleep(0.5)
            
            # Check if sidebar is closed
            sidebar = driver.find_element(By.ID, "sidebar")
            if "show" not in sidebar.get_attribute("class"):
                print("✅ Close button successfully closes sidebar")
            else:
                print("❌ Close button doesn't close sidebar")
        else:
            print("❌ Close button not found in sidebar")
        
        # Take mobile screenshot
        print("\n📋 Test 6: Taking mobile screenshot...")
        driver.save_screenshot("/home/kdresdell/Documents/DEV/minipass_env/app/.playwright-mcp/sidebar-modifications-mobile.png")
        print("✅ Mobile screenshot saved")
        
        print("\n🎉 Sidebar modification tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        driver.quit()
    
    return True

if __name__ == "__main__":
    success = test_sidebar_modifications()
    sys.exit(0 if success else 1)