#!/usr/bin/env python3
"""
Check real Interac emails in 'payment processes' folder for Reply-To headers
"""
import imaplib
import email
import sys

# Email credentials
MAIL_SERVER = "mail.minipass.me"
MAIL_USERNAME = "lhgi@minipass.me"
MAIL_PASSWORD = "monsterinc00"

def check_interac_headers():
    """Connect to mailbox and check Reply-To headers in payment emails"""

    print(f"🔌 Connecting to {MAIL_SERVER}...")

    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(MAIL_SERVER)
        mail.login(MAIL_USERNAME, MAIL_PASSWORD)
        print(f"✅ Logged in successfully as {MAIL_USERNAME}")

        # List all folders
        print(f"\n📂 Available folders:")
        status, folders = mail.list()
        for folder in folders:
            print(f"   {folder.decode()}")

        # Select 'PaymentProcessed' folder
        print(f"\n📂 Selecting 'PaymentProcessed' folder...")
        status, messages = mail.select('PaymentProcessed')
        if status != 'OK':
            # Try alternate name
            status, messages = mail.select('payment-processes')
        if status != 'OK':
            print(f"❌ Could not select folder. Status: {status}")
            return

        total_emails = int(messages[0].decode())
        print(f"✅ Found {total_emails} emails in folder")

        # Check last 5 emails
        check_count = min(5, total_emails)
        print(f"\n🔍 Checking last {check_count} emails for Reply-To headers:\n")

        for i in range(total_emails, max(total_emails - check_count, 0), -1):
            status, msg_data = mail.fetch(str(i).encode(), '(RFC822)')
            if status != 'OK':
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extract key headers
            from_addr = email.utils.parseaddr(msg.get("From", ""))[1]
            reply_to = msg.get("Reply-To")
            subject = msg.get("Subject", "")[:60]
            date = msg.get("Date", "")

            print(f"{'='*70}")
            print(f"Email #{i}:")
            print(f"  Date: {date}")
            print(f"  From: {from_addr}")
            print(f"  Subject: {subject}...")
            print(f"  Reply-To: {reply_to if reply_to else '❌ NOT PRESENT'}")

            if reply_to:
                parsed_reply = email.utils.parseaddr(reply_to)[1]
                print(f"  → Parsed Reply-To: {parsed_reply}")
            print()

        mail.close()
        mail.logout()
        print(f"\n✅ Done!")

    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_interac_headers()
