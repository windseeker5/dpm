#!/usr/bin/env python3
"""
Direct test - import Flask app and call the route function
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Set environment to avoid duplicate app initialization
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

print("Loading Flask app...")
from app import app, db
from flask import session as flask_session
import time

print("Creating test client...")
client = app.test_client()

# Login first
print("\n1. Logging in...")
with client:
    with client.session_transaction() as sess:
        sess['admin'] = 'kdresdell@gmail.com'

    print("2. Sending survey invitation request...")
    response = client.post('/send-survey-invitations/8',
                          data={'resend_all': 'true'},
                          follow_redirects=False)

    print(f"   Response: {response.status_code}")
    print(f"   Location: {response.headers.get('Location')}")

print("\n3. Waiting 3 seconds for async email sending...")
time.sleep(3)

print("\n4. Reading debug log...")
try:
    with open("/tmp/survey_debug.log", "r") as f:
        log_content = f.read()
        print("\n" + "=" * 80)
        print("DEBUG LOG:")
        print("=" * 80)
        print(log_content)
        print("=" * 80)
except FileNotFoundError:
    print("   ❌ No debug log found!")

# Check email log
print("\n5. Checking email_log table...")
import sqlite3
conn = sqlite3.connect('instance/minipass.db')
c = conn.cursor()
c.execute("""
    SELECT datetime(timestamp, 'localtime'), to_email, subject, result, error_message
    FROM email_log
    ORDER BY timestamp DESC
    LIMIT 3
""")
for row in c.fetchall():
    print(f"   {row}")
conn.close()

print("\nTest completed!")
