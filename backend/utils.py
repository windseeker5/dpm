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

# === SETTINGS ===
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

# === QR CODE GENERATION ===
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

# === EMAIL ===
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
        server.set_debuglevel(1)
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
