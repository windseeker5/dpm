#!/usr/bin/env python3
"""
Test script to verify dropdown menu fix on signups page
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import os

def test_dropdown_fix():
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("🚀 Starting dropdown fix test...")
        
        # Navigate to login page
        driver.get("http://127.0.0.1:8890/login")
        print("📍 Navigated to login page")
        
        # Login
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys("kdresdell@gmail.com")
        
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys("admin123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        print("✅ Logged in successfully")
        
        # Wait for redirect and navigate to signups page
        time.sleep(2)
        driver.get("http://127.0.0.1:8890/signups")
        print("📍 Navigated to signups page")
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table")))
        time.sleep(2)
        
        # Test 1: Open first dropdown
        print("\n🧪 Test 1: Opening first dropdown...")
        dropdowns = driver.find_elements(By.CSS_SELECTOR, "[data-bs-toggle='dropdown']")
        
        if len(dropdowns) >= 2:
            # Click first dropdown in table (skip bulk actions dropdown)
            first_dropdown = dropdowns[1] if len(dropdowns) > 1 else dropdowns[0]
            driver.execute_script("arguments[0].scrollIntoView(true);", first_dropdown)
            time.sleep(1)
            first_dropdown.click()
            time.sleep(1)
            
            # Take screenshot with first dropdown open
            driver.save_screenshot("/home/kdresdell/Documents/DEV/minipass_env/app/tests/dropdown_test_1_open.png")
            print("📸 Screenshot 1: First dropdown open")
            
            # Check if dropdown menu is visible
            first_menu = driver.find_element(By.CSS_SELECTOR, ".dropdown-menu.show")
            if first_menu.is_displayed():
                print("✅ First dropdown menu is visible")
            
            # Test 2: Open second dropdown (should close first)
            print("\n🧪 Test 2: Opening second dropdown (should close first)...")
            if len(dropdowns) >= 3:
                second_dropdown = dropdowns[2]
                driver.execute_script("arguments[0].scrollIntoView(true);", second_dropdown)
                time.sleep(1)
                second_dropdown.click()
                time.sleep(1)
                
                # Take screenshot with second dropdown open
                driver.save_screenshot("/home/kdresdell/Documents/DEV/minipass_env/app/tests/dropdown_test_2_second_open.png")
                print("📸 Screenshot 2: Second dropdown open, first should be closed")
                
                # Check how many dropdowns are open
                open_menus = driver.find_elements(By.CSS_SELECTOR, ".dropdown-menu.show")
                print(f"📊 Number of open dropdown menus: {len(open_menus)}")
                
                if len(open_menus) == 1:
                    print("✅ SUCCESS: Only one dropdown is open at a time!")
                else:
                    print(f"❌ FAIL: {len(open_menus)} dropdowns are open (expected 1)")
            
            # Test 3: Click outside to close
            print("\n🧪 Test 3: Clicking outside to close dropdown...")
            body = driver.find_element(By.TAG_NAME, "body")
            body.click()
            time.sleep(1)
            
            # Take screenshot after clicking outside
            driver.save_screenshot("/home/kdresdell/Documents/DEV/minipass_env/app/tests/dropdown_test_3_all_closed.png")
            print("📸 Screenshot 3: All dropdowns should be closed")
            
            # Check if all dropdowns are closed
            open_menus = driver.find_elements(By.CSS_SELECTOR, ".dropdown-menu.show")
            print(f"📊 Number of open dropdown menus after clicking outside: {len(open_menus)}")
            
            if len(open_menus) == 0:
                print("✅ SUCCESS: All dropdowns closed when clicking outside!")
            else:
                print(f"❌ FAIL: {len(open_menus)} dropdowns still open")
            
            # Test 4: Test Escape key
            print("\n🧪 Test 4: Testing Escape key to close dropdown...")
            first_dropdown.click()
            time.sleep(1)
            
            # Press Escape
            actions = ActionChains(driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            
            # Check if dropdown closed
            open_menus = driver.find_elements(By.CSS_SELECTOR, ".dropdown-menu.show")
            print(f"📊 Number of open dropdown menus after Escape key: {len(open_menus)}")
            
            if len(open_menus) == 0:
                print("✅ SUCCESS: Dropdown closed with Escape key!")
            else:
                print(f"❌ FAIL: {len(open_menus)} dropdowns still open after Escape")
            
            # Final screenshot
            driver.save_screenshot("/home/kdresdell/Documents/DEV/minipass_env/app/tests/dropdown_test_final.png")
            print("\n📸 Screenshot 4: Final state of page")
            
        else:
            print("❌ Not enough dropdowns found on page to test")
        
        print("\n✅ Test completed! Check screenshots in /tests/ folder")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        driver.save_screenshot("/home/kdresdell/Documents/DEV/minipass_env/app/tests/dropdown_test_error.png")
    
    finally:
        driver.quit()
        print("🏁 Browser closed")

if __name__ == "__main__":
    test_dropdown_fix()