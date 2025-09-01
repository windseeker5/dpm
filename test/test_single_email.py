#!/usr/bin/env python3
"""
Simple Single Email Test - Tests compiled template with images
Sends ONE email to kdresdell@gmail.com to verify inline images are working
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils import send_email_async
from datetime import datetime

def test_single_email():
    """Send one test email with compiled template and images"""
    try:
        with app.app_context():
            print("📧 Sending ONE test email with compiled template...")
            print("🎯 Template: signup (compiled version with images)")
            print("📬 To: kdresdell@gmail.com")
            
            # Use signup template which has compiled version with images
            send_email_async(
                app=app,
                subject=f"✅ Image Fix Test - {datetime.now().strftime('%H:%M:%S')}",
                to_email="kdresdell@gmail.com",
                template_name="signup",  # This should resolve to signup_compiled
                context={
                    'title': 'Image Loading Test',
                    'intro_text': 'This email should now show images properly (QR codes, logos, hero images).',
                    'conclusion_text': 'If you see images above, the inline_images.json loading fix worked!'
                }
            )
            
            print("✅ Email sent successfully!")
            print("📧 Check your inbox at kdresdell@gmail.com")
            print("🔍 Look for: Hero images, QR codes, logos properly displayed")
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    test_single_email()