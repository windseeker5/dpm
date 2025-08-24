#!/usr/bin/env python3
"""
Debug script to test IMAP connection with various configurations
"""

import imaplib
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_setting
from app import app

def test_imap_connection():
    """Test IMAP connection with current settings"""
    
    with app.app_context():
        # Get settings
        mail_username = get_setting("MAIL_USERNAME")
        mail_password = get_setting("MAIL_PASSWORD")
        mail_server = get_setting("MAIL_SERVER")
        mail_port = get_setting("MAIL_PORT", "587")  # This is SMTP port
        
        print("=" * 60)
        print("EMAIL SETTINGS DEBUG")
        print("=" * 60)
        print(f"Username: {mail_username}")
        print(f"Password: {'*' * len(mail_password) if mail_password else 'NOT SET'}")
        print(f"Mail Server (SMTP): {mail_server}")
        print(f"Mail Port (SMTP): {mail_port}")
        print()
        
        # Common IMAP ports
        imap_ports = {
            'SSL': 993,
            'TLS': 143
        }
        
        # Try to determine IMAP server from SMTP server
        if mail_server:
            # Common conversions
            if 'smtp' in mail_server.lower():
                imap_server = mail_server.lower().replace('smtp', 'imap')
            elif 'mail' in mail_server.lower():
                imap_server = mail_server  # Often mail.domain.com works for both
            else:
                imap_server = f"imap.{mail_server.split('.')[-2]}.{mail_server.split('.')[-1]}"
        else:
            imap_server = "imap.gmail.com"  # Current hardcoded default
            
        print("=" * 60)
        print("IMAP CONNECTION TESTS")
        print("=" * 60)
        
        # Test 1: Try hardcoded Gmail
        print("\n1. Testing hardcoded Gmail IMAP (current code):")
        print(f"   Server: imap.gmail.com:993 (SSL)")
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(mail_username, mail_password)
            mail.select("inbox")
            print("   ✅ SUCCESS - Connected to Gmail")
            mail.logout()
        except Exception as e:
            print(f"   ❌ FAILED - {str(e)}")
            
        # Test 2: Try with guessed IMAP server (SSL)
        print(f"\n2. Testing {imap_server}:993 (SSL):")
        try:
            mail = imaplib.IMAP4_SSL(imap_server, 993)
            mail.login(mail_username, mail_password)
            mail.select("inbox")
            print(f"   ✅ SUCCESS - Connected to {imap_server}")
            
            # Get inbox info
            result, data = mail.search(None, "ALL")
            if result == 'OK':
                email_ids = data[0].split()
                print(f"   📧 Found {len(email_ids)} emails in inbox")
            
            mail.logout()
        except Exception as e:
            print(f"   ❌ FAILED - {str(e)}")
            
        # Test 3: Try with TLS
        print(f"\n3. Testing {imap_server}:143 (TLS):")
        try:
            mail = imaplib.IMAP4(imap_server, 143)
            mail.starttls()
            mail.login(mail_username, mail_password)
            mail.select("inbox")
            print(f"   ✅ SUCCESS - Connected to {imap_server} with TLS")
            mail.logout()
        except Exception as e:
            print(f"   ❌ FAILED - {str(e)}")
            
        # Test 4: Try without encryption (not recommended)
        print(f"\n4. Testing {imap_server}:143 (Plain):")
        try:
            mail = imaplib.IMAP4(imap_server, 143)
            mail.login(mail_username, mail_password)
            mail.select("inbox")
            print(f"   ✅ SUCCESS - Connected to {imap_server} (INSECURE)")
            mail.logout()
        except Exception as e:
            print(f"   ❌ FAILED - {str(e)}")
            
        # Test 5: Try common mail server as IMAP
        if mail_server and mail_server != imap_server:
            print(f"\n5. Testing {mail_server}:993 (using SMTP server as IMAP):")
            try:
                mail = imaplib.IMAP4_SSL(mail_server, 993)
                mail.login(mail_username, mail_password)
                mail.select("inbox")
                print(f"   ✅ SUCCESS - Connected to {mail_server}")
                mail.logout()
            except Exception as e:
                print(f"   ❌ FAILED - {str(e)}")
        
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
        print("\nBased on the tests above:")
        print("1. Check which test succeeded (if any)")
        print("2. Update the code in utils.py line 633 to use the correct server")
        print("3. Consider adding IMAP_SERVER and IMAP_PORT settings")
        print("\nFor Gmail users:")
        print("- Ensure 2-factor authentication is enabled")
        print("- Use an App Password (not regular password)")
        print("- Enable 'Less secure app access' if using regular password")
        print("\nFor custom mail servers:")
        print("- Contact your mail provider for IMAP settings")
        print("- Common IMAP ports: 993 (SSL), 143 (TLS/Plain)")

if __name__ == "__main__":
    test_imap_connection()