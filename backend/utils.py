import smtplib
import qrcode
import base64
import io
import socket
import traceback

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from models import Setting, db, Pass, Redemption
import threading
import logging
from datetime import datetime
 
from flask import render_template, render_template_string, url_for, current_app


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


def send_email_bk(user_email, subject, user_name, pass_code, created_date, remaining_games, special_message=""):
    try:
        from utils import get_setting  # ✅ Just to be safe if reused from another module

        # ✅ Generate QR code image
        qr_image_bytes_io = generate_qr_code_image(pass_code)
        qr_image_bytes_io.seek(0)
        qr_image_bytes = qr_image_bytes_io.read()  # Use binary directly

        # ✅ Fetch dynamic settings
        email_info = get_setting("EMAIL_INFO_TEXT", "")
        email_footer = get_setting("EMAIL_FOOTER_TEXT", "")
        sender_email = get_setting("MAIL_DEFAULT_SENDER") or "no-reply@example.com"



        history_data = get_pass_history_data(pass_code)

        # Build the pass history table as HTML
        history_html = """
        <div style="text-align: center; width: 100%; margin-top: 10px;">
        <table style="
            width: 100%;
            max-width: 500px;
            margin: 0 auto;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 12px;
            border: 1px solid #ccc;
            border-radius: 8px;
            overflow: hidden;
            text-align: left;
        ">
            <thead>
            <tr style="background-color: #f2f2f2;">
                <th style='text-align: left; padding: 8px 12px; border-bottom: 1px solid #ccc; font-weight: bold;'>Event</th>
                <th style='text-align: left; padding: 8px 12px; border-bottom: 1px solid #ccc; font-weight: bold;'>Date</th>
            </tr>
            </thead>
            <tbody>
        """

        # Add Created row
        history_html += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">Created</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{history_data['created']}</td>
        </tr>
        """

        # Add Paid row
        if history_data["paid"]:
            history_html += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">Paid</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{history_data['paid']}</td>
        </tr>
        """
        else:
            history_html += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">Paid</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;"><span style="font-size: 16px;">❌</span> Not Paid</td>
        </tr>
        """

        # Add Redemptions
        for idx, date in enumerate(history_data["redemptions"], 1):
            history_html += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">Redeem #{idx}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{date}</td>
        </tr>
        """

        # Add Expired row
        if history_data["expired"]:
            history_html += f"""
        <tr>
            <td style="padding: 8px 12px;">Expired</td>
            <td style="padding: 8px 12px;">{history_data['expired']}</td>
        </tr>
        """

        # Close table
        history_html += """
            </tbody>
        </table>
        </div>
        """






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
                .info-box {{
                    margin-top: 20px;
                    background-color: #eef5ff;
                    padding: 10px;
                    border-radius: 6px;
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

                    <div class="history-box" style="margin-top: 20px;">
                    <h4 style="font-size: 16px; color: #333;">📜 Pass History</h4>
                    {history_html}
                    </div>



                    {f'<p style="color: red; font-weight: bold;">{special_message}</p>' if special_message else ''}

                    <div class="info-box">{email_info}</div>
                </div>
                <div class="footer">
                    {email_footer}
                </div>
            </div>
        </body>
        </html>
        """

        # ✅ Build Email
        msg = MIMEMultipart("related")
        msg["From"] = sender_email
        msg["To"] = user_email
        msg["Subject"] = subject
        msg.attach(MIMEText(email_html, "html"))

        # ✅ Attach QR code image
        qr_image = MIMEImage(qr_image_bytes, _subtype="png")
        qr_image.add_header("Content-ID", "<qr_code>")
        qr_image.add_header("Content-Disposition", "inline", filename="qr_code.png")
        msg.attach(qr_image)

        # ✅ Load SMTP Settings
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

        # ✅ Connect and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0)
        server.ehlo()
        if not use_proxy and use_tls:
            server.starttls()
            server.ehlo()
        if not use_proxy and smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)

        server.sendmail(sender_email, [user_email], msg.as_string())
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




def get_pass_history_data(pass_code: str) -> dict:
    with current_app.app_context():

        DATETIME_FORMAT = "%Y-%m-%d %H:%M"

        hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
        if not hockey_pass:
            return {"error": "Pass not found."}

        redemptions = (
            Redemption.query.filter_by(pass_id=hockey_pass.id)
            .order_by(Redemption.date_used.asc())
            .all()
        )

        history = {
            "created": hockey_pass.pass_created_dt.strftime(DATETIME_FORMAT),
            "paid": None,
            "redemptions": [],
            "expired": None
        }

        if hockey_pass.paid_ind:
            # Optional: infer from earliest redemption or fallback to creation
            history["paid"] = hockey_pass.pass_created_dt.strftime(DATETIME_FORMAT)

        for redemption in redemptions:
            history["redemptions"].append(redemption.date_used.strftime(DATETIME_FORMAT))

        if hockey_pass.games_remaining == 0 and redemptions:
            history["expired"] = redemptions[-1].date_used.strftime(DATETIME_FORMAT)

        return history




def send_email(user_email, subject, user_name, pass_code, created_date, remaining_games, special_message=""):
    try:
        from utils import get_setting  # ✅ Just to be safe if reused from another module

        # ✅ Generate QR code image
        qr_image_bytes_io = generate_qr_code_image(pass_code)
        qr_image_bytes_io.seek(0)
        qr_image_bytes = qr_image_bytes_io.read()  # Use binary directly


        # ✅ Fetch dynamic settings
        email_info = get_setting("EMAIL_INFO_TEXT", "")
        email_footer = get_setting("EMAIL_FOOTER_TEXT", "")
        sender_email = get_setting("MAIL_DEFAULT_SENDER") or "no-reply@example.com"



        history_data = get_pass_history_data(pass_code)

        # Load the hockey_pass object
        hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()

        # Render email_info with access to hockey_pass
        email_info_template = get_setting("EMAIL_INFO_TEXT", "")
        email_info = render_template_string(email_info_template, hockey_pass=hockey_pass)


        with open("static/uploads/logo.png", "rb") as logo_file:
            logo_bytes = logo_file.read()
            logo_url = "cid:logo_image"



        email_html = render_template(
            "email_pass.html",
            user_name=user_name,
            created_date=created_date,
            remaining_games=remaining_games,
            special_message=special_message,
            history=history_data,
            logo_url=logo_url,
            email_info=email_info,
            email_footer=email_footer,
            hockey_pass=hockey_pass  # ✅ Needed for the owner card section
        )

    

        # ✅ Build Email
        msg = MIMEMultipart("related")
        msg["From"] = sender_email
        msg["To"] = user_email
        msg["Subject"] = subject
        msg.attach(MIMEText(email_html, "html"))

        # ✅ Attach QR code image
        qr_image = MIMEImage(qr_image_bytes, _subtype="png")
        qr_image.add_header("Content-ID", "<qr_code>")
        qr_image.add_header("Content-Disposition", "inline", filename="qr_code.png")
        msg.attach(qr_image)

        # ✅ Attach logo image
        logo_image = MIMEImage(logo_bytes, _subtype="jpeg")
        logo_image.add_header("Content-ID", "<logo_image>")
        logo_image.add_header("Content-Disposition", "inline", filename="logo.jpg")
        msg.attach(logo_image)


        # ✅ Load SMTP Settings
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

        # ✅ Connect and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0)
        server.ehlo()
        if not use_proxy and use_tls:
            server.starttls()
            server.ehlo()
        if not use_proxy and smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)

        server.sendmail(sender_email, [user_email], msg.as_string())
        server.quit()

        print(f"✅ Email sent to {user_email}")
        return True

    except Exception as e:
        print("❌ Error sending email:")
        traceback.print_exc()
        return False

