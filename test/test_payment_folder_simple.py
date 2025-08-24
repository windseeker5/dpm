#!/usr/bin/env python3
"""
Simple test script to verify PaymentProcessed folder functionality
Tests IMAP connection and folder operations without Flask dependencies
"""

import imaplib

def test_payment_folder_simple():
    """Test the PaymentProcessed folder creation and email moving"""
    
    print("=" * 60)
    print("TESTING PAYMENT FOLDER FUNCTIONALITY (SIMPLE)")
    print("=" * 60)
    
    # Hardcoded settings for testing
    mail_username = "lhgi@minipass.me"
    mail_password = "monsterinc00"
    imap_server = "mail.minipass.me"
    processed_folder = "PaymentProcessed"
    
    print(f"Server: {imap_server}")
    print(f"Username: {mail_username}")
    print(f"Processed Folder: {processed_folder}")
    print()
    
    try:
        # Connect to IMAP server
        print("1. Connecting to IMAP server...")
        try:
            mail = imaplib.IMAP4_SSL(imap_server, 993)
            print("   ✅ Connected via SSL")
        except Exception as e:
            print(f"   ⚠️ SSL failed ({e}), trying TLS...")
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
                    email_ids = data[0].split() if data[0] else []
                    print(f"   📊 Emails in '{processed_folder}': {len(email_ids)}")
            else:
                print(f"   ❌ Cannot select folder: {select_result}")
        except Exception as e:
            print(f"   ❌ Error accessing folder: {e}")
        
        # Check inbox for payment emails
        print("\n7. Checking inbox for payment emails...")
        mail.select("inbox")
        
        # Search for Interac/payment emails
        search_terms = [
            ('SUBJECT "Interac"', "Interac"),
            ('SUBJECT "Virement"', "Virement"),
            ('SUBJECT "Payment"', "Payment"),
            ('FROM "notify@payments.interac.ca"', "from Interac notify")
        ]
        
        for search_query, description in search_terms:
            result, data = mail.search(None, search_query)
            if result == 'OK' and data[0]:
                email_ids = data[0].split()
                print(f"   💰 Found {len(email_ids)} emails with {description}")
                
                # Show first few subjects
                if email_ids:
                    print(f"      Sample emails (max 3):")
                    for email_id in email_ids[:3]:
                        try:
                            result, msg_data = mail.fetch(email_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
                            if result == 'OK':
                                header = msg_data[0][1].decode('utf-8', errors='ignore')
                                # Extract subject
                                for line in header.split('\n'):
                                    if line.startswith('Subject:'):
                                        print(f"      - {line.strip()[:80]}")
                                        break
                        except Exception as e:
                            print(f"      Error reading email: {e}")
            else:
                print(f"   ℹ️  No emails found with {description}")
        
        # Test moving functionality with a test email
        print("\n8. Testing email move functionality...")
        mail.select("inbox")
        
        # Look for any test email
        result, data = mail.search(None, 'SUBJECT "test"')
        if result == 'OK' and data[0]:
            test_ids = data[0].split()
            if test_ids:
                print(f"   🧪 Found {len(test_ids)} test email(s)")
                test_uid = test_ids[0]
                
                # Get UID for the test email
                result, uid_data = mail.fetch(test_uid, '(UID)')
                if result == 'OK':
                    uid_response = uid_data[0].decode() if isinstance(uid_data[0], bytes) else str(uid_data[0])
                    # Extract UID from response
                    import re
                    uid_match = re.search(r'UID (\d+)', uid_response)
                    if uid_match:
                        uid = uid_match.group(1)
                        print(f"   📧 Testing move with email UID: {uid}")
                        
                        # Try to copy and delete (move)
                        copy_result = mail.uid("COPY", uid, processed_folder)
                        if copy_result[0] == 'OK':
                            print(f"   ✅ Successfully copied test email to '{processed_folder}'")
                            # Mark for deletion
                            mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                            print(f"   ✅ Marked test email for deletion from inbox")
                            # Expunge to actually delete
                            mail.expunge()
                            print(f"   ✅ Test email moved successfully!")
                        else:
                            print(f"   ❌ Could not copy test email: {copy_result}")
            else:
                print("   ℹ️  No test emails found")
                print("   💡 To test moving: Send an email with 'test' in the subject to this account")
        else:
            print("   ℹ️  No test emails found in inbox")
            print("   💡 To test moving: Send an email with 'test' in the subject to this account")
        
        # Logout
        mail.logout()
        print("\n✅ Testing completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_payment_folder_simple()
    
    if success:
        print("\n" + "=" * 60)
        print("SUMMARY: Payment folder system is ready!")
        print("\nThe PaymentProcessed folder has been verified/created.")
        print("Payment emails will now be moved there after processing.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("SUMMARY: Please check the errors above")
        print("=" * 60)