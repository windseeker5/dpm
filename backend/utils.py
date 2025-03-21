import smtplib
import qrcode
import base64
import io
import socket
import traceback

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from flask import current_app
from models import Setting, db
import threading
import logging




 
##
## === SETTINGS ===
##
def get_setting(key, default=""):
    with current_app.app_context():
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default




def save_setting(key, value):
    with current_app.app_context():
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.session.add(setting)
        db.session.commit()



def is_on_proxy_network():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return ip.startswith("142.168.")  # Adjust to your actual proxy IP range
    except:
        return False



##
## === QR CODE GENERATION ===
##

def generate_qr_code(pass_code):
    qr = qrcode.make(pass_code)
    img_bytes = io.BytesIO()
    qr.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return base64.b64encode(img_bytes.read()).decode()



def generate_qr_code_image(pass_code):
    qr = qrcode.make(pass_code)
    img_bytes = io.BytesIO()
    qr.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes





##
## === EMAIL ===
##

def send_email(user_email, subject, user_name, pass_code, created_date, remaining_games, special_message=""):
    try:
        # ✅ Generate QR code image as base64 string
        qr_image_bytes_io = generate_qr_code_image(pass_code)  # Returns BytesIO
        qr_image_bytes_io.seek(0)  # Ensure we are at the start of the stream
        qr_base64 = base64.b64encode(qr_image_bytes_io.read()).decode()  # Encode to base64 string

        # ✅ Convert Base64 to Binary for Email Attachment
        qr_image_bytes = base64.b64decode(qr_base64)

        # ✅ Email Template
        email_html = f"""<html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    font-size: 20px;
                    font-weight: bold;
                    color: #333;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                .content {{
                    padding: 20px;
                    text-align: center;
                    color: #555;
                }}
                .qr-container {{
                    background-color: #f2f2f2;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px auto;
                    width: 200px;
                    text-align: center;
                }}
                .qr-container img {{
                    width: 150px;
                    height: 150px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #1a73e8;
                    color: white;
                    text-decoration: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    margin-top: 15px;
                    font-size: 14px;
                }}
                .footer {{
                    font-size: 12px;
                    color: #777;
                    text-align: center;
                    margin-top: 20px;
                    padding-top: 10px;
                    border-top: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">🏒 Your Hockey Pass</div>
                <div class="content">
                    <p><strong>Hello, {user_name}!</strong></p>
                    <p>Your pass was created on <strong>{created_date}</strong>.</p>
                    <p>You have <strong>{remaining_games}</strong> games remaining.</p>
                    <div class="qr-container">
                        <img src="cid:qr_code" alt="QR Code">
                    </div>
                    <p>Scan this QR code at the entrance.</p>
                    <a href="#" class="button">View Pass</a>
                </div>
                <div class="footer">
                    <p>Need help? <a href="#">Contact Support</a></p>
                    <p>&copy; 2025 Your Hockey League</p>
                </div>
            </div>
        </body>
        </html>
        """

        # ✅ Build Email
        msg = MIMEMultipart("related")
        msg["From"] = get_setting("MAIL_DEFAULT_SENDER") or "no-reply@example.com"
        msg["To"] = user_email
        msg["Subject"] = subject
        msg.attach(MIMEText(email_html, "html"))

        # ✅ Attach QR Code Image
        qr_image = MIMEImage(qr_image_bytes, _subtype="png")
        qr_image.add_header("Content-ID", "<qr_code>")
        qr_image.add_header("Content-Disposition", "inline", filename="qr_code.png")
        msg.attach(qr_image)

        # ✅ Load Email Settings
        smtp_server = get_setting("MAIL_SERVER")
        smtp_port = int(get_setting("MAIL_PORT", "587"))
        smtp_user = get_setting("MAIL_USERNAME")
        smtp_pass = get_setting("MAIL_PASSWORD")
        use_tls = get_setting("MAIL_USE_TLS", "True").lower() == "true"

        use_proxy = smtp_port == 25 and not use_tls  # Detect proxy mode

        print("📬 Sending email with the following settings:")
        print(f"  SERVER: {smtp_server}")
        print(f"  PORT: {smtp_port}")
        print(f"  USER: {smtp_user}")
        print(f"  USE_TLS: {use_tls}")
        print(f"  DETECTED MODE: {'PROXY' if use_proxy else 'GMAIL'}")

        # ✅ Send Email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0)  # Enable SMTP debug
        server.ehlo()

        if not use_proxy and use_tls:
            server.starttls()
            server.ehlo()

        if not use_proxy and smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)

        server.sendmail(msg["From"], [user_email], msg.as_string())
        server.quit()

        print(f"✅ Email sent to {user_email}")
        return True

    except Exception as e:
        print("❌ Error sending email:")
        traceback.print_exc()
        return False








def send_email_async(app, *args, **kwargs):
    def run_in_context():
        with app.app_context():
            send_email(*args, **kwargs)
    thread = threading.Thread(target=run_in_context)
    thread.start()
