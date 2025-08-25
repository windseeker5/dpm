#!/usr/bin/env python3
"""
Verify that the payment folder setting is correctly configured to PaymentProcessed
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils import get_setting

def verify_payment_folder():
    """Verify the payment folder configuration"""
    
    print("="*60)
    print("PAYMENT FOLDER CONFIGURATION VERIFICATION")
    print("="*60)
    
    with app.app_context():
        # Check the setting value
        folder_name = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "PaymentProcessed")
        
        print(f"\n✓ Current folder setting: '{folder_name}'")
        
        if folder_name == "PaymentProcessed":
            print("✅ SUCCESS: Email folder is correctly set to 'PaymentProcessed'")
            print("\nEmails will now be moved to the 'PaymentProcessed' folder after payment validation.")
            return True
        elif folder_name == "InteractProcessed":
            print("❌ ERROR: Email folder is still set to old value 'InteractProcessed'")
            print("\nEmails will be moved to the wrong folder!")
            return False
        else:
            print(f"⚠️ WARNING: Unexpected folder name: '{folder_name}'")
            return False
    
    print("\n" + "="*60)

if __name__ == "__main__":
    success = verify_payment_folder()
    sys.exit(0 if success else 1)