#!/usr/bin/env python3
"""
Send simple test email with clean subject
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils import send_email
from datetime import datetime

with app.app_context():
    print("Sending simple test email...")
    
    # Send with very simple subject and content to avoid spam filters
    send_email(
        subject="Test Email from Minipass",
        to_email="kdresdell@gmail.com",
        html_body="""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Test Email</h2>
            <p>This is a test email from your Minipass application.</p>
            <p>Time sent: {}</p>
            <p>If you receive this, your email system is working.</p>
            <hr>
            <p><small>Sent from mail.minipass.me</small></p>
        </body>
        </html>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    
    print("✅ Email sent! Check ALL folders in Gmail:")
    print("   - Primary inbox")
    print("   - Spam folder")  
    print("   - All Mail")
    print("   - Promotions tab")
    print("   - Social tab")