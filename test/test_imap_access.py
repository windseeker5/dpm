#!/usr/bin/env python3
"""
Test IMAP access for lhgi@minipass.me
"""

import imaplib
import email
from datetime import datetime

def test_email_connection():
    """Test connection to mail.minipass.me with provided credentials"""
    
    # Credentials
    username = "lhgi@minipass.me"
    password = "monsterinc00"
    server = "mail.minipass.me"
    
    print("=" * 60)
    print("TESTING EMAIL CONNECTION")
    print("=" * 60)
    print(f"Server: {server}")
    print(f"Username: {username}")
    print()
    
    results = []
    
    # Test 1: SSL Connection (port 993)
    print("1. Testing SSL connection (port 993)...")
    try:
        mail = imaplib.IMAP4_SSL(server, 993)
        mail.login(username, password)
        print("   ✅ SSL connection successful!")
        
        # Select inbox
        result, data = mail.select("inbox")
        if result == 'OK':
            print(f"   📧 Connected to INBOX")
            
            # Get message count
            result, data = mail.search(None, "ALL")
            if result == 'OK':
                email_ids = data[0].split()
                print(f"   📊 Total emails in inbox: {len(email_ids)}")
                
                # Show last 5 emails (if any)
                if email_ids:
                    print("\n   Recent emails (last 5):")
                    for email_id in email_ids[-5:]:
                        try:
                            result, msg_data = mail.fetch(email_id, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
                            if result == 'OK':
                                raw_header = msg_data[0][1].decode('utf-8', errors='ignore')
                                print(f"   - {raw_header[:100].strip()}...")
                        except Exception as e:
                            print(f"   Error reading email {email_id}: {e}")
                            
            # Search for Interac emails
            print("\n   Searching for payment emails...")
            result, data = mail.search(None, 'SUBJECT "Interac"')
            if result == 'OK':
                interac_ids = data[0].split()
                print(f"   💰 Found {len(interac_ids)} emails with 'Interac' in subject")
                
            result, data = mail.search(None, 'SUBJECT "Virement"')
            if result == 'OK':
                virement_ids = data[0].split()
                print(f"   💰 Found {len(virement_ids)} emails with 'Virement' in subject")
        
        mail.logout()
        results.append("SSL: SUCCESS")
        
    except Exception as e:
        print(f"   ❌ SSL connection failed: {e}")
        results.append(f"SSL: FAILED - {e}")
        
        # Test 2: TLS Connection (port 143)
        print("\n2. Testing TLS connection (port 143)...")
        try:
            mail = imaplib.IMAP4(server, 143)
            mail.starttls()
            mail.login(username, password)
            print("   ✅ TLS connection successful!")
            
            # Select inbox
            result, data = mail.select("inbox")
            if result == 'OK':
                print(f"   📧 Connected to INBOX")
                
                # Get message count
                result, data = mail.search(None, "ALL")
                if result == 'OK':
                    email_ids = data[0].split()
                    print(f"   📊 Total emails in inbox: {len(email_ids)}")
            
            mail.logout()
            results.append("TLS: SUCCESS")
            
        except Exception as e:
            print(f"   ❌ TLS connection failed: {e}")
            results.append(f"TLS: FAILED - {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for result in results:
        print(f"• {result}")
    
    print("\nIMPLICATIONS FOR YOUR APP:")
    if "SUCCESS" in str(results):
        print("✅ Email connection works! The bot should be able to read emails.")
        print("   Make sure your app is using the same connection method that worked.")
    else:
        print("❌ Could not connect to email server.")
        print("   Check credentials and server settings.")

if __name__ == "__main__":
    test_email_connection()