#!/usr/bin/env python3
"""
Test different IMAP methods to find what actually works on mail.minipass.me
"""

import imaplib
from app import app
from utils import get_setting

with app.app_context():
    mail = imaplib.IMAP4_SSL('mail.minipass.me')
    mail.login(get_setting('MAIL_USERNAME'), get_setting('MAIL_PASSWORD'))
    mail.select('INBOX')

    # Count before
    typ, data = mail.search(None, 'FROM', 'notify@payments.interac.ca')
    before = len(data[0].split()) if data[0] else 0
    print(f'\n📊 BEFORE: {before} emails in INBOX')

    if before == 0:
        print("❌ No test emails available")
        mail.logout()
        exit(1)

    # Get first email UID
    typ, data = mail.fetch('1', '(UID)')
    uid = data[0].decode().split()[2].replace(')', '')
    print(f'🎯 Testing with UID: {uid}')

    print('\n🧪 METHOD: COPY + STORE(Deleted) + EXPUNGE')
    mail.uid('COPY', uid, 'PaymentProcessed')
    mail.uid('STORE', uid, '+FLAGS', '(\\Deleted)')
    result = mail.expunge()
    print(f'   Expunge result: {result}')

    # Count after
    typ, data = mail.search(None, 'FROM', 'notify@payments.interac.ca')
    after = len(data[0].split()) if data[0] else 0
    print(f'\n📊 AFTER: {after} emails in INBOX')
    print(f'✅ SUCCESS: Deleted {before - after} email(s)' if after < before else '❌ FAILED: Email still in inbox')

    mail.logout()
