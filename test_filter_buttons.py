#!/usr/bin/env python3
"""
Test script to verify filter button functionality on activity dashboard
"""
import requests
import re
from bs4 import BeautifulSoup

# Test filter button rendering
def test_filter_buttons():
    session = requests.Session()
    
    # Login first
    login_data = {
        'email': 'kdresdell@gmail.com',
        'password': 'admin123'
    }
    
    print("Testing filter button functionality...")
    
    # Get login page to extract CSRF token
    login_page = session.get('http://127.0.0.1:8890/login')
    
    # Extract CSRF token
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    if csrf_token:
        login_data['csrf_token'] = csrf_token['value']
    
    # Login with follow redirects
    login_response = session.post('http://127.0.0.1:8890/login', data=login_data, allow_redirects=True)
    
    if login_response.status_code == 200:
        print("✓ Login successful")
        
        # Check if we can access the main dashboard first
        main_dashboard = session.get('http://127.0.0.1:8890/dashboard')
        print(f"Main dashboard status: {main_dashboard.status_code}")
        
        # Check activities page
        activities_page = session.get('http://127.0.0.1:8890/activities')
        print(f"Activities page status: {activities_page.status_code}")
        
        if activities_page.status_code == 200:
            # Extract activity dashboard links
            soup_activities = BeautifulSoup(activities_page.text, 'html.parser')
            dashboard_links = soup_activities.find_all('a', href=True)
            dashboard_urls = [link['href'] for link in dashboard_links if '/activity/' in link['href'] and '/dashboard' in link['href']]
            
            if dashboard_urls:
                print(f"Found dashboard URLs: {dashboard_urls[:3]}")  # Show first 3
                dashboard_url = 'http://127.0.0.1:8890' + dashboard_urls[0]
            else:
                print("No dashboard links found, trying activity/1/dashboard")
                dashboard_url = 'http://127.0.0.1:8890/activity/1/dashboard'
        else:
            dashboard_url = 'http://127.0.0.1:8890/activity/1/dashboard'
        
        # Navigate to activity dashboard
        dashboard_response = session.get(dashboard_url)
        
        if dashboard_response.status_code == 200:
            print("✓ Activity dashboard loaded")
            
            # Parse HTML to check filter buttons
            soup = BeautifulSoup(dashboard_response.text, 'html.parser')
            
            # Find filter buttons
            filter_buttons = soup.find_all('button', class_='github-filter-btn')
            
            print(f"Found {len(filter_buttons)} filter buttons")
            
            for i, button in enumerate(filter_buttons):
                onclick = button.get('onclick', 'No onclick')
                btn_id = button.get('id', 'No ID')
                btn_class = button.get('class', [])
                
                print(f"Button {i+1}:")
                print(f"  ID: {btn_id}")
                print(f"  Classes: {' '.join(btn_class)}")
                print(f"  OnClick: {onclick}")
                print(f"  Text: {button.get_text().strip()}")
                print()
            
            # Check if CSS is properly loaded
            style_tags = soup.find_all('style')
            css_content = '\n'.join([tag.get_text() for tag in style_tags])
            
            if '.github-filter-btn' in css_content:
                print("✓ CSS for filter buttons found in page")
                
                # Check for specific CSS properties
                if 'cursor: pointer' in css_content:
                    print("✓ Cursor pointer style found")
                else:
                    print("✗ Cursor pointer style missing")
                    
                if 'background: #e1e4e8' in css_content:
                    print("✓ Button background style found")
                else:
                    print("✗ Button background style missing")
            else:
                print("✗ CSS for filter buttons not found")
            
            # Check JavaScript functions
            script_tags = soup.find_all('script')
            js_content = '\n'.join([tag.get_text() for tag in script_tags if tag.get_text()])
            
            if 'function filterPassports(' in js_content:
                print("✓ filterPassports function found")
            else:
                print("✗ filterPassports function missing")
                
            if 'function filterSignups(' in js_content:
                print("✓ filterSignups function found")
            else:
                print("✗ filterSignups function missing")
                
        else:
            print(f"✗ Failed to load dashboard: {dashboard_response.status_code}")
    else:
        print(f"✗ Login failed: {login_response.status_code}")

if __name__ == '__main__':
    test_filter_buttons()