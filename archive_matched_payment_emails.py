#!/usr/bin/env python3
"""
Archive Matched Payment Emails Script

This script finds emails in the inbox that correspond to MATCHED payment records
in the database and moves them to the PaymentProcessed folder.

This is needed because the backfill script fixed the database records but didn't
move the emails from the inbox.

Usage:
    python archive_matched_payment_emails.py --dry-run    # See what would be moved
    python archive_matched_payment_emails.py              # Actually move the emails
"""

import sys
import re
import imaplib
import email.header
from app import app, db
from models import EbankPayment
from utils import get_setting

def connect_to_imap():
    """Connect to IMAP server using settings from database"""
    # Get IMAP server from settings
    imap_server = get_setting("IMAP_SERVER")
    if not imap_server:
        mail_server = get_setting("MAIL_SERVER")
        imap_server = mail_server if mail_server else "mail.minipass.me"

    # Get credentials
    user = get_setting("MAIL_USERNAME")
    password = get_setting("MAIL_PASSWORD")

    if not user or not password:
        print("❌ Error: MAIL_USERNAME or MAIL_PASSWORD not configured in settings")
        sys.exit(1)

    print(f"🔌 Connecting to IMAP server: {imap_server}")
    print(f"   User: {user}")

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(user, password)
        print("✅ Connected successfully")
        return mail
    except Exception as e:
        print(f"❌ Error connecting to IMAP server: {e}")
        sys.exit(1)

def find_emails_to_move(mail):
    """Find emails in inbox that match MATCHED payment records"""
    # Get the processed folder name from settings
    processed_folder = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "PaymentProcessed")

    print(f"\n📧 Searching inbox for emails to archive...")
    print(f"   Target folder: {processed_folder}\n")

    # Select inbox
    mail.select("INBOX")

    # Search for payment emails from Interac
    typ, data = mail.search(None, 'FROM', 'notify@payments.interac.ca')
    if typ != 'OK':
        print("❌ Error searching inbox")
        return []

    email_ids = data[0].split()
    print(f"📬 Found {len(email_ids)} Interac payment emails in inbox")

    # Get all MATCHED payment records from database
    matched_records = EbankPayment.query.filter_by(result="MATCHED").all()
    print(f"💾 Found {len(matched_records)} MATCHED records in database\n")

    emails_to_move = []

    print("🔍 Analyzing emails in inbox...\n")

    # For each email, check if it matches a MATCHED record
    for email_id in email_ids:
        # Fetch email subject AND UID
        typ, msg_data = mail.fetch(email_id, '(BODY[HEADER.FIELDS (SUBJECT)] UID)')
        if typ != 'OK':
            continue

        # Extract UID from response
        uid_line = msg_data[0][0].decode() if isinstance(msg_data[0][0], bytes) else str(msg_data[0][0])
        uid_match = re.search(r'UID (\d+)', uid_line)
        uid = uid_match.group(1) if uid_match else None

        if not uid:
            print(f"   ⚠️ Could not extract UID for email {email_id}")
            continue

        # Extract and decode subject (handles MIME encoding like =?UTF-8?Q?...?=)
        subject_data = msg_data[0][1].decode('utf-8', errors='ignore')
        subject_raw = subject_data.replace('Subject: ', '').strip()

        # Decode MIME-encoded subject
        decoded_parts = email.header.decode_header(subject_raw)
        subject = ''
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                subject += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                subject += part

        # Extract name and amount from subject
        # Format: "Virement Interac : Vous avez reçu 50,00 $ de DAVID CASTONGUAY et ce montant..."
        match = re.search(r'reçu ([\d,]+) \$ de (.+?) et ce', subject, re.IGNORECASE)
        if not match:
            print(f"   ⚠️ Could not parse subject: {subject[:60]}...")
            continue

        amount_str = match.group(1).replace(',', '.')
        name = match.group(2).strip()

        try:
            amount = float(amount_str)
        except:
            print(f"   ⚠️ Could not parse amount from: {amount_str}")
            continue

        print(f"   📧 Email: {name} - ${amount}")

        # Check if this matches any MATCHED record
        found_match = False
        for record in matched_records:
            # Match by name and amount
            if (record.bank_info_name and
                record.bank_info_name.upper() == name.upper() and
                abs(record.bank_info_amt - amount) < 0.01):

                print(f"      ✅ MATCHED to DB record #{record.id} (Passport #{record.matched_pass_id})")
                emails_to_move.append({
                    'uid': uid,  # Store UID, not sequence number
                    'subject': subject[:80] + '...',
                    'name': name,
                    'amount': amount,
                    'record_id': record.id,
                    'matched_passport_id': record.matched_pass_id
                })
                found_match = True
                break

        if not found_match:
            print(f"      ❌ No matching MATCHED record in database")

    return emails_to_move, processed_folder

def move_emails(mail, emails_to_move, processed_folder, dry_run=False):
    """Move emails to the processed folder"""
    if not emails_to_move:
        print("ℹ️  No emails to move")
        return

    print(f"\n{'='*80}")
    if dry_run:
        print(f"DRY RUN - These emails WOULD be moved to {processed_folder}:")
    else:
        print(f"Moving {len(emails_to_move)} emails to {processed_folder}:")
    print(f"{'='*80}\n")

    for i, email in enumerate(emails_to_move, 1):
        print(f"{i}. {email['name']} - ${email['amount']}")
        print(f"   Subject: {email['subject']}")
        print(f"   Passport ID: {email['matched_passport_id']}")
        print(f"   DB Record ID: {email['record_id']}")

        if not dry_run:
            try:
                # Check if folder exists, create if needed
                if i == 1:  # Only check once
                    folder_exists = False
                    result, folder_list = mail.list()
                    if result == 'OK':
                        for folder_info in folder_list:
                            if folder_info:
                                folder_str = folder_info.decode() if isinstance(folder_info, bytes) else folder_info
                                if processed_folder in folder_str:
                                    folder_exists = True
                                    break

                    if not folder_exists:
                        print(f"\n📁 Creating folder: {processed_folder}")
                        try:
                            mail.create(processed_folder)
                            print(f"✅ Folder created")
                        except Exception as e:
                            print(f"⚠️  Could not create folder: {e}")

                # MOVE command doesn't work properly on this server
                # Use COPY + DELETE + EXPUNGE instead (same as application code)
                copy_result = mail.uid("COPY", email['uid'], processed_folder)
                if copy_result[0] == 'OK':
                    # Mark for deletion
                    mail.uid("STORE", email['uid'], "+FLAGS", "(\\Deleted)")
                    # CRITICAL: Expunge IMMEDIATELY after marking (like application does)
                    mail.expunge()
                    print(f"   ✅ Moved to {processed_folder} (UID {email['uid']})")
                else:
                    print(f"   ❌ Failed to copy: {copy_result}")
            except Exception as e:
                print(f"   ❌ Error: {e}")

        print()

    if not dry_run:
        print(f"\n✅ All emails moved successfully!")
        # Note: Expunge is called after each email (see above)

def main():
    dry_run = '--dry-run' in sys.argv

    print("="*80)
    print("ARCHIVE MATCHED PAYMENT EMAILS")
    if dry_run:
        print("MODE: DRY RUN (no emails will be moved)")
    else:
        print("MODE: LIVE (emails will be moved)")
    print("="*80)
    print()

    with app.app_context():
        # Connect to IMAP
        mail = connect_to_imap()

        # Find emails to move
        emails_to_move, processed_folder = find_emails_to_move(mail)

        # Move emails
        move_emails(mail, emails_to_move, processed_folder, dry_run)

        # Disconnect
        mail.logout()
        print(f"\n{'='*80}")
        print("✅ COMPLETE")
        print("="*80)

        if dry_run:
            print("\nTo actually move the emails, run:")
            print("  python archive_matched_payment_emails.py")

if __name__ == "__main__":
    main()
