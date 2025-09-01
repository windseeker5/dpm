#!/usr/bin/env python3
"""
Debug SMTP Connection - Test why emails aren't being delivered
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_smtp_connection():
    """Test SMTP connection and configuration"""
    
    from app import app
    from utils import get_setting
    
    with app.app_context():
        print("🔍 SMTP Configuration Debug")
        print("=" * 60)
        
        # Get SMTP settings
        smtp_host = get_setting("MAIL_SERVER")
        smtp_port = int(get_setting("MAIL_PORT", 587))
        smtp_user = get_setting("MAIL_USERNAME")
        smtp_pass = get_setting("MAIL_PASSWORD")
        use_tls = str(get_setting("MAIL_USE_TLS") or "true").lower() == "true"
        use_ssl = str(get_setting("MAIL_USE_SSL") or "false").lower() == "true"
        from_email = get_setting("MAIL_DEFAULT_SENDER") or "noreply@minipass.me"
        sender_name = get_setting("MAIL_SENDER_NAME") or "Minipass"
        
        print("📧 Current SMTP Configuration:")
        print(f"   Server: {smtp_host}")
        print(f"   Port: {smtp_port}")
        print(f"   Username: {smtp_user}")
        print(f"   Password: {'*' * len(smtp_pass) if smtp_pass else 'NOT SET'}")
        print(f"   Use TLS: {use_tls}")
        print(f"   Use SSL: {use_ssl}")
        print(f"   From Email: {from_email}")
        print(f"   Sender Name: {sender_name}")
        
        if not smtp_host:
            print("\n❌ ERROR: MAIL_SERVER not configured!")
            print("   Please configure SMTP settings in Settings → Email Configuration")
            return False
            
        if not smtp_user or not smtp_pass:
            print("\n⚠️ WARNING: No SMTP authentication configured")
            print("   This may work for local SMTP servers but not for external services")
        
        print("\n🔌 Testing SMTP Connection...")
        print("-" * 40)
        
        try:
            # Create test message
            msg = MIMEMultipart()
            msg['Subject'] = f"SMTP Debug Test - {datetime.now().strftime('%H:%M:%S')}"
            msg['From'] = f"{sender_name} <{from_email}>"
            msg['To'] = "kdresdell@gmail.com"
            
            body = f"""
            This is a debug test email to verify SMTP configuration.
            
            Test Details:
            - Server: {smtp_host}:{smtp_port}
            - TLS: {use_tls}
            - SSL: {use_ssl}
            - From: {from_email}
            - Time: {datetime.now()}
            
            If you receive this email, your SMTP configuration is working correctly!
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Try to connect and send
            print(f"1. Connecting to {smtp_host}:{smtp_port}...")
            
            if use_ssl:
                print("   Using SSL connection...")
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                print("   Using standard SMTP connection...")
                server = smtplib.SMTP(smtp_host, smtp_port)
            
            server.set_debuglevel(2)  # Enable verbose debug output
            
            print("2. Sending EHLO...")
            server.ehlo()
            
            if use_tls and not use_ssl:
                print("3. Starting TLS...")
                server.starttls()
                server.ehlo()
            
            if smtp_user and smtp_pass:
                print(f"4. Authenticating as {smtp_user}...")
                server.login(smtp_user, smtp_pass)
                print("   ✅ Authentication successful")
            else:
                print("4. No authentication configured")
            
            print("5. Sending email to kdresdell@gmail.com...")
            server.sendmail(from_email, ["kdresdell@gmail.com"], msg.as_string())
            
            print("6. Closing connection...")
            server.quit()
            
            print("\n✅ SUCCESS! Email sent successfully!")
            print("📧 Check your inbox at kdresdell@gmail.com")
            print("   (Also check spam folder)")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"\n❌ AUTHENTICATION ERROR: {e}")
            print("   Check your MAIL_USERNAME and MAIL_PASSWORD settings")
            
        except smtplib.SMTPConnectError as e:
            print(f"\n❌ CONNECTION ERROR: {e}")
            print("   Check your MAIL_SERVER and MAIL_PORT settings")
            print("   Make sure the server is reachable from your network")
            
        except smtplib.SMTPException as e:
            print(f"\n❌ SMTP ERROR: {e}")
            print("   There's an issue with the SMTP configuration")
            
        except Exception as e:
            print(f"\n❌ UNEXPECTED ERROR: {e}")
            import traceback
            print("\nFull traceback:")
            print(traceback.format_exc())
        
        return False

def check_email_logs():
    """Check recent email logs for errors"""
    from app import app
    from models import EmailLog
    
    with app.app_context():
        print("\n📊 Recent Email Logs")
        print("=" * 60)
        
        recent_logs = EmailLog.query.order_by(EmailLog.timestamp.desc()).limit(10).all()
        
        for log in recent_logs:
            status_icon = "✅" if log.result == "SENT" else "❌"
            print(f"{status_icon} {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {log.to_email}")
            print(f"   Subject: {log.subject}")
            print(f"   Result: {log.result}")
            if log.error_message:
                print(f"   ERROR: {log.error_message}")
            print()

if __name__ == "__main__":
    print("🚀 Starting SMTP Debug Test")
    print("=" * 60)
    
    # Test SMTP connection
    success = test_smtp_connection()
    
    # Check email logs
    check_email_logs()
    
    if not success:
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("1. Check Settings → Email Configuration in your web app")
        print("2. Common SMTP settings:")
        print("   - Gmail: smtp.gmail.com:587 (TLS) or 465 (SSL)")
        print("   - Outlook: smtp-mail.outlook.com:587 (TLS)")
        print("   - SendGrid: smtp.sendgrid.net:587 (TLS)")
        print("3. For Gmail, you may need an App Password instead of your regular password")
        print("4. Check if your firewall/network allows outbound SMTP connections")