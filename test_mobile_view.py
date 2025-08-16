#!/usr/bin/env python3

import requests
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_mobile_view():
    # Set up Firefox in headless mode
    options = Options()
    options.headless = True
    
    # Set mobile viewport
    options.add_argument("--width=390")
    options.add_argument("--height=844")
    
    driver = webdriver.Firefox(options=options)
    
    try:
        # Navigate to login page
        driver.get("http://127.0.0.1:8890/login")
        
        # Wait for login form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        
        # Fill login form
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        
        email_field.send_keys("kdresdell@gmail.com")
        password_field.send_keys("admin123")
        
        # Submit form
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for dashboard to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "d-md-none"))
        )
        
        # Set mobile viewport size
        driver.set_window_size(390, 844)
        
        # Scroll to mobile activities section
        mobile_section = driver.find_element(By.CSS_SELECTOR, ".d-md-none .d-flex.overflow-auto")
        driver.execute_script("arguments[0].scrollIntoView();", mobile_section)
        
        time.sleep(2)
        
        # Take screenshot
        driver.save_screenshot("/home/kdresdell/Documents/DEV/minipass_env/app/.playwright-mcp/mobile-height-test.png")
        print("Screenshot saved to mobile-height-test.png")
        
        # Get heights of activity cards vs placeholder
        activity_cards = driver.find_elements(By.CSS_SELECTOR, ".d-md-none .flex-shrink-0 .card")
        
        if len(activity_cards) >= 2:
            # Compare first activity card with last (placeholder) card
            first_card_height = activity_cards[0].size['height']
            last_card_height = activity_cards[-1].size['height']
            
            print(f"First activity card height: {first_card_height}px")
            print(f"Placeholder card height: {last_card_height}px")
            print(f"Height difference: {abs(first_card_height - last_card_height)}px")
            
            if first_card_height == last_card_height:
                print("✅ Heights match exactly!")
            else:
                print("❌ Heights don't match - need further adjustment")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_mobile_view()