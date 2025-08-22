#!/usr/bin/env python3
"""Verify the filter buttons are working correctly"""

import requests
from bs4 import BeautifulSoup

# Start a session
session = requests.Session()

# Login
login_url = "http://127.0.0.1:8890/login"
login_page = session.get(login_url)
soup = BeautifulSoup(login_page.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

login_data = {
    "email": "kdresdell@gmail.com",
    "password": "admin123",
    "csrf_token": csrf_token
}

login_response = session.post(login_url, data=login_data, allow_redirects=False)

# Access signups page
response = session.get("http://127.0.0.1:8890/signups")
soup = BeautifulSoup(response.text, 'html.parser')

# Extract and display filter section HTML
filter_section = soup.find('div', {'id': 'filterButtons'})

if filter_section:
    print("✅ Filter buttons HTML structure:")
    print("-" * 50)
    
    # Pretty print the filter section
    from bs4 import BeautifulSoup
    pretty_html = BeautifulSoup(str(filter_section), 'html.parser').prettify()
    
    # Show first 50 lines to see the structure
    lines = pretty_html.split('\n')
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3}: {line}")
    
    print("-" * 50)
    print(f"\n📊 Total lines in filter section: {len(lines)}")
    
    # Count and display button info
    buttons = filter_section.find_all('button', class_='btn-filter')
    print(f"\n🔘 Found {len(buttons)} filter buttons:")
    for btn in buttons:
        text = btn.get_text(strip=True)
        classes = ' '.join(btn.get('class', []))
        filter_type = btn.get('data-filter', 'N/A')
        print(f"  - {text:20} | filter: {filter_type:10} | classes: {classes}")
else:
    print("❌ Filter section not found")