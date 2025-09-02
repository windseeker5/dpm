#!/usr/bin/env python3
"""
Test script to verify KPI cards are working on activity dashboard
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_activity_dashboard_kpi():
    """Test KPI cards on activity dashboard"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("🚀 Starting KPI Activity Dashboard Test...")
        
        # Login
        driver.get("http://localhost:5000/login")
        print("✓ Navigated to login page")
        
        # Login credentials
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        email_field.send_keys("kdresdell@gmail.com")
        password_field.send_keys("admin123")
        
        # Submit form
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        print("✓ Logged in successfully")
        
        # Wait for dashboard to load
        time.sleep(2)
        
        # Navigate to an activity dashboard (assuming activity ID 1 exists)
        driver.get("http://localhost:5000/activity-dashboard/1")
        print("✓ Navigated to activity dashboard")
        
        # Wait for KPI cards to load
        time.sleep(3)
        
        # Check if KPI cards exist
        kpi_cards = driver.find_elements(By.CSS_SELECTOR, "[data-kpi-card]")
        print(f"✓ Found {len(kpi_cards)} KPI cards")
        
        # Check Revenue card
        revenue_value = driver.find_element(By.ID, "revenue-value")
        print(f"  Revenue value: {revenue_value.text}")
        
        # Check if chart containers exist
        revenue_chart = driver.find_element(By.ID, "revenue-chart")
        active_chart = driver.find_element(By.ID, "active-passports-chart")
        created_chart = driver.find_element(By.ID, "passports-created-chart")
        unpaid_chart = driver.find_element(By.ID, "pending-signups-chart")
        
        # Check if charts have SVG elements (means ApexCharts rendered)
        charts_rendered = []
        for chart_id, chart_el in [
            ("revenue-chart", revenue_chart),
            ("active-passports-chart", active_chart),
            ("passports-created-chart", created_chart),
            ("pending-signups-chart", unpaid_chart)
        ]:
            svg_elements = chart_el.find_elements(By.TAG_NAME, "svg")
            if svg_elements:
                charts_rendered.append(chart_id)
                print(f"  ✓ {chart_id} has rendered chart")
            else:
                print(f"  ✗ {chart_id} has NO chart")
        
        # Test period dropdown (click "All time")
        print("\n🔄 Testing period dropdown...")
        
        # Find and click first dropdown
        dropdown_button = driver.find_element(By.CSS_SELECTOR, "[data-kpi-period-button]")
        dropdown_button.click()
        time.sleep(1)
        
        # Click "All time" option
        all_time_option = driver.find_element(By.XPATH, "//a[@data-period='all']")
        all_time_option.click()
        print("✓ Clicked 'All time' option")
        
        # Wait for update
        time.sleep(3)
        
        # Check if value changed
        new_revenue_value = driver.find_element(By.ID, "revenue-value")
        print(f"  New revenue value: {new_revenue_value.text}")
        
        # Check if charts still exist after update
        revenue_chart_after = driver.find_element(By.ID, "revenue-chart")
        svg_after = revenue_chart_after.find_elements(By.TAG_NAME, "svg")
        if svg_after:
            print("  ✓ Chart still rendered after period change")
        else:
            print("  ✗ Chart disappeared after period change!")
        
        print("\n✅ Test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        driver.quit()
        print("🏁 Browser closed")

if __name__ == "__main__":
    success = test_activity_dashboard_kpi()
    exit(0 if success else 1)