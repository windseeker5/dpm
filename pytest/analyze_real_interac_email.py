#!/usr/bin/env python3
"""
Analyze a real Interac email to find where the sender's email is located.
READ ONLY - Does not move or delete any emails.
"""

import imaplib
import email
import sys
import os

# Add parent directory to path to import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from models import db, Setting
from app import app

def analyze_interac_email():
    """Connect to IMAP and analyze the DARIO COTE email"""

    with app.app_context():
        # Get credentials from database
        mail_username = Setting.query.filter_by(key='MAIL_USERNAME').first()
        mail_password = Setting.query.filter_by(key='MAIL_PASSWORD').first()
        mail_server = Setting.query.filter_by(key='MAIL_SERVER').first()

        if not all([mail_username, mail_password, mail_server]):
            print("❌ Missing email credentials in database")
            return

        print(f"📧 Connecting to {mail_server.value} as {mail_username.value}...")

        try:
            # Connect to IMAP
            imap = imaplib.IMAP4_SSL(mail_server.value)
            imap.login(mail_username.value, mail_password.value)
            print("✅ Connected successfully")

            # Select inbox
            imap.select("INBOX", readonly=True)  # READ-ONLY mode
            print("📬 Opened INBOX (read-only)")

            # Search for DARIO COTE email
            print("\n🔍 Searching for DARIO COTE $120 email...")
            status, messages = imap.search(None, 'SUBJECT "DARIO COTE"')

            if status != 'OK' or not messages[0]:
                print("❌ No emails found with DARIO COTE in subject")
                # Try broader search
                print("\n🔍 Searching for recent Interac emails...")
                status, messages = imap.search(None, 'FROM "notify@payments.interac.ca"')

            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()
                print(f"✅ Found {len(email_ids)} email(s)")

                # Get the most recent one
                latest_email_id = email_ids[-1]
                print(f"\n📨 Fetching email ID: {latest_email_id.decode()}")

                # Fetch the raw email
                status, data = imap.fetch(latest_email_id, '(RFC822)')

                if status == 'OK':
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    print("\n" + "="*70)
                    print("📋 EMAIL ANALYSIS")
                    print("="*70)

                    # Print all headers
                    print("\n🏷️  ALL HEADERS:")
                    print("-"*70)
                    for header, value in msg.items():
                        print(f"{header}: {value}")

                    # Check for Reply-To specifically
                    print("\n🎯 REPLY-TO HEADER:")
                    print("-"*70)
                    reply_to = msg.get("Reply-To")
                    if reply_to:
                        print(f"✅ Found: {reply_to}")
                        parsed = email.utils.parseaddr(reply_to)
                        print(f"   Parsed: {parsed}")
                    else:
                        print("❌ No Reply-To header found")

                    # Extract body
                    print("\n📝 EMAIL BODY:")
                    print("-"*70)
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                                    break
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')

                    print(body[:2000])  # First 2000 chars

                    # Search for email addresses in body
                    print("\n🔍 SEARCHING FOR EMAIL ADDRESSES IN BODY:")
                    print("-"*70)
                    import re
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    found_emails = re.findall(email_pattern, body)
                    if found_emails:
                        print(f"✅ Found {len(found_emails)} email address(es):")
                        for email_addr in found_emails:
                            print(f"   • {email_addr}")
                    else:
                        print("❌ No email addresses found in body")

                    print("\n" + "="*70)
                    print("✅ Analysis complete")
                    print("="*70)

            imap.close()
            imap.logout()
            print("\n✅ Disconnected from mailbox")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    analyze_interac_email()
