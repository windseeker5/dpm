#!/usr/bin/env python3
"""
Subscribe to ManualProcessed folder so NeoMutt can see it
"""

import imaplib

username = "lhgi@minipass.me"
password = "monsterinc00"
imap_server = "mail.minipass.me"

print(f"🔌 Connecting to {imap_server}...")
mail = imaplib.IMAP4_SSL(imap_server)
mail.login(username, password)
print("✅ Connected!\n")

folder_name = "ManualProcessed"

print(f"📬 Subscribing to '{folder_name}'...")
try:
    status, data = mail.subscribe(folder_name)
    if status == 'OK':
        print(f"✅ Successfully subscribed to '{folder_name}'")
    else:
        print(f"❌ Failed to subscribe: {status} - {data}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n📋 Checking subscribed folders now:")
result, subscribed = mail.lsub()
if result == 'OK':
    for folder_info in subscribed:
        if folder_info:
            print(f"  {folder_info.decode() if isinstance(folder_info, bytes) else folder_info}")

mail.logout()
print("\n✅ Done! Try refreshing NeoMutt now (press 'c' then '?' to see folder list)")
