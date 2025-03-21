import smtplib
import qrcode
import base64
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from config import Config

def generate_qr_code_image(pass_code):
    """Generate QR code and return BytesIO image"""
    qr = qrcode.make(pass_code)
    img_bytes = io.BytesIO()
    qr.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes


def send_email(user_email, subject, user_name, pass_code, created_date, remaining_games, special_message=""):
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
