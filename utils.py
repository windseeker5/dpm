import smtplib
import qrcode
import base64
import io
import socket
import traceback

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from models import Setting, db, Pass, Redemption, Admin, EbankPayment, ReminderLog

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


from datetime import datetime, timedelta, timezone  # ✅ Keep this for datetime.timezone
from pytz import timezone as pytz_timezone, utc      # ✅ This is for "America/Toronto"

import json
import os





def utc_to_local(dt_utc):
    if not dt_utc:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = utc.localize(dt_utc)

    eastern = pytz_timezone("America/Toronto")
    return dt_utc.astimezone(eastern)



from flask import current_app
from models import Setting

def get_setting(key, default=""):
    with current_app.app_context():
        setting = Setting.query.filter_by(key=key).first()
        if setting and setting.value not in [None, ""]:
            return setting.value
    return default







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





def send_email(app, user_email, subject, user_name, pass_code, created_date, remaining_games, special_message=None, admin_email=None):
    try:
        from utils import get_setting
        from models import EmailLog
        from flask import render_template_string, render_template, current_app

        env = os.environ.get("FLASK_ENV", "prod").lower()
        dev_redirect = os.environ.get("DEV_EMAIL_REDIRECT", None)

        if env == "dev" and dev_redirect:
            print(f"📨 [DEV MODE] Redirecting email originally to {user_email} → {dev_redirect}")
            subject = f"[DEV] {subject}"
            user_email = dev_redirect

        qr_image_bytes_io = generate_qr_code_image(pass_code)
        qr_image_bytes = qr_image_bytes_io.read()

        sender_email = get_setting("MAIL_DEFAULT_SENDER") or "no-reply@example.com"
        email_footer = get_setting("EMAIL_FOOTER_TEXT", "")
        email_info_template = get_setting("EMAIL_INFO_TEXT", "")

        hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
        db.session.refresh(hockey_pass)
        email_info = render_template_string(email_info_template, hockey_pass=hockey_pass)
        history_data = get_pass_history_data(pass_code, fallback_admin_email=admin_email)

        owner_html = render_template("partials/owner_section.html", hockey_pass=hockey_pass, logo_src="cid:logo_image")
        history_html = render_template("partials/history_section.html", history=history_data)

        with open("static/uploads/logo.png", "rb") as logo_file:
            logo_bytes = logo_file.read()

        email_html = render_template(
            "email_pass.html",
            user_name=user_name,
            created_date=created_date,
            remaining_games=remaining_games,
            special_message=special_message,
            history=history_data,
            logo_url="cid:logo_image",
            email_info=email_info,
            email_footer=email_footer,
            hockey_pass=hockey_pass,
            owner_html=owner_html,
            history_html=history_html
        )

        msg = MIMEMultipart("related")
        msg["From"] = sender_email
        msg["To"] = user_email
        msg["Subject"] = subject
        msg.attach(MIMEText(email_html, "html"))

        qr_image = MIMEImage(qr_image_bytes, _subtype="png")
        qr_image.add_header("Content-ID", "<qr_code>")
        qr_image.add_header("Content-Disposition", "inline", filename="qr_code.png")
        msg.attach(qr_image)

        logo_image = MIMEImage(logo_bytes, _subtype="jpeg")
        logo_image.add_header("Content-ID", "<logo_image>")
        logo_image.add_header("Content-Disposition", "inline", filename="logo.jpg")
        msg.attach(logo_image)

        # ✅ Send email
        smtp_server = get_setting("MAIL_SERVER")
        smtp_port = int(get_setting("MAIL_PORT", "587"))
        smtp_user = get_setting("MAIL_USERNAME")
        smtp_pass = get_setting("MAIL_PASSWORD")
        use_tls = get_setting("MAIL_USE_TLS", "True").lower() == "true"
        use_proxy = smtp_port == 25 and not use_tls

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        if not use_proxy and use_tls:
            server.starttls()
            server.ehlo()
        if not use_proxy and smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)

        server.sendmail(sender_email, [user_email], msg.as_string())
        server.quit()

        print(f"✅ Email sent to {user_email}")

        # ✅ Log success with consistent timestamp
        db.session.add(EmailLog(
            to_email=user_email,
            subject=subject,
            pass_code=pass_code,
            template_name="email_pass.html",

            context_json=json.dumps({
                "user_name": user_name,
                "created_date": created_date.strftime("%Y-%m-%d %H:%M:%S"),
                "remaining_games": remaining_games,
                "special_message": special_message,
                "history": history_data
            }),


            #timestamp=datetime.strptime(created_date, "%Y-%m-%d %H:%M:%S"),
            timestamp=created_date,  # ⏱ full datetime with microseconds

            result="SENT"
        ))
        db.session.commit()

        return True

    except Exception as e:
        print("❌ Error sending email:")
        traceback.print_exc()

        db.session.add(EmailLog(
            to_email=user_email,
            subject=subject,
            pass_code=pass_code,
            template_name="email_pass.html",

            context_json=json.dumps({
                "user_name": user_name,
                "created_date": created_date.strftime("%Y-%m-%d %H:%M:%S"),
                "remaining_games": remaining_games,
                "special_message": special_message,
                "history": history_data
            }),


            result="FAILED",
            error_message=str(e)
        ))
        db.session.commit()

        return False




def extract_interac_transfers(gmail_user, gmail_password, mail=None):
    results = []

    try:
        # ✅ Always load these settings — even when mail is reused
        subject_keyword = get_setting("BANK_EMAIL_SUBJECT", "Virement Interac :")
        from_expected = get_setting("BANK_EMAIL_FROM", "notify@payments.interac.ca")

        if not mail:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_user, gmail_password)
            mail.select("inbox")

        status, data = mail.search(None, f'SUBJECT "{subject_keyword}"')
        if status != "OK":
            print(f"📭 No matching emails found for subject: {subject_keyword}")
            return results

        for num in data[0].split():
            # 📥 Fetch email content & UID
            status, msg_data = mail.fetch(num, "(BODY.PEEK[] UID)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            uid_line = msg_data[0][0].decode()
            uid_match = re.search(r"UID (\d+)", uid_line)
            uid = uid_match.group(1) if uid_match else None

            # 📦 Parse email headers
            msg = email.message_from_bytes(raw_email)
            from_email = email.utils.parseaddr(msg.get("From"))[1]
            subject_raw = msg["Subject"]
            subject = email.header.decode_header(subject_raw)[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            # 🛡️ Validate subject and sender
            if not subject.lower().startswith(subject_keyword.lower()):
                continue
            if from_email.lower() != from_expected.lower():
                print(f"⚠️ Ignored email from unexpected sender: {from_email}")
                continue

            # 💰 Extract name & amount — support multiple Interac subject formats
            amount_match = re.search(r"reçu\s([\d,]+)\s*\$\s*de", subject)
            name_match = re.search(r"de\s(.+?)\set ce montant", subject)

            # 🔁 Fallback: e.g. "Remi Methot vous a envoyé 15,00 $"
            if not amount_match:
                amount_match = re.search(r"envoyé\s([\d,]+)\s*\$", subject)
            if not name_match:
                name_match = re.search(r":\s*(.*?)\svous a envoyé", subject)

            # 🛡️ Skip if we still can't match
            if not (amount_match and name_match):
                print(f"❌ Skipped unmatched subject: {subject}")
                continue

            # 💵 Final parsing
            amt_str = amount_match.group(1).replace(",", ".")
            name = name_match.group(1).strip()

            try:
                amount = float(amt_str)
            except ValueError:
                print(f"❌ Invalid amount format: {amt_str}")
                continue

            # ✅ Only append if parsing succeeded
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
    and moves matched email to the configured Gmail label.
    """
    with current_app.app_context():
        user = get_setting("MAIL_USERNAME")
        pwd = get_setting("MAIL_PASSWORD")

        if not user or not pwd:
            print("❌ MAIL_USERNAME or MAIL_PASSWORD is not set.")
            return

        # 🧠 Load dynamic matching config
        FUZZY_NAME_MATCH_THRESHOLD = int(get_setting("BANK_EMAIL_NAME_CONFIDANCE", "85"))
        gmail_label = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "InteractProcessed")

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
                    note=f"Fuzzy name score ≥ {FUZZY_NAME_MATCH_THRESHOLD}. Email moved to '{gmail_label}'." if uid else "No UID: email not moved."
                ))

                db.session.commit()
                print(f"✅ Matched & marked as paid: {best_pass.user_name} (${best_pass.sold_amt})")

                # ✅ Send confirmation email
                print("✉️ Sending payment confirmation email...")
                send_email_async(
                    current_app._get_current_object(),  # 👈 REQUIRED!
                    user_email=best_pass.user_email,
                    #subject="LHGI ✅ Payment Received",
                    subject="LHGI ✅ Paiement Confirmé",
                    user_name=best_pass.user_name,
                    pass_code=best_pass.pass_code,
                    created_date=best_pass.pass_created_dt.strftime('%Y-%m-%d'),
                    remaining_games=best_pass.games_remaining,
                    special_message="We've received your payment. Your pass is now active. Thank you!"
                )

                # ✅ Move matched email to configured Gmail label
                if uid:
                    print(f"📂 Moving matched email UID {uid} to '{gmail_label}'")
                    mail.uid("COPY", uid, gmail_label)
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



def send_unpaid_reminders(app):
    """
    Sends reminder emails for unpaid passes older than CALL_BACK_DAYS.
    Ensures a reminder is only sent once per pass per interval.
    Logs all reminders into ReminderLog with a UTC-aware timestamp.
    """
    def ensure_utc_aware(dt):
        """Ensures datetime is timezone-aware (UTC)."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    with app.app_context():
        # 🛠 Get reminder delay (in days) from settings
        try:
            days = float(get_setting("CALL_BACK_DAYS", "15"))
        except ValueError:
            print("❌ Invalid CALL_BACK_DAYS value. Defaulting to 15.")
            days = 15

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # 🔍 Find all unpaid passes older than cutoff
        unpaid_passes = Pass.query.filter(
            Pass.paid_ind == False,
            Pass.pass_created_dt <= cutoff_date
        ).all()

        print(f"🔔 Found {len(unpaid_passes)} unpaid passes older than {days} days.")

        for p in unpaid_passes:
            # ⏩ Skip if a reminder was already sent within the interval
            recent_reminder = ReminderLog.query.filter_by(pass_id=p.id)\
                .order_by(ReminderLog.reminder_sent_at.desc())\
                .first()

            if recent_reminder and ensure_utc_aware(recent_reminder.reminder_sent_at) > datetime.now(timezone.utc) - timedelta(days=days):
                print(f"⏩ Skipping {p.user_email} — reminded too recently.")
                continue

            # ✉️ Compose and send the reminder email
            #subject = "LHGI ⚠️ Your digital pass is still unpaid. Please complete your payment"
            subject = "LHGI ⚠️ Rappel - Vous avez une passe électronique en attente de paiement."
       
            special_message = (
                f"Your pass was created on {p.pass_created_dt.strftime('%Y-%m-%d')} and is still unpaid. "
                f"Please complete your payment soon to use it."
            )

            send_email_async(
                app,
                user_email=p.user_email,
                subject=subject,
                user_name=p.user_name,
                pass_code=p.pass_code,
                created_date=p.pass_created_dt.strftime('%Y-%m-%d'),
                remaining_games=p.games_remaining,
                special_message=special_message,
                admin_email="auto-reminder@system"
            )

            # 📝 Log the reminder with an explicit UTC timestamp
            db.session.add(ReminderLog(
                pass_id=p.id,
                reminder_sent_at=datetime.now(timezone.utc)
            ))
            db.session.commit()

            print(f"✅ Reminder sent to {p.user_email}")

        print("📬 All eligible reminders processed.")



def get_all_activity_logs():
    from models import Pass, Redemption, EmailLog, EbankPayment, ReminderLog
    from utils import utc_to_local
    from flask import current_app

    DATETIME_FORMAT = "%Y-%m-%d %H:%M"
    logs = []

    with current_app.app_context():
        # Pass Creation
        for p in Pass.query.all():
            logs.append({
                "timestamp": utc_to_local(p.pass_created_dt).strftime(DATETIME_FORMAT),
                "type": "Pass Created",
                "user": p.user_name,
                "details": f"Email: {p.user_email}, Code: {p.pass_code}"
            })

        # Redemption
        for r in Redemption.query.all():
            logs.append({
                "timestamp": utc_to_local(r.date_used).strftime(DATETIME_FORMAT),
                "type": "Pass Redeemed",
                "user": r.redeemed_by,
                "details": f"Pass ID: {r.pass_id}"
            })

        # Email Sent
        for e in EmailLog.query.all():
            logs.append({
                "timestamp": utc_to_local(e.timestamp).strftime(DATETIME_FORMAT),
                "type": f"Email {e.result}",
                "user": e.to_email,
                "details": f"Subject: {e.subject}, Pass: {e.pass_code or 'N/A'}"
            })

        # Payments
        for p in EbankPayment.query.all():
            logs.append({
                "timestamp": utc_to_local(p.timestamp).strftime(DATETIME_FORMAT),
                "type": f"Payment {p.result}",
                "user": p.from_email,
                "details": f"Name: {p.bank_info_name}, Amount: {p.bank_info_amt}"
            })

        # Reminders
        for r in ReminderLog.query.all():
            logs.append({
                "timestamp": utc_to_local(r.reminder_sent_at).strftime(DATETIME_FORMAT),
                "type": "Reminder Sent",
                "user": "-",
                "details": f"Pass ID: {r.pass_id}"
            })

    # Sort by timestamp descending
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return logs





def get_kpi_stats():
    from datetime import datetime, timedelta, timezone
    from models import Pass
    from flask import current_app

    with current_app.app_context():
        now = datetime.now(timezone.utc)

        # Define current and previous ranges
        ranges = {
            "7d": (now - timedelta(days=7), now),
            "30d": (now - timedelta(days=30), now),
            "90d": (now - timedelta(days=90), now),
            "all": (datetime.min.replace(tzinfo=timezone.utc), now),
        }
        previous_ranges = {
            "7d": (now - timedelta(days=14), now - timedelta(days=7)),
            "30d": (now - timedelta(days=60), now - timedelta(days=30)),
            "90d": (now - timedelta(days=180), now - timedelta(days=90)),
            "all": (datetime.min.replace(tzinfo=timezone.utc), now),  # same
        }

        kpis = {}

        for label in ranges:
            start, end = ranges[label]
            prev_start, prev_end = previous_ranges[label]

            current_passes = Pass.query.filter(Pass.pass_created_dt >= start, Pass.pass_created_dt <= end).all()
            previous_passes = Pass.query.filter(Pass.pass_created_dt >= prev_start, Pass.pass_created_dt <= prev_end).all()

            def total(passes): return sum(p.sold_amt for p in passes)
            def created(passes): return len(passes)
            def active(passes): return len([p for p in passes if p.games_remaining > 0])

            kpis[label] = {
                "revenue": round(total(current_passes), 2),
                "revenue_prev": round(total(previous_passes), 2),
                "pass_created": created(current_passes),
                "pass_created_prev": created(previous_passes),
                "active_users": active(current_passes),
                "active_users_prev": active(previous_passes)
            }

        return kpis

