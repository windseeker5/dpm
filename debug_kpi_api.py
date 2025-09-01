import requests
import json
from requests.sessions import Session

# Detailed debug of API response structure
base_url = 'http://127.0.0.1:5000'
session = Session()

# Get login page for CSRF token
login_page = session.get(f'{base_url}/login')
csrf_token = None
for line in login_page.text.split('\n'):
    if 'csrf_token' in line and 'value=' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

# Login
login_data = {
    'email': 'kdresdell@gmail.com',
    'password': 'admin123',
    'csrf_token': csrf_token
}
session.post(f'{base_url}/login', data=login_data)

# Test multiple periods to see the full data structure
for period in ['7d', '30d', 'all']:
    print(f'=== PERIOD: {period} ===')
    response = session.get(f'{base_url}/api/kpi-data?period={period}')
    
    if response.status_code == 200:
        data = response.json()
        print(f'Success: {data["success"]}')
        print(f'Period: {data["period"]}')
        print(f'Activity ID: {data["activity_id"]}')
        
        # Check each KPI in detail
        for kpi_name, kpi_data in data["kpi_data"].items():
            print(f'  {kpi_name}:')
            print(f'    current: {kpi_data["current"]}')
            print(f'    previous: {kpi_data.get("previous", "N/A")}')
            print(f'    change: {kpi_data.get("change", "N/A")}')
            print(f'    trend length: {len(kpi_data["trend"]) if "trend" in kpi_data else 0}')
            if "trend" in kpi_data and len(kpi_data["trend"]) > 0:
                print(f'    trend sample: {kpi_data["trend"][:5]}...')
        print('')
    else:
        print(f'Error {response.status_code}: {response.text}')
        print('')