#!/usr/bin/env python3
"""
Test script to login and access activity dashboard to check for chart issues
"""
import requests
from bs4 import BeautifulSoup
import re

def test_activity_dashboard_with_login():
    """Login and test activity dashboard charts"""
    
    session = requests.Session()
    
    try:
        # First, get the login page to see if we need CSRF tokens
        print("=== GETTING LOGIN PAGE ===")
        login_response = session.get('http://localhost:5000/login')
        print(f"Login page status: {login_response.status_code}")
        
        # Try login with known credentials (common test passwords)
        print("\n=== ATTEMPTING LOGIN ===")
        login_data = {
            'email': 'test@example.com',
            'password': 'admin123'  # Common test password
        }
        
        login_post = session.post('http://localhost:5000/login', data=login_data)
        print(f"Login post status: {login_post.status_code}")
        print(f"Final URL after login: {login_post.url}")
        
        # Check if redirected to dashboard (successful login)
        if '/dashboard' in login_post.url:
            print("✓ Login successful!")
        else:
            print("✗ Login may have failed")
            print(f"Response text preview: {login_post.text[:200]}...")
            
            # Try another password
            print("\n=== TRYING ALTERNATE LOGIN ===")
            login_data = {
                'email': 'jf@jfgoulet.com', 
                'password': 'password'
            }
            login_post = session.post('http://localhost:5000/login', data=login_data)
            if '/dashboard' in login_post.url:
                print("✓ Login successful with alternate credentials!")
            else:
                print("✗ Alternate login failed too")
                return
        
        # Now try to access activity dashboard
        print("\n=== ACCESSING ACTIVITY DASHBOARD ===")
        dashboard_response = session.get('http://localhost:5000/activity-dashboard/1')
        print(f"Activity dashboard status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            print("✓ Activity dashboard accessible")
            
            # Parse HTML and check for charts
            soup = BeautifulSoup(dashboard_response.text, 'html.parser')
            
            print("\n=== CHART CONTAINER CHECK ===")
            chart_ids = ['revenue-chart', 'active-users-chart', 'passports-created-chart', 'unpaid-passports-chart']
            for chart_id in chart_ids:
                chart_div = soup.find('div', {'id': chart_id})
                if chart_div:
                    print(f"✓ Found {chart_id}")
                else:
                    print(f"✗ Missing {chart_id}")
            
            print("\n=== JAVASCRIPT FUNCTION CHECK ===")
            script_tags = soup.find_all('script')
            js_content = '\n'.join([script.string or '' for script in script_tags if script.string])
            
            functions_to_check = [
                'initializeChartsWithData',
                'initializeApexChartsForKPI', 
                'initializeKPIBarChart'
            ]
            
            for func_name in functions_to_check:
                if func_name in js_content:
                    print(f"✓ Found function: {func_name}")
                else:
                    print(f"✗ Missing function: {func_name}")
                    
            print("\n=== APEX CHARTS LIBRARY CHECK ===")
            apex_script = soup.find('script', src=re.compile(r'apexcharts'))
            if apex_script:
                print(f"✓ Found ApexCharts library: {apex_script.get('src')}")
            else:
                print("✗ ApexCharts library not found")
            
        else:
            print(f"✗ Cannot access activity dashboard: {dashboard_response.status_code}")
            if dashboard_response.status_code == 302:
                print("Still being redirected - login issue")
        
    except Exception as e:
        print(f"Error testing activity dashboard: {e}")

if __name__ == "__main__":
    test_activity_dashboard_with_login()