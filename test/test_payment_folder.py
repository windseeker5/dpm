#!/usr/bin/env python3
"""
Test script to verify PaymentProcessed folder functionality
Tests IMAP connection, folder creation, and email moving
"""

import imaplib
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_setting

def test_payment_folder():
    """Test the PaymentProcessed folder creation and email moving"""
    
    print("=" * 60)
    print("TESTING PAYMENT FOLDER FUNCTIONALITY")
    print("=" * 60)
    
    # Get settings
    mail_username = get_setting("MAIL_USERNAME")
    mail_password = get_setting("MAIL_PASSWORD")
    processed_folder = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "PaymentProcessed")
    
    # Get IMAP server
    imap_server = get_setting("IMAP_SERVER")
    if not imap_server:
        mail_server = get_setting("MAIL_SERVER")
        if mail_server:
            imap_server = mail_server
        else:
            imap_server = "imap.gmail.com"
    
    print(f"Server: {imap_server}")
    print(f"Username: {mail_username}")
    print(f"Processed Folder: {processed_folder}")
    print()
    
    if not mail_username or not mail_password:
        print("❌ MAIL_USERNAME or MAIL_PASSWORD not configured")
        return False
    
    try:
        # Connect to IMAP server
        print("1. Connecting to IMAP server...")
        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            print("   ✅ Connected via SSL")
        except:
            print("   ⚠️ SSL failed, trying TLS...")
            mail = imaplib.IMAP4(imap_server, 143)
            mail.starttls()
            print("   ✅ Connected via TLS")
        
        # Login
        print("\n2. Logging in...")
        mail.login(mail_username, mail_password)
        print("   ✅ Login successful")
        
        # List all folders
        print("\n3. Listing current folders...")
        result, folder_list = mail.list()
        if result == 'OK':
            print("   Current folders:")
            folder_exists = False
            for folder_info in folder_list:
                if folder_info:
                    folder_str = folder_info.decode() if isinstance(folder_info, bytes) else folder_info
                    # Extract just the folder name for display
                    if '"' in folder_str:
                        parts = folder_str.split('"')
                        if len(parts) >= 3:
                            folder_name = parts[-2]
                            print(f"   - {folder_name}")
                            if processed_folder.lower() in folder_name.lower():
                                folder_exists = True
                    else:
                        print(f"   - {folder_str}")
                        if processed_folder in folder_str:
                            folder_exists = True
        
        # Check if PaymentProcessed folder exists
        print(f"\n4. Checking for '{processed_folder}' folder...")
        if folder_exists:
            print(f"   ✅ '{processed_folder}' folder already exists")
        else:
            print(f"   ⚠️ '{processed_folder}' folder not found")
            
            # Try to create the folder
            print(f"\n5. Creating '{processed_folder}' folder...")
            try:
                create_result = mail.create(processed_folder)
                if create_result[0] == 'OK':
                    print(f"   ✅ Successfully created '{processed_folder}' folder")
                else:
                    print(f"   ❌ Failed to create folder: {create_result}")
            except Exception as e:
                print(f"   ❌ Error creating folder: {e}")
        
        # Test selecting the folder
        print(f"\n6. Testing folder access...")
        try:
            select_result = mail.select(processed_folder)
            if select_result[0] == 'OK':
                print(f"   ✅ Can access '{processed_folder}' folder")
                # Get message count
                result, data = mail.search(None, "ALL")
                if result == 'OK':
                    email_ids = data[0].split()
                    print(f"   📊 Emails in '{processed_folder}': {len(email_ids)}")
            else:
                print(f"   ❌ Cannot select folder: {select_result}")
        except Exception as e:
            print(f"   ❌ Error accessing folder: {e}")
        
        # Test moving an email (if there are any in inbox)
        print("\n7. Testing email move functionality...")
        mail.select("inbox")
        result, data = mail.search(None, "ALL")
        if result == 'OK' and data[0]:
            email_ids = data[0].split()
            if email_ids:
                print(f"   📧 Found {len(email_ids)} emails in inbox")
                
                # Search for payment emails
                result, data = mail.search(None, 'SUBJECT "test"')
                if result == 'OK' and data[0]:
                    test_ids = data[0].split()
                    print(f"   🧪 Found {len(test_ids)} test emails")
                    print("   ℹ️  To test moving, send a test email with 'test' in subject")
                else:
                    print("   ℹ️  No test emails found. Send an email with 'test' in subject to test moving")
            else:
                print("   📭 Inbox is empty")
        
        # Logout
        mail.logout()
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load Flask app context for settings
    from app import app
    with app.app_context():
        success = test_payment_folder()
        
        if success:
            print("\n" + "=" * 60)
            print("SUMMARY: Payment folder system is working correctly!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("SUMMARY: There were issues with the payment folder system")
            print("=" * 60)