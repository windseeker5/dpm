#!/usr/bin/env python3
"""
Email Recovery & Debug Script for Payment Bot

This script helps debug and recover emails related to payment bot operations.
It can search for emails, move them between folders, list folder structure,
and test archive operations.

Usage:
    # Find an email
    python debug_email_recovery.py --search "Jean Martin Morin" --amount 80

    # List all folders
    python debug_email_recovery.py --list-folders

    # Restore email from folder to Inbox
    python debug_email_recovery.py --restore --uid 71 --from-folder "Trash"

    # Test archive operation
    python debug_email_recovery.py --test-archive --name "Jean Martin Morin" --amount 80
"""

import sys
import os
import imaplib
import email
import argparse
import re
from email.header import decode_header
import unicodedata

# Add app directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_setting(key, default=None):
    """Get setting from database or command line args"""
    # Try to get from global args first (set in main)
    global script_args
    if 'script_args' in globals() and script_args:
        if key == "MAIL_USERNAME" and script_args.username:
            return script_args.username
        elif key == "MAIL_PASSWORD" and script_args.password:
            return script_args.password
        elif key == "IMAP_SERVER" and script_args.imap_server:
            return script_args.imap_server
        elif key == "MAIL_SERVER" and script_args.mail_server:
            return script_args.mail_server
        elif key == "BANK_EMAIL_FROM" and script_args.bank_sender:
            return script_args.bank_sender
        elif key == "GMAIL_LABEL_FOLDER_PROCESSED" and script_args.target_folder:
            return script_args.target_folder

    # Try database as fallback
    try:
        from models import Setting
        from app import app
        with app.app_context():
            setting = Setting.query.filter_by(key=key).first()
            return setting.value if setting else default
    except:
        return default

def normalize_name(text):
    """Normalize name for comparison - handles accents, special chars"""
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', str(text))
    ascii_text = normalized.encode('ASCII', 'ignore').decode('ASCII')
    return ascii_text.lower().strip()

def decode_email_subject(subject):
    """Decode email subject handling various encodings"""
    if not subject:
        return ""

    decoded_parts = decode_header(subject)
    subject_text = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            subject_text += part.decode(encoding or 'utf-8', errors='ignore')
        else:
            subject_text += part
    return subject_text

def connect_to_imap():
    """Connect to IMAP server using settings from database"""
    user = get_setting("MAIL_USERNAME")
    pwd = get_setting("MAIL_PASSWORD")
    imap_server = get_setting("IMAP_SERVER")

    if not user or not pwd:
        print("❌ Error: Email credentials not configured in settings")
        sys.exit(1)

    if not imap_server:
        mail_server = get_setting("MAIL_SERVER")
        imap_server = mail_server if mail_server else "imap.gmail.com"

    print(f"🔌 Connecting to {imap_server} as {user}...")

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
    except:
        try:
            mail = imaplib.IMAP4(imap_server, 143)
            mail.starttls()
        except Exception as e:
            print(f"❌ Error connecting to IMAP server: {e}")
            sys.exit(1)

    try:
        mail.login(user, pwd)
        print("✅ Connected successfully!\n")
        return mail
    except Exception as e:
        print(f"❌ Login failed: {e}")
        sys.exit(1)

def list_folders(mail):
    """List all folders on the email server"""
    print("📂 Listing all folders on server:\n")

    result, folder_list = mail.list()
    if result != 'OK':
        print("❌ Failed to retrieve folder list")
        return

    print(f"{'Folder Name':<30} | Attributes")
    print("-" * 60)

    for folder_info in folder_list:
        if folder_info:
            folder_str = folder_info.decode() if isinstance(folder_info, bytes) else folder_info
            print(f"  {folder_str}")

    print()

def search_email(mail, search_name=None, search_amount=None):
    """Search for email across all folders"""
    print(f"🔍 Searching for email:")
    if search_name:
        print(f"   Name: {search_name}")
    if search_amount:
        print(f"   Amount: ${search_amount}")
    print()

    # Get list of folders
    result, folder_list = mail.list()
    if result != 'OK':
        print("❌ Failed to retrieve folder list")
        return

    found_emails = []

    for folder_info in folder_list:
        if not folder_info:
            continue

        folder_str = folder_info.decode() if isinstance(folder_info, bytes) else folder_info
        # Extract folder name (format: (\HasNoChildren) "." "INBOX")
        match = re.search(r'"([^"]+)"$', folder_str)
        if not match:
            match = re.search(r'\s+(\S+)$', folder_str)

        if not match:
            continue

        folder_name = match.group(1)

        try:
            status, _ = mail.select(folder_name, readonly=True)
            if status != 'OK':
                continue

            # Search all emails in folder
            status, data = mail.search(None, 'ALL')
            if status != 'OK' or not data[0]:
                continue

            email_ids = data[0].split()
            print(f"📂 Checking folder: {folder_name}... {len(email_ids)} emails")

            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = decode_email_subject(msg.get("Subject", ""))
                date = msg.get("Date", "")

                # Extract name and amount from subject
                amount_match = re.search(r"reçu\s+([\d,\s]+)\s+\$\s+de", subject)
                name_match = re.search(r"de\s+(.+?)\s+et ce montant", subject)

                if not amount_match:
                    amount_match = re.search(r"envoyé\s+([\d,\s]+)\s*\$", subject)
                if not name_match:
                    name_match = re.search(r":\s*(.*?)\svous a envoyé", subject)

                # Check if matches search criteria
                matches = True
                if search_name and name_match:
                    extracted_name = name_match.group(1).strip()
                    if normalize_name(search_name) not in normalize_name(extracted_name):
                        matches = False

                if search_amount and amount_match:
                    amt_str = amount_match.group(1).replace(" ", "").replace(",", ".")
                    try:
                        extracted_amt = float(amt_str)
                        if abs(extracted_amt - float(search_amount)) > 0.01:
                            matches = False
                    except:
                        matches = False

                if matches and (name_match or amount_match):
                    found_emails.append({
                        'folder': folder_name,
                        'uid': email_id.decode(),
                        'subject': subject,
                        'date': date,
                        'name': name_match.group(1).strip() if name_match else "Unknown",
                        'amount': amount_match.group(1) if amount_match else "Unknown"
                    })

        except Exception as e:
            print(f"   ⚠️  Error checking {folder_name}: {e}")
            continue

    print()

    if not found_emails:
        print("❌ No matching emails found")
        return None

    print(f"✅ Found {len(found_emails)} matching email(s):\n")

    for idx, email_info in enumerate(found_emails, 1):
        print(f"[{idx}] 📧 Email in folder: {email_info['folder']}")
        print(f"    UID: {email_info['uid']}")
        print(f"    Name: {email_info['name']}")
        print(f"    Amount: {email_info['amount']}")
        print(f"    Subject: {email_info['subject'][:80]}...")
        print(f"    Date: {email_info['date']}")
        print()

    return found_emails

def restore_email(mail, uid, from_folder, to_folder="INBOX"):
    """Move email from one folder to another"""
    print(f"🔄 Restoring email:")
    print(f"   UID: {uid}")
    print(f"   From: {from_folder}")
    print(f"   To: {to_folder}")
    print()

    try:
        # Select source folder
        status, _ = mail.select(from_folder)
        if status != 'OK':
            print(f"❌ Failed to select folder: {from_folder}")
            return False

        # Copy to destination folder
        print(f"📋 Copying email to {to_folder}...")
        copy_result = mail.uid("COPY", uid, to_folder)

        if copy_result[0] != 'OK':
            print(f"❌ Failed to copy email: {copy_result}")
            return False

        print("✅ Copy successful!")

        # Delete from source folder
        print(f"🗑️  Deleting from {from_folder}...")
        mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
        mail.expunge()

        print("✅ Email restored successfully!")
        return True

    except Exception as e:
        print(f"❌ Error restoring email: {e}")
        return False

def test_archive(mail, name, amount):
    """Test the archive operation (simulate what Archive button does)"""
    print(f"🧪 Testing archive operation for:")
    print(f"   Name: {name}")
    print(f"   Amount: ${amount}")
    print()

    # Get folder settings
    processed_folder = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "PaymentProcessed")
    print(f"📁 Target folder from settings: {processed_folder}")
    print()

    # Check if folder exists
    print("🔍 Checking if target folder exists...")
    result, folder_list = mail.list()
    folder_exists = False

    if result == 'OK':
        for folder_info in folder_list:
            if folder_info:
                folder_str = folder_info.decode() if isinstance(folder_info, bytes) else folder_info
                if processed_folder in folder_str:
                    folder_exists = True
                    print(f"✅ Folder exists: {processed_folder}")
                    break

    if not folder_exists:
        print(f"⚠️  Folder does NOT exist: {processed_folder}")
        print(f"   Attempting to create it...")
        try:
            mail.create(processed_folder)
            print(f"✅ Folder created successfully!")
        except Exception as e:
            print(f"❌ Failed to create folder: {e}")
            return False

    print()

    # Search for email in INBOX
    print("🔍 Searching for email in INBOX...")
    status, _ = mail.select("INBOX")
    if status != 'OK':
        print("❌ Failed to select INBOX")
        return False

    from_email = get_setting("BANK_EMAIL_FROM", "notify@payments.interac.ca")
    print(f"   Sender: {from_email}")

    status, data = mail.search(None, f'FROM "{from_email}"')
    if status != 'OK' or not data[0]:
        print("❌ No emails found from sender")
        return False

    email_ids = data[0].split()
    print(f"   Found {len(email_ids)} emails from sender")
    print()

    # Find matching email
    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        if status != 'OK':
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        subject = decode_email_subject(msg.get("Subject", ""))

        # Parse subject
        amount_match = re.search(r"reçu\s+([\d,\s]+)\s+\$\s+de", subject)
        name_match = re.search(r"de\s+(.+?)\s+et ce montant", subject)

        if amount_match and name_match:
            extracted_name = name_match.group(1).strip()
            amt_str = amount_match.group(1).replace(" ", "").replace(",", ".")

            try:
                extracted_amt = float(amt_str)

                # Check if matches
                if (normalize_name(name) == normalize_name(extracted_name) and
                    abs(extracted_amt - float(amount)) < 0.01):

                    print(f"✅ Found matching email!")
                    print(f"   UID: {email_id.decode()}")
                    print(f"   Subject: {subject[:80]}...")
                    print()

                    # Test copy operation
                    print(f"🧪 Testing COPY to {processed_folder}...")
                    copy_result = mail.uid("COPY", email_id, processed_folder)

                    if copy_result[0] == 'OK':
                        print(f"✅ COPY command successful!")
                        print(f"   Result: {copy_result}")
                        print()
                        print("⚠️  NOTE: Email was COPIED (not moved) for testing purposes.")
                        print(f"   The email is now in both INBOX and {processed_folder}.")
                        print(f"   In production, it would be deleted from INBOX after copy.")
                        return True
                    else:
                        print(f"❌ COPY command failed!")
                        print(f"   Result: {copy_result}")
                        return False
            except:
                continue

    print("❌ No matching email found in INBOX")
    return False

def main():
    parser = argparse.ArgumentParser(
        description="Email Recovery & Debug Tool for Payment Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find an email (with credentials)
  %(prog)s --username "email@example.com" --password "pass" --imap-server "mail.example.com" \\
           --search "Jean Martin Morin" --amount 80

  # List all folders
  %(prog)s --username "email@example.com" --password "pass" --imap-server "mail.example.com" \\
           --list-folders

  # Restore email
  %(prog)s --username "email@example.com" --password "pass" --imap-server "mail.example.com" \\
           --restore --uid 71 --from-folder "Trash"

  # Test archive operation
  %(prog)s --username "email@example.com" --password "pass" --imap-server "mail.example.com" \\
           --test-archive --name "Jean Martin Morin" --amount 80
        """
    )

    # Credentials
    parser.add_argument('--username', type=str,
                        help='Email username/address')
    parser.add_argument('--password', type=str,
                        help='Email password')
    parser.add_argument('--imap-server', type=str,
                        help='IMAP server address (e.g., mail.example.com)')
    parser.add_argument('--mail-server', type=str,
                        help='Mail server (fallback for IMAP server)')
    parser.add_argument('--bank-sender', type=str, default='notify@payments.interac.ca',
                        help='Email sender for payment notifications')
    parser.add_argument('--target-folder', type=str, default='PaymentProcessed',
                        help='Target folder for archiving (default: PaymentProcessed)')

    # Operations
    parser.add_argument('--list-folders', action='store_true',
                        help='List all folders on email server')
    parser.add_argument('--search', type=str,
                        help='Search for emails by name')
    parser.add_argument('--amount', type=float,
                        help='Filter search by amount')
    parser.add_argument('--restore', action='store_true',
                        help='Restore email to INBOX')
    parser.add_argument('--uid', type=str,
                        help='Email UID for restore operation')
    parser.add_argument('--from-folder', type=str,
                        help='Source folder for restore operation')
    parser.add_argument('--test-archive', action='store_true',
                        help='Test archive operation (simulate Archive button)')
    parser.add_argument('--name', type=str,
                        help='Name for test-archive operation')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompts')

    args = parser.parse_args()

    # Make args globally available for get_setting function
    global script_args
    script_args = args

    # Connect to IMAP
    mail = connect_to_imap()

    try:
        if args.list_folders:
            list_folders(mail)

        elif args.search:
            found = search_email(mail, args.search, args.amount)
            if found and len(found) == 1:
                print("💡 To restore this email, run:")
                print(f"   python {sys.argv[0]} --restore --uid {found[0]['uid']} --from-folder \"{found[0]['folder']}\"")
                print()

        elif args.restore:
            if not args.uid or not args.from_folder:
                print("❌ Error: --restore requires both --uid and --from-folder")
                sys.exit(1)

            if args.yes:
                restore_email(mail, args.uid, args.from_folder)
            else:
                confirm = input(f"⚠️  Restore email UID {args.uid} from {args.from_folder} to INBOX? (y/n): ")
                if confirm.lower() == 'y':
                    restore_email(mail, args.uid, args.from_folder)
                else:
                    print("❌ Cancelled")

        elif args.test_archive:
            if not args.name or not args.amount:
                print("❌ Error: --test-archive requires both --name and --amount")
                sys.exit(1)

            test_archive(mail, args.name, args.amount)

        else:
            parser.print_help()

    finally:
        mail.logout()
        print("\n👋 Disconnected from email server")

if __name__ == "__main__":
    main()
