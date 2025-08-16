#!/usr/bin/env python3
"""Take a screenshot of the signups page with filter buttons"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

try:
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    
    # Navigate to login page
    driver.get("http://127.0.0.1:8890/login")
    
    # Fill in login form
    email_field = driver.find_element(By.NAME, "email")
    password_field = driver.find_element(By.NAME, "password")
    
    email_field.send_keys("kdresdell@gmail.com")
    password_field.send_keys("admin123")
    
    # Submit form
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()
    
    # Wait for redirect and navigate to signups
    time.sleep(2)
    driver.get("http://127.0.0.1:8890/signups")
    
    # Wait for filter buttons to load
    wait = WebDriverWait(driver, 10)
    filter_section = wait.until(EC.presence_of_element_located((By.ID, "filterButtons")))
    
    # Take screenshot
    driver.save_screenshot("/tmp/signups_with_filters.png")
    print("✅ Screenshot saved to /tmp/signups_with_filters.png")
    
    # Test clicking on filters
    filters_to_test = ["unpaid", "paid", "pending", "approved"]
    
    for filter_type in filters_to_test:
        # Find and click the filter button
        filter_btn = driver.find_element(By.XPATH, f"//button[@data-filter='{filter_type}']")
        filter_btn.click()
        time.sleep(2)  # Wait for page to reload
        
        # Take screenshot of filtered view
        driver.save_screenshot(f"/tmp/signups_filter_{filter_type}.png")
        print(f"✅ Screenshot of {filter_type} filter saved")
    
    driver.quit()
    print("\n✅ All screenshots captured successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if 'driver' in locals():
        driver.quit()