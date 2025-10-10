#!/usr/bin/env python3
"""
Check IMAP folder details - subscription status, hierarchy, naming
"""

import imaplib
import sys

username = "lhgi@minipass.me"
password = "monsterinc00"
imap_server = "mail.minipass.me"

print(f"🔌 Connecting to {imap_server}...")
try:
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(username, password)
    print("✅ Connected successfully!\n")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("=" * 70)
print("📂 ALL FOLDERS (using LIST command):")
print("=" * 70)
result, folder_list = mail.list()
if result == 'OK':
    for folder_info in folder_list:
        if folder_info:
            print(folder_info.decode() if isinstance(folder_info, bytes) else folder_info)
print()

print("=" * 70)
print("📬 SUBSCRIBED FOLDERS (using LSUB command):")
print("=" * 70)
result, subscribed = mail.lsub()
if result == 'OK':
    for folder_info in subscribed:
        if folder_info:
            print(folder_info.decode() if isinstance(folder_info, bytes) else folder_info)
else:
    print("❌ LSUB command failed or not supported")
print()

print("=" * 70)
print("🔍 Checking ManualProcessed folder details:")
print("=" * 70)

# Try to select ManualProcessed
try:
    status, data = mail.select('ManualProcessed', readonly=True)
    if status == 'OK':
        print(f"✅ Can SELECT 'ManualProcessed' folder")
        print(f"   Status: {status}")
        print(f"   Data: {data}")

        # Check how many emails
        status, search_data = mail.search(None, 'ALL')
        if status == 'OK' and search_data[0]:
            email_ids = search_data[0].split()
            print(f"   📧 Contains {len(email_ids)} email(s)")
        else:
            print(f"   📧 Folder is empty")
    else:
        print(f"❌ Cannot SELECT 'ManualProcessed'")
        print(f"   Status: {status}")
except Exception as e:
    print(f"❌ Error selecting folder: {e}")

print()

# Try common variations
print("=" * 70)
print("🧪 Testing folder name variations:")
print("=" * 70)

variations = [
    "ManualProcessed",
    "INBOX.ManualProcessed",
    "INBOX/ManualProcessed",
    ".ManualProcessed",
    "manualprocessed",
    "Manual Processed"
]

for folder_name in variations:
    try:
        status, data = mail.select(folder_name, readonly=True)
        if status == 'OK':
            print(f"✅ '{folder_name}' - SUCCESS")
        else:
            print(f"❌ '{folder_name}' - FAILED: {status}")
    except Exception as e:
        print(f"❌ '{folder_name}' - ERROR: {str(e)[:50]}")

print()
print("=" * 70)
print("🔧 IMAP Server Namespace:")
print("=" * 70)
try:
    status, data = mail.namespace()
    if status == 'OK':
        print(f"Namespace: {data}")
    else:
        print("❌ NAMESPACE command not supported")
except:
    print("❌ NAMESPACE command failed")

mail.logout()
print("\n👋 Disconnected")
