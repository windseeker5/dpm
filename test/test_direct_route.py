#!/usr/bin/env python3
"""
DIRECT TEST: Call the test_email_template route directly with Flask test client
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from datetime import datetime

print("\n" + "="*80)
print("🔥 DIRECT ROUTE TEST - CALLING test_email_template")
print("="*80)

with app.test_client() as client:
    # Login first
    print("\n1️⃣ Logging in as admin...")
    with client.session_transaction() as sess:
        sess['admin'] = 'kdresdell@gmail.com'
    
    # Get CSRF token
    print("\n2️⃣ Getting CSRF token...")
    response = client.get('/activity/2/email-templates')
    import re
    csrf_match = re.search(b'name="csrf_token" value="([^"]+)"', response.data)
    if csrf_match:
        csrf_token = csrf_match.group(1).decode()
        print(f"   Got CSRF token: {csrf_token[:20]}...")
    else:
        csrf_token = None
        print("   ⚠️ No CSRF token found, continuing anyway...")
    
    # Call the test email route
    print("\n3️⃣ Calling /activity/2/email-test route...")
    print("   This should trigger all our debug logging")
    print("   Watch for these markers:")
    print("     🔥 TEST_EMAIL_TEMPLATE ROUTE CALLED")
    print("     📨 SEND_EMAIL FUNCTION CALLED")
    print("     ✅✅✅ EMAIL SENT SUCCESSFULLY")
    print("\n" + "-"*60)
    
    data = {'template_type': 'newPass'}
    if csrf_token:
        data['csrf_token'] = csrf_token
    
    response = client.post('/activity/2/email-test', data=data, follow_redirects=False)
    
    print("-"*60)
    print(f"\n4️⃣ Response status: {response.status_code}")
    print(f"   Location: {response.location if response.status_code in [302, 303] else 'No redirect'}")
    
    # Follow redirect to check flash messages
    if response.status_code in [302, 303]:
        final_response = client.get(response.location)
        if b"Test email sent" in final_response.data:
            print("   ✅ Success flash message found in response!")
        else:
            print("   ⚠️ No success message in response")

print("\n" + "="*80)
print("📋 CHECK ABOVE FOR DEBUG OUTPUT")
print("="*80)
print("If you see all three markers, the email was sent.")
print("If not, check which step failed.")
print("="*80)