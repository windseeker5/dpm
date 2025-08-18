"""
Simple test script for Settings page
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8890"

# Create a session to maintain cookies
session = requests.Session()

# Login
login_data = {
    'email': 'kdresdell@gmail.com',
    'password': 'admin123'
}

print("🔐 Logging in...")
response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
if response.status_code in [302, 303]:
    print("✅ Login successful")
else:
    print(f"❌ Login failed with status: {response.status_code}")

# Test API endpoint
print("\n📊 Testing API endpoint...")
response = session.get(f"{BASE_URL}/api/test-settings")
if response.status_code == 200:
    data = response.json()
    print(f"✅ API Response: {json.dumps(data, indent=2)}")
    
    # Verify expected values
    settings = data.get('data', {})
    
    if settings.get('org_name') == 'Hockey Gagnon Image':
        print("✅ Organization name is correct")
    else:
        print(f"❌ Organization name: {settings.get('org_name')}")
    
    if settings.get('logo_file_exists'):
        print(f"✅ Logo file exists at: {settings.get('org_logo_path')}")
    else:
        print("❌ Logo file does not exist")
    
    if 'notifications_enabled' in settings:
        print(f"✅ Email notifications: {'Enabled' if settings['notifications_enabled'] else 'Disabled'}")
    
    if 'analytics_enabled' in settings:
        print(f"✅ Analytics tracking: {'Enabled' if settings['analytics_enabled'] else 'Disabled'}")
else:
    print(f"❌ API test failed with status: {response.status_code}")

print("\n✨ Test completed!")