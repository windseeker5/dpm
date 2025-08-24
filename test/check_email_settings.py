#!/usr/bin/env python3
"""Quick check of email settings"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_setting
from app import app

with app.app_context():
    print("\n=== CURRENT EMAIL SETTINGS ===")
    print(f"MAIL_SERVER (SMTP): {get_setting('MAIL_SERVER')}")
    print(f"MAIL_PORT: {get_setting('MAIL_PORT')}")
    print(f"MAIL_USERNAME: {get_setting('MAIL_USERNAME')}")
    print(f"MAIL_USE_TLS: {get_setting('MAIL_USE_TLS')}")
    print(f"PAYMENT_EMAIL_ADDRESS: {get_setting('PAYMENT_EMAIL_ADDRESS')}")
    
    print("\n=== PROBLEM IDENTIFIED ===")
    print("The code in utils.py line 633 is hardcoded to use:")
    print("  mail = imaplib.IMAP4_SSL('imap.gmail.com')")
    print("\nBut your email is NOT a Gmail account!")
    print("You need to use your actual IMAP server.")
    
    mail_server = get_setting('MAIL_SERVER')
    if mail_server:
        if 'smtp' in mail_server.lower():
            imap_suggestion = mail_server.lower().replace('smtp', 'imap')
        else:
            imap_suggestion = mail_server
        print(f"\nSuggested IMAP server: {imap_suggestion}")
        print("\nTo fix this:")
        print(f"1. Replace 'imap.gmail.com' with '{imap_suggestion}' in utils.py line 633")
        print("2. Or better: add IMAP_SERVER setting and use that")