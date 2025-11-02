#!/usr/bin/env python3
"""
Manual Payment Bot Test Script
Run this to manually trigger the payment bot and see detailed logs
"""

from app import app
from utils import match_gmail_payments_to_passes

print("="*80)
print("PAYMENT BOT MANUAL TEST")
print("="*80)
print("\nThis will process payment emails from your inbox.")
print("Watch the logs carefully for:")
print("  - 🎯 MATCH FOUND messages")
print("  - 🔍 PRE/POST-COMMIT STATE")
print("  - ❌ BUG DETECTED messages")
print("  - Any exceptions or errors")
print("\n" + "="*80 + "\n")

with app.app_context():
    try:
        match_gmail_payments_to_passes()
        print("\n" + "="*80)
        print("✅ Payment bot completed successfully")
        print("="*80)
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ Payment bot failed with error: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
