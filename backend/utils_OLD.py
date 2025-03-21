import smtplib
import qrcode
import base64
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from models import Setting, db
from flask import current_app

import socket

import traceback
from config import get_setting
from config import Config





def is_on_proxy_network():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return ip.startswith("142.168.")  # Adjust to match your real proxy range
    except:
        return False
    



def save_setting(key, value):
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    db.session.commit()




def get_setting2(key):
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else None

def get_setting(key, default=""):
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else default



def generate_qr_code_image(pass_code):
    """Generate QR code and return as base64 string"""
    qr = qrcode.make(pass_code)
    img_bytes = io.BytesIO()
    qr.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return base64.b64encode(img_bytes.read()).decode()



def generate_qr_code(pass_code):
    """Generate QR code and return as base64 string"""
    qr = qrcode.make(pass_code)
    img_bytes = io.BytesIO()
    qr.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return base64.b64encode(img_bytes.read()).decode()




def send_email_OLD(user_email, subject, user_name, pass_code, created_date, remaining_games, special_message=""):
    """Send an HTML email to the user with embedded QR code"""

    # ✅ Generate QR image
    qr_image_bytes = generate_qr_code_image(pass_code)

    # ✅ Email HTML with CID reference to image
    email_html = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #0056b3;">🏒 Hockey Pass Confirmation</h2>
            <p>Hi <strong>{user_name}</strong>,</p>
            <p>Your pass was created on <strong>{created_date}</strong>.</p>

            <h3>🎟️ Pass Details</h3>
            <ul>
                <li><strong>Pass Code:</strong> {pass_code}</li>
                <li><strong>Remaining Games:</strong> {remaining_games}</li>
            </ul>

            <h3>📸 Scan QR Code</h3>
            <img src="cid:qr_code" alt="QR Code" style="width: 500px; height: 500px;" />

            <p style="color: red; font-weight: bold;">{special_message}</p>

            <h3>💰 Payment Instructions</h3>
            <p>Please transfer the payment to the following account:</p>
            <p><strong>Email:</strong> your-payment-email@gmail.com</p>
            <p><strong>Amount:</strong> $50</p>

            <p>Thank you for supporting the league!</p>
        </div>
    </body>
    </html>
    """

    # ✅ Build email
    msg = MIMEMultipart("related")
    msg["From"] = Config.MAIL_DEFAULT_SENDER or "no-reply@yourcompany.com"
    msg["To"] = user_email
    msg["Subject"] = subject

    # Attach HTML part
    html_part = MIMEText(email_html, "html")
    msg.attach(html_part)

    # Attach QR image with content ID
    qr_image = MIMEImage(qr_image_bytes.read(), _subtype="png")
    qr_image.add_header("Content-ID", "<qr_code>")
    qr_image.add_header("Content-Disposition", "inline", filename="qr_code.png")
    msg.attach(qr_image)

    # ✅ Send the email
    try:
        server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
        server.ehlo()
        server.sendmail(msg["From"], user_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {user_email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")





def send_email(user_email, subject, user_name, pass_code, created_date, remaining_games, special_message=""):

    qr_image_bytes = generate_qr_code_image(pass_code)

    email_html = f"""
    <html>
    <body>
        <h2>🏒 Hockey Pass Info</h2>
        <p><strong>User:</strong> {user_name}</p>
        <p><strong>Date Created:</strong> {created_date}</p>
        <p><strong>Remaining Games:</strong> {remaining_games}</p>
        <img src="cid:qr_code" width="150" height="150"><br>
        <p style="color: red;">{special_message}</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("related")
    msg["From"] = get_setting("MAIL_DEFAULT_SENDER") or "no-reply@example.com"
    msg["To"] = user_email
    msg["Subject"] = subject
    msg.attach(MIMEText(email_html, "html"))

    # Attach QR code image
    qr_image = MIMEImage(qr_image_bytes.read(), _subtype="png")
    qr_image.add_header("Content-ID", "<qr_code>")
    qr_image.add_header("Content-Disposition", "inline", filename="qr_code.png")
    msg.attach(qr_image)

    # Load settings
    smtp_server = get_setting("MAIL_SERVER")
    smtp_port = int(get_setting("MAIL_PORT", "587"))
    smtp_user = get_setting("MAIL_USERNAME")
    smtp_pass = get_setting("MAIL_PASSWORD")
    use_tls = get_setting("MAIL_USE_TLS", "True").lower() == "true"

    use_proxy = smtp_port == 25 and not use_tls

    print("📬 Sending email with the following settings:")
    print(f"  SERVER: {smtp_server}")
    print(f"  PORT: {smtp_port}")
    print(f"  USER: {smtp_user}")
    print(f"  USE_TLS: {use_tls}")
    print(f"  DETECTED MODE: {'PROXY' if use_proxy else 'GMAIL'}")

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Enable SMTP debug
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


