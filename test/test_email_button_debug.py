#!/usr/bin/env python3
"""
DEBUG: Trace exactly what happens when the Send Test Email button is clicked
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime

print("\n" + "="*80)
print("🔍 EMAIL BUTTON DEBUG TEST")
print("="*80)

# Setup session for authentication
session = requests.Session()
base_url = "http://localhost:5000"

# Step 1: Login
print("\n1️⃣ LOGGING IN...")
login_data = {
    "email": "kdresdell@gmail.com",
    "password": "theusual"
}
response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
print(f"   Status: {response.status_code}")
print(f"   Cookies: {dict(session.cookies)}")

# Step 2: Get CSRF token from email template page
print("\n2️⃣ GETTING CSRF TOKEN...")
response = session.get(f"{base_url}/activity/2/email-templates")
print(f"   Status: {response.status_code}")

# Extract CSRF token
import re
csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
if csrf_match:
    csrf_token = csrf_match.group(1)
    print(f"   CSRF Token: {csrf_token[:20]}...")
else:
    print("   ❌ NO CSRF TOKEN FOUND!")
    sys.exit(1)

# Step 3: Send test email using the EXACT same form data as the button
print("\n3️⃣ SENDING TEST EMAIL (simulating button click)...")
print(f"   URL: {base_url}/activity/2/email-test")
print(f"   Method: POST")

test_data = {
    "csrf_token": csrf_token,
    "template_type": "newPass"
}

print(f"   Form data: {test_data}")

# Make the request with full debugging
response = session.post(
    f"{base_url}/activity/2/email-test",
    data=test_data,
    allow_redirects=False
)

print(f"\n4️⃣ RESPONSE:")
print(f"   Status: {response.status_code}")
print(f"   Location: {response.headers.get('Location', 'No redirect')}")

# Check for flash messages in cookies
if 'Set-Cookie' in response.headers:
    print(f"   Cookies set: {response.headers['Set-Cookie'][:100]}...")

# Follow redirect to see flash messages
if response.status_code in [302, 303]:
    print("\n5️⃣ FOLLOWING REDIRECT...")
    redirect_url = response.headers['Location']
    if not redirect_url.startswith('http'):
        redirect_url = base_url + redirect_url
    final_response = session.get(redirect_url)
    
    # Look for flash messages
    if "Test email sent" in final_response.text:
        print("   ✅ SUCCESS FLASH MESSAGE FOUND!")
    else:
        print("   ⚠️ No success message in response")
    
    # Check for error messages
    if "Error" in final_response.text or "error" in final_response.text:
        error_matches = re.findall(r'class="alert[^"]*error[^>]*>([^<]+)', final_response.text)
        if error_matches:
            print(f"   ❌ ERROR FOUND: {error_matches}")

print("\n" + "="*80)
print("📋 SUMMARY:")
print("="*80)
print("The test simulated exactly what the browser does when clicking Send Test Email")
print("Check the Flask server logs above to see if send_email() was actually called")
print("Look for these markers:")
print("  🔥 TEST_EMAIL_TEMPLATE ROUTE CALLED")
print("  📨 SEND_EMAIL FUNCTION CALLED")
print("  ✅✅✅ EMAIL SENT SUCCESSFULLY")
print("\nIf you see all three, the email was sent.")
print("If not, there's a problem in the chain.")
print("="*80)