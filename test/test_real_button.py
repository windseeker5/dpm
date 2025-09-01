#!/usr/bin/env python3
"""
TEST THE ACTUAL BUTTON - Simulate exactly what happens when YOU click it
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "🔴"*40)
print("TESTING THE ACTUAL BUTTON IN THE BROWSER")
print("🔴"*40)

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Use headless Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

print("\n1️⃣ Starting browser...")
try:
    driver = webdriver.Chrome(options=options)
except:
    print("❌ Chrome not found, trying Firefox...")
    from selenium.webdriver.firefox.options import Options
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)

print("2️⃣ Logging in...")
driver.get("http://localhost:5000/login")
driver.find_element(By.NAME, "email").send_keys("kdresdell@gmail.com")
driver.find_element(By.NAME, "password").send_keys("theusual")
driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]").click()

print("3️⃣ Going to Monday Comedy Show...")
time.sleep(1)
driver.get("http://localhost:5000/activity/2/dashboard")

print("4️⃣ Clicking Email Templates...")
email_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Email Templates')]")
email_button.click()

print("5️⃣ Waiting for page to load...")
time.sleep(2)

print("6️⃣ CLICKING THE SEND TEST EMAIL BUTTON...")
# Find the first Send Test Email button
test_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Send Test Email')]")
print(f"   Found button: {test_button.text}")
print(f"   Button onclick: {test_button.get_attribute('onclick')}")

# Click it
test_button.click()

print("7️⃣ Waiting for response...")
time.sleep(3)

# Check for success message
page_source = driver.page_source
if "Test email sent" in page_source:
    print("   ✅ SUCCESS MESSAGE FOUND IN PAGE!")
else:
    print("   ❌ No success message found")

# Check current URL
print(f"8️⃣ Current URL: {driver.current_url}")

driver.quit()

print("\n" + "🔴"*40)
print("IF YOU SEE THE SUCCESS MESSAGE ABOVE,")
print("THE BUTTON IS WORKING CORRECTLY.")
print("CHECK YOUR SPAM FOLDER FOR: lhgi@minipass.me")
print("🔴"*40)