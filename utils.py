import smtplib
import qrcode
import base64
import io
import socket
import traceback

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from models import Setting, db, Pass, Redemption, Admin, EbankPayment
import threading
import logging
from datetime import datetime
 
from flask import render_template, render_template_string, url_for, current_app, session


from pprint import pprint
from email.utils import parsedate_to_datetime
import imaplib
import email
import re

from rapidfuzz import fuzz
import imaplib

from pytz import timezone, utc



def utc_to_local(dt_utc):
    """Converts UTC or naive datetime to local 'America/Toronto' time safely."""
    if not dt_utc:
        return None

    if dt_utc.tzinfo is None:
        # 🛑 Naive datetime — assume it's UTC
        dt_utc = utc.localize(dt_utc)

    eastern = timezone("America/Toronto")
    return dt_utc.astimezone(eastern)



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



def send_email_async(app, *args, **kwargs):
    def run_in_context():
        with app.app_context():
            send_email(app, *args, **kwargs)  # ✅ FIXED
    thread = threading.Thread(target=run_in_context)
    thread.start()



 

def get_pass_history_data(pass_code: str, fallback_admin_email=None) -> dict:
    """
    Builds the history log for a digital pass, converting UTC timestamps to local time (America/Toronto).
    Returns a dictionary including: created, paid, redemptions, expired, and who performed each action.

    Accepts fallback_admin_email for use in background tasks (outside of request context).
    """
    with current_app.app_context():
        DATETIME_FORMAT = "%Y-%m-%d %H:%M"

        # 🔍 Fetch pass
        hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
        if not hockey_pass:
            return {"error": "Pass not found."}

        # 🔁 Fetch redemptions sorted by usage date
        redemptions = (
            Redemption.query
            .filter_by(pass_id=hockey_pass.id)
            .order_by(Redemption.date_used.asc())
            .all()
        )

        # 📦 Initialize history structure
        history = {
            "created": None,
            "created_by": None,
            "paid": None,
            "paid_by": None,
            "redemptions": [],
            "expired": None
        }

        # 📅 Created (UTC → local)
        if hockey_pass.pass_created_dt:
            history["created"] = utc_to_local(hockey_pass.pass_created_dt).strftime(DATETIME_FORMAT)

        # 👤 Created by
        if hockey_pass.created_by:
            admin = Admin.query.get(hockey_pass.created_by)
            history["created_by"] = admin.email if admin else "-"

        # 💵 Payment info (UTC → local)
        if hockey_pass.paid_ind and hockey_pass.paid_date:
            history["paid"] = utc_to_local(hockey_pass.paid_date).strftime(DATETIME_FORMAT)

            ebank = (
                EbankPayment.query
                .filter_by(matched_pass_id=hockey_pass.id, mark_as_paid=True)
                .order_by(EbankPayment.timestamp.desc())
                .first()
            )

            if ebank:
                history["paid_by"] = ebank.from_email
            else:
                # ✅ Session-safe: fallback_admin_email is passed in by route OR defaults
                email = fallback_admin_email or "admin panel"
                history["paid_by"] = email.split("@")[0] if "@" in email else email

        # 🎮 Redemptions (UTC → local)
        for r in redemptions:
            local_used = utc_to_local(r.date_used)
            history["redemptions"].append({
                "date": local_used.strftime(DATETIME_FORMAT),
                "by": r.redeemed_by or "-"
            })

        # ❌ Expired if no games remaining
        if hockey_pass.games_remaining == 0 and redemptions:
            history["expired"] = utc_to_local(redemptions[-1].date_used).strftime(DATETIME_FORMAT)

        return history




def get_pass_history_data_OLD(pass_code: str) -> dict:
    """
    Builds the history log for a digital pass, converting UTC timestamps to local time (America/Toronto).
    Returns a dictionary including: created, paid, redemptions, expired, and who performed each action.
    """
    with current_app.app_context():
        DATETIME_FORMAT = "%Y-%m-%d %H:%M"

        # 🔍 Fetch pass
        hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
        if not hockey_pass:
            return {"error": "Pass not found."}

        # 🔁 Fetch redemptions sorted by usage date
        redemptions = (
            Redemption.query
            .filter_by(pass_id=hockey_pass.id)
            .order_by(Redemption.date_used.asc())
            .all()
        )

        # 📦 Initialize history structure
        history = {
            "created": None,
            "created_by": None,
            "paid": None,
            "paid_by": None,
            "redemptions": [],
            "expired": None
        }

        # 📅 Created (UTC → local)
        if hockey_pass.pass_created_dt:
            history["created"] = utc_to_local(hockey_pass.pass_created_dt).strftime(DATETIME_FORMAT)

        # 👤 Created by
        if hockey_pass.created_by:
            admin = Admin.query.get(hockey_pass.created_by)
            history["created_by"] = admin.email if admin else "-"

        # 💵 Payment info (UTC → local)
        if hockey_pass.paid_ind and hockey_pass.paid_date:
            history["paid"] = utc_to_local(hockey_pass.paid_date).strftime(DATETIME_FORMAT)

            ebank = (
                EbankPayment.query
                .filter_by(matched_pass_id=hockey_pass.id, mark_as_paid=True)
                .order_by(EbankPayment.timestamp.desc())
                .first()
            )

            if ebank:
                history["paid_by"] = ebank.from_email
            else:
                history["paid_by"] = "admin panel"

        # 🎮 Redemptions
        for r in redemptions:
            local_used = utc_to_local(r.date_used)
            history["redemptions"].append({
                "date": local_used.strftime(DATETIME_FORMAT),
                "by": r.redeemed_by or "-"
            })

        # ❌ Expired if no games remaining
        if hockey_pass.games_remaining == 0 and redemptions:
            history["expired"] = utc_to_local(redemptions[-1].date_used).strftime(DATETIME_FORMAT)

        return history




def send_email(app, user_email, subject, user_name, pass_code, created_date, remaining_games, special_message=None, admin_email=None):

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



        #history_data = get_pass_history_data(pass_code)
        history_data = get_pass_history_data(pass_code, fallback_admin_email=admin_email)

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




def extract_interac_transfers(gmail_user, gmail_password, mail=None):
    results = []

    try:
        if not mail:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_user, gmail_password)
            mail.select("inbox")

        status, data = mail.search(None, 'SUBJECT "Virement Interac :"')
        if status != "OK":
            print("No matching Interac emails found.")
            return results

        for num in data[0].split():
            # Fetch email metadata + body
            status, msg_data = mail.fetch(num, "(BODY.PEEK[] UID)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            uid_line = msg_data[0][0].decode()
            uid_match = re.search(r"UID (\d+)", uid_line)
            uid = uid_match.group(1) if uid_match else None

            msg = email.message_from_bytes(raw_email)
            from_email = email.utils.parseaddr(msg.get("From"))[1]
            subject_raw = msg["Subject"]
            subject = email.header.decode_header(subject_raw)[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            if not subject.lower().startswith("virement interac"):
                continue
            if from_email.lower() != "notify@payments.interac.ca":
                print(f"⚠️ Ignored email from: {from_email}")
                continue

            amount_match = re.search(r"reçu\s([\d,]+)\s*\$\s*de", subject)
            name_match = re.search(r"de\s(.+?)\set ce montant", subject)

            if amount_match and name_match:
                amt_str = amount_match.group(1).replace(",", ".")
                name = name_match.group(1).strip()
                try:
                    amount = float(amt_str)
                except ValueError:
                    continue

                results.append({
                    "bank_info_name": name,
                    "bank_info_amt": amount,
                    "subject": subject,
                    "from_email": from_email,
                    "uid": uid
                })

    except Exception as e:
        print(f"❌ Error reading Gmail: {e}")

    return results





def match_gmail_payments_to_passes():
    """
    Checks Gmail for Interac payment emails, matches them to unpaid passes,
    updates payment status, logs to EbankPayment, sends confirmation email,
    and moves matched email to InteractProcessed label.
    """
    FUZZY_NAME_MATCH_THRESHOLD = 85

    with current_app.app_context():
        user = get_setting("MAIL_USERNAME")
        pwd = get_setting("MAIL_PASSWORD")

        if not user or not pwd:
            print("❌ MAIL_USERNAME or MAIL_PASSWORD is not set.")
            return

        print("📥 Connecting to Gmail...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, pwd)
        mail.select("inbox")

        print("📬 Fetching Interac emails...")
        matches = extract_interac_transfers(user, pwd, mail)
        print(f"📌 Found {len(matches)} email(s) to process")

        for match in matches:
            name = match["bank_info_name"]
            amt = match["bank_info_amt"]
            subject = match["subject"]
            from_email = match.get("from_email")
            uid = match.get("uid")

            best_score = 0
            best_pass = None
            unpaid_passes = Pass.query.filter_by(paid_ind=False).all()

            for p in unpaid_passes:
                name_score = fuzz.partial_ratio(name.lower(), p.user_name.lower())
                if name_score >= FUZZY_NAME_MATCH_THRESHOLD and abs(p.sold_amt - amt) < 1:
                    if name_score > best_score:
                        best_score = name_score
                        best_pass = p

            if best_pass:
                best_pass.paid_ind = True
                best_pass.paid_date = datetime.utcnow()
                db.session.add(best_pass)

                db.session.add(EbankPayment(
                    from_email=from_email,
                    subject=subject,
                    bank_info_name=name,
                    bank_info_amt=amt,
                    matched_pass_id=best_pass.id,
                    matched_name=best_pass.user_name,
                    matched_amt=best_pass.sold_amt,
                    name_score=best_score,
                    result="MATCHED",
                    mark_as_paid=True,
                    note=f"Fuzzy name score ≥ {FUZZY_NAME_MATCH_THRESHOLD}. Email moved to 'InteractProcessed'." if uid else "No UID: email not moved."
                ))

                db.session.commit()
                print(f"✅ Matched & marked as paid: {best_pass.user_name} (${best_pass.sold_amt})")

                # ✅ Send confirmation email
                print("✉️ Sending payment confirmation email...")
                send_email_async(
                    current_app._get_current_object(),  # 👈 REQUIRED!
                    user_email=best_pass.user_email,
                    subject="LHGI ✅ Payment Received",
                    user_name=best_pass.user_name,
                    pass_code=best_pass.pass_code,
                    created_date=best_pass.pass_created_dt.strftime('%Y-%m-%d'),
                    remaining_games=best_pass.games_remaining,
                    special_message="We've received your payment. Your pass is now active. Thank you!"
                )

                # ✅ Move matched email to Gmail label
                if uid:
                    print(f"📂 Moving matched email UID {uid} to 'InteractProcessed'")
                    mail.uid("COPY", uid, "InteractProcessed")
                    mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")

            else:
                # ❌ Log unmatched emails
                db.session.add(EbankPayment(
                    from_email=from_email,
                    subject=subject,
                    bank_info_name=name,
                    bank_info_amt=amt,
                    name_score=0,
                    result="NO_MATCH",
                    mark_as_paid=False,
                    note=f"No match found with threshold ≥ {FUZZY_NAME_MATCH_THRESHOLD}"
                ))
                print(f"⚠️ No match for: {name} - ${amt}")

        db.session.commit()
        print("📋 All actions committed to EbankPayment log.")

        mail.expunge()
        mail.logout()
        print("🧹 Gmail cleanup complete.")
