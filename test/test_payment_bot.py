#!/usr/bin/env python3
"""
Simple script to test the payment bot manually
Run this directly on the server: python3 test_payment_bot.py
"""

import sys
import os

# Add the app directory to Python path
sys.path.append('/home/kdresdell/minipass_env/app')

def run_payment_bot():
    print("🚀 Starting manual payment bot test...")
    
    try:
        # Import the Flask app and utils
        from app import app
        from utils import match_gmail_payments_to_passes
        
        # Run within app context
        with app.app_context():
            print("📧 Running payment bot...")
            result = match_gmail_payments_to_passes()
            
            if result and isinstance(result, dict):
                print(f"✅ SUCCESS: {result.get('matched', 0)} payments matched!")
                print(f"📊 Details: {result}")
            else:
                print("✅ Payment bot completed - no new payments found.")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("MANUAL PAYMENT BOT TEST")
    print("=" * 60)
    run_payment_bot()
    print("=" * 60)
    print("DONE")