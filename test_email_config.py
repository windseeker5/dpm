#!/usr/bin/env python3
"""
Test script to verify the email configuration has been updated to LHGI
"""

import sqlite3
import json
from flask_mail import Mail, Message
from flask import Flask

def check_email_settings():
    """Check that email settings have been updated to LHGI configuration."""
    
    print("🔍 Checking Email Configuration...")
    print("="*50)
    
    # Connect to the database
    db_path = 'instance/minipass.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all email-related settings
    cursor.execute("""
        SELECT key, value FROM settings 
        WHERE key LIKE 'MAIL_%' 
        ORDER BY key
    """)
    
    settings = cursor.fetchall()
    
    print("\n📧 Current Email Settings in Database:")
    print("-"*40)
    
    expected_values = {
        'MAIL_SERVER': 'mail.minipass.me',
        'MAIL_USERNAME': 'lhgi@minipass.me',
        'MAIL_DEFAULT_SENDER': 'lhgi@minipass.me',
        'MAIL_SENDER_NAME': 'LHGI',
        'MAIL_PORT': '587',
        'MAIL_USE_TLS': 'True'
    }
    
    all_correct = True
    for key, value in settings:
        if key == 'MAIL_PASSWORD':
            # Don't display password
            status = "✅" if value == 'monsterinc00' else "❌"
            print(f"  {key}: {'*' * 8} {status}")
            if value != 'monsterinc00':
                all_correct = False
        else:
            expected = expected_values.get(key, '')
            status = "✅" if value == expected else "❌"
            print(f"  {key}: {value} {status}")
            
            if key in expected_values and value != expected_values[key]:
                print(f"    Expected: {expected_values[key]}")
                all_correct = False
    
    print("\n" + "="*50)
    
    if all_correct:
        print("✅ SUCCESS: All email settings have been updated to LHGI configuration!")
        print("\n📮 Your emails will now be sent:")
        print("  From: LHGI <lhgi@minipass.me>")
        print("  Server: mail.minipass.me:587 (TLS)")
        print("\n✅ Gmail configuration has been completely REPLACED")
    else:
        print("❌ ERROR: Some settings are still using old values")
        print("Please check the settings page and save the LHGI configuration")
    
    conn.close()
    
    # Test Flask-Mail configuration
    print("\n🧪 Testing Flask-Mail Integration...")
    print("-"*40)
    
    app = Flask(__name__)
    
    # Load settings from database
    settings_dict = {key: value for key, value in settings}
    
    app.config['MAIL_SERVER'] = settings_dict.get('MAIL_SERVER', '')
    app.config['MAIL_PORT'] = int(settings_dict.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = settings_dict.get('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = settings_dict.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = settings_dict.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = settings_dict.get('MAIL_DEFAULT_SENDER', '')
    
    mail = Mail(app)
    
    print(f"  Mail Server: {app.config['MAIL_SERVER']}")
    print(f"  Mail Port: {app.config['MAIL_PORT']}")
    print(f"  Use TLS: {app.config['MAIL_USE_TLS']}")
    print(f"  Username: {app.config['MAIL_USERNAME']}")
    print(f"  Default Sender: {app.config['MAIL_DEFAULT_SENDER']}")
    
    if app.config['MAIL_SERVER'] == 'mail.minipass.me':
        print("\n✅ Flask-Mail is configured to use LHGI email server!")
    else:
        print("\n❌ Flask-Mail is still using old configuration")
    
    return all_correct

if __name__ == "__main__":
    check_email_settings()