#!/usr/bin/env python3
"""
Simple Email Test Runner
Run this script to test your email functionality and send test emails to kdresdell@gmail.com
"""

import subprocess
import sys
import os

def run_email_test():
    """Run the email functionality test"""
    print("🚀 Starting Email Functionality Test...")
    print("📧 Will send test emails to kdresdell@gmail.com")
    print("-" * 50)
    
    # Change to the app directory
    os.chdir('/home/kdresdell/Documents/DEV/minipass_env/app')
    
    try:
        # Run the test script
        result = subprocess.run([
            sys.executable, 'test/test_email_functionality.py'
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Email test completed successfully!")
        else:
            print(f"\n⚠️  Email test completed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running email test: {e}")

if __name__ == "__main__":
    run_email_test()