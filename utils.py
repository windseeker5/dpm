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


from flask import render_template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
import traceback
from premailer import transform
import os
import re
from flask import current_app
from models import Setting





def utc_to_local(dt_utc):
    if not dt_utc:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = utc.localize(dt_utc)

    eastern = pytz_timezone("America/Toronto")
    return dt_utc.astimezone(eastern)



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



def send_email_async(app, **kwargs):
    def send_in_thread():
        with app.app_context():
            try:
                from utils import send_email

                subject = kwargs.get("subject")
                to_email = kwargs.get("to_email")
                template_name = kwargs.get("template_name")
                context = kwargs.get("context", {})
                inline_images = kwargs.get("inline_images", {})
                intro_text = kwargs.get("intro_text")
                conclusion_text = kwargs.get("conclusion_text")
                html_body = kwargs.get("html_body")
                timestamp_override = kwargs.get("timestamp_override")

                send_email(
                    subject=subject,
                    to_email=to_email,
                    template_name=template_name,
                    context=context,
                    inline_images=inline_images,
                    intro_text=intro_text,
                    conclusion_text=conclusion_text,
                    html_body=html_body  # 🆕 New support
                )

                from models import EmailLog
                def format_dt(dt):
                    return dt.strftime('%Y-%m-%d %H:%M') if isinstance(dt, datetime) else dt

                db.session.add(EmailLog(
                    to_email=to_email,
                    subject=subject,
                    pass_code=context.get("hockey_pass", {}).get("pass_code"),
                    template_name=template_name,
                    context_json=json.dumps({
                        "user_name": context.get("hockey_pass", {}).get("user_name"),
                        "created_date": format_dt(context.get("hockey_pass", {}).get("pass_created_dt")),
                        "remaining_games": context.get("hockey_pass", {}).get("games_remaining"),
                        "special_message": context.get("special_message", "")
                    }),
                    result="SENT",
                    timestamp=timestamp_override or datetime.now(timezone.utc)
                ))
                db.session.commit()

            except Exception as e:
                import traceback
                traceback.print_exc()
                from models import EmailLog
                db.session.add(EmailLog(
                    to_email=kwargs.get("to_email"),
                    subject=kwargs.get("subject"),
                    pass_code=kwargs.get("context", {}).get("hockey_pass", {}).get("pass_code"),
                    template_name=kwargs.get("template_name"),
                    context_json=json.dumps({"error": str(e)}),
                    result="FAILED",
                    error_message=str(e),
                    timestamp=kwargs.get("timestamp_override") or datetime.now(timezone.utc)
                ))
                db.session.commit()

    thread = threading.Thread(target=send_in_thread)
    thread.start()



def notify_pass_event(app, *, event_type, hockey_pass, admin_email=None, timestamp=None):
    from utils import send_email_async, get_pass_history_data, generate_qr_code_image, get_setting
    from flask import render_template, render_template_string, url_for
    from datetime import datetime, timezone
    import json
    import base64
    import os

    timestamp = timestamp or datetime.now(timezone.utc)
    event_key = event_type.lower().replace(" ", "_")

    # ✅ Normalize theme_key prefix based on event type
    if event_key in ["pass_created", "pass_redeemed", "payment_received", "payment_late"]:
        theme_key = f"THEME_{event_key}"
        subject_key = f"SUBJECT_{event_key}"
        title_key = f"TITLE_{event_key}"
        intro_key = f"INTRO_{event_key}"
        conclusion_key = f"CONCLUSION_{event_key}"
    else:
        theme_key = f"THEME_pass_{event_key}"
        subject_key = f"SUBJECT_pass_{event_key}"
        title_key = f"TITLE_pass_{event_key}"
        intro_key = f"INTRO_pass_{event_key}"
        conclusion_key = f"CONCLUSION_pass_{event_key}"

    theme = get_setting(theme_key, "confirmation.html")
    print("🧪 Raw get_setting theme key:", theme_key)
    print("🧪 theme value from DB:", theme)

    subject = get_setting(subject_key, f"[Minipass] {event_type.title()} Notification")
    title = get_setting(title_key, f"{event_type.title()} Confirmation")
    intro_raw = get_setting(intro_key, "")
    conclusion_raw = get_setting(conclusion_key, "")

    # ✅ Normalize cross-model values
    games_remaining = getattr(hockey_pass, "games_remaining", None) or getattr(hockey_pass, "uses_remaining", 0)
    activity_display = getattr(hockey_pass, "activity", "")
    if hasattr(activity_display, "name"):
        activity_display = activity_display.name

    intro = render_template_string(intro_raw, hockey_pass=hockey_pass, default_qt=games_remaining, activity_list=activity_display)
    conclusion = render_template_string(conclusion_raw, hockey_pass=hockey_pass, default_qt=games_remaining, activity_list=activity_display)

    print("🔔 Email debug - subject:", subject)
    print("🔔 Email debug - title:", title)
    print("🔔 Email debug - intro:", intro[:80])

    qr_data = generate_qr_code_image(hockey_pass.pass_code).read()
    history = get_pass_history_data(hockey_pass.pass_code, fallback_admin_email=admin_email)

    context = {
        "hockey_pass": {
            "pass_code": hockey_pass.pass_code,
            "user_name": getattr(hockey_pass, "user_name", None) or getattr(getattr(hockey_pass, "user", None), "name", ""),
            "activity": activity_display,
            "games_remaining": games_remaining,
            "sold_amt": hockey_pass.sold_amt,
            "user_email": getattr(hockey_pass, "user_email", None) or getattr(getattr(hockey_pass, "user", None), "email", ""),
            "phone_number": getattr(hockey_pass, "phone_number", None) or getattr(getattr(hockey_pass, "user", None), "phone_number", ""),
            "pass_created_dt": getattr(hockey_pass, "pass_created_dt", getattr(hockey_pass, "created_dt", None)),
            "paid_ind": getattr(hockey_pass, "paid_ind", getattr(hockey_pass, "paid", False))
        },
        "title": title,
        "intro_text": intro,
        "conclusion_text": conclusion,
        "owner_html": render_template("email_blocks/owner_card_inline.html", hockey_pass=hockey_pass),
        "history_html": render_template("email_blocks/history_table_inline.html", history=history),
        "email_info": "",
        "logo_url": url_for("static", filename="uploads/logo.png"),
        "special_message": ""
    }

    compiled_folder = os.path.join("templates/email_templates", theme.replace(".html", "_compiled"))
    index_path = os.path.join(compiled_folder, "index.html")
    json_path = os.path.join(compiled_folder, "inline_images.json")
    use_compiled = os.path.exists(index_path) and os.path.exists(json_path)

    if use_compiled:
        with open(index_path, "r") as f:
            raw_html = f.read()
        html_body = render_template_string(raw_html, **context)

        with open(json_path, "r") as f:
            inline_images = {cid: base64.b64decode(data) for cid, data in json.load(f).items()}
        inline_images["qr_code"] = qr_data

        logo_path = os.path.join(compiled_folder.replace("_compiled", ""), "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as logo_file:
                inline_images["logo"] = logo_file.read()
        else:
            print("⚠️ logo.png not found in template folder.")

        send_email_async(
            app,
            subject=subject,
            to_email=getattr(hockey_pass, "user_email", None) or getattr(getattr(hockey_pass, "user", None), "email", None),
            html_body=html_body,
            inline_images=inline_images,
            timestamp_override=timestamp
        )
    else:
        inline_images = {
            "qr_code": qr_data,
            "logo_image": open("static/uploads/logo.png", "rb").read()
        }

        send_email_async(
            app,
            subject=subject,
            to_email=hockey_pass.user_email,
            template_name=theme,
            context=context,
            inline_images=inline_images,
            timestamp_override=timestamp
        )




def get_pass_history_data333333333333333(pass_code: str, fallback_admin_email=None) -> dict:
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


def get_pass_history_data(pass_code: str, fallback_admin_email=None) -> dict:
    """
    Builds the history log for a digital pass, converting UTC timestamps to local time (America/Toronto).
    Returns a dictionary including: created, paid, redemptions, expired, and who performed each action.

    Accepts fallback_admin_email for use in background tasks (outside of request context).
    """
    with current_app.app_context():
        from models import Admin, EbankPayment, Redemption, Pass, Passport
        DATETIME_FORMAT = "%Y-%m-%d %H:%M"

        # 🔍 Try both models
        hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
        passport_mode = False
        if not hockey_pass:
            hockey_pass = Passport.query.filter_by(pass_code=pass_code).first()
            passport_mode = True

        if not hockey_pass:
            return {"error": "Pass not found."}

        # 🔁 Fetch redemptions if using Pass
        redemptions = []
        if not passport_mode:
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

        # 📅 Created
        created_dt = getattr(hockey_pass, "pass_created_dt", None) or getattr(hockey_pass, "created_dt", None)
        if created_dt:
            history["created"] = utc_to_local(created_dt).strftime(DATETIME_FORMAT)

        # 👤 Created by
        created_by = getattr(hockey_pass, "created_by", None)
        if created_by:
            admin = Admin.query.get(created_by)
            history["created_by"] = admin.email if admin else "-"

        # 💵 Payment info
        paid = getattr(hockey_pass, "paid_ind", None) if not passport_mode else getattr(hockey_pass, "paid", False)
        paid_date = getattr(hockey_pass, "paid_date", None) if not passport_mode else None
        if paid and (paid_date or not passport_mode):
            paid_dt = utc_to_local(paid_date) if paid_date else created_dt  # fallback to created_dt for Passport
            history["paid"] = paid_dt.strftime(DATETIME_FORMAT)

            if not passport_mode:
                ebank = (
                    EbankPayment.query
                    .filter_by(matched_pass_id=hockey_pass.id, mark_as_paid=True)
                    .order_by(EbankPayment.timestamp.desc())
                    .first()
                )

                if ebank:
                    history["paid_by"] = ebank.from_email
                else:
                    email = fallback_admin_email or "admin panel"
                    history["paid_by"] = email.split("@")[0] if "@" in email else email
            else:
                history["paid_by"] = fallback_admin_email or "admin"

        # 🎮 Redemptions
        for r in redemptions:
            local_used = utc_to_local(r.date_used)
            history["redemptions"].append({
                "date": local_used.strftime(DATETIME_FORMAT),
                "by": r.redeemed_by or "-"
            })

        # ❌ Expired if no games remaining
        games_remaining = getattr(hockey_pass, "games_remaining", None) or getattr(hockey_pass, "uses_remaining", None)
        if games_remaining == 0 and redemptions:
            history["expired"] = utc_to_local(redemptions[-1].date_used).strftime(DATETIME_FORMAT)

        return history





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




def get_all_activity_logs():
    from models import Pass, Redemption, EmailLog, EbankPayment, ReminderLog, AdminActionLog, Signup
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

        # Admin Actions (e.g. Activity Created/Edited)
        for a in AdminActionLog.query.all():
            logs.append({
                "timestamp": utc_to_local(a.timestamp).strftime(DATETIME_FORMAT),
                "type": "Admin Action",
                "user": a.admin_email or "-",
                "details": a.action
            })

        # User Signups
        for s in Signup.query.all():
            logs.append({
                "timestamp": utc_to_local(s.signed_up_at).strftime(DATETIME_FORMAT),
                "type": "Signup Submitted",
                "user": s.user.name if s.user else "-",
                "details": f"Activity: {s.activity.name if s.activity else '-'}"
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





def strip_html_tags(html):
    return re.sub('<[^<]+?>', '', html)





def send_email(subject, to_email, template_name=None, context=None, inline_images=None, intro_text=None, conclusion_text=None, html_body=None, timestamp_override=None):
    from flask import current_app, render_template
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    from email.utils import formataddr
    from premailer import transform
    import logging
    from utils import get_setting

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["To"] = to_email

    from_email = get_setting("MAIL_DEFAULT_SENDER") or "noreply@minipass.me"
    msg["From"] = formataddr(("Minipass", from_email))

    context = context or {}
    inline_images = inline_images or {}

    # 🧪 Determine whether to use rendered HTML or template rendering
    if html_body:
        final_html = html_body
    else:
        final_html = render_template(f"email_templates/{template_name}", intro_text=intro_text, conclusion_text=conclusion_text, **context)

    final_html = transform(final_html)
    plain_text = "Votre passe numérique est prête."

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(plain_text, "plain"))
    alt_part.attach(MIMEText(final_html, "html"))
    msg.attach(alt_part)

    for cid, img_data in inline_images.items():
        if img_data:
            try:
                part = MIMEImage(img_data)
                part.add_header("Content-ID", f"<{cid}>")
                part.add_header("Content-Disposition", "inline", filename=f"{cid}.png")
                msg.attach(part)
            except Exception as e:
                logging.error(f"❌ Image embed error for {cid}: {e}")

    try:
        smtp_host = get_setting("MAIL_SERVER")
        smtp_port = int(get_setting("MAIL_PORT", 587))
        smtp_user = get_setting("MAIL_USERNAME")
        smtp_pass = get_setting("MAIL_PASSWORD")
        use_tls = str(get_setting("MAIL_USE_TLS") or "true").lower() == "true"

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        if use_tls:
            server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)

        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        logging.info(f"✅ Email sent to {to_email} with subject '{subject}'")

    except Exception as e:
        logging.exception(f"❌ Failed to send email to {to_email}: {e}")




def send_unpaid_reminders(app):
    from utils import get_setting, notify_pass_event
    from models import ReminderLog, Pass, db
    from datetime import datetime, timedelta, timezone

    def ensure_utc_aware(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    with app.app_context():
        try:
            days = float(get_setting("CALL_BACK_DAYS", "15"))
        except ValueError:
            print("❌ Invalid CALL_BACK_DAYS value. Defaulting to 15.")
            days = 15

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        unpaid_passes = Pass.query.filter(
            Pass.paid_ind == False,
            Pass.pass_created_dt <= cutoff_date
        ).all()

        for p in unpaid_passes:
            recent_reminder = ReminderLog.query.filter_by(pass_id=p.id)\
                .order_by(ReminderLog.reminder_sent_at.desc())\
                .first()

            if recent_reminder and ensure_utc_aware(recent_reminder.reminder_sent_at) > datetime.now(timezone.utc) - timedelta(days=days):
                print(f"⏳ Skipping reminder: {p.user_name} (already reminded)")
                continue

            print(f"📬 Sending reminder to: {p.user_email}")

            # 📧 Notify using visual email
            notify_pass_event(
                app=app,
                event_type="payment_late",  # ✅ FIXED
                hockey_pass=p,
                admin_email="auto-reminder@system",
                timestamp=datetime.now(timezone.utc)
            )



            db.session.add(ReminderLog(
                pass_id=p.id,
                reminder_sent_at=datetime.now(timezone.utc)
            ))
            db.session.commit()
            print(f"✅ Logged reminder for: {p.user_name}")




def match_gmail_payments_to_passes():
    from utils import extract_interac_transfers, get_setting, notify_pass_event
    from models import EbankPayment, Pass, db
    from datetime import datetime, timezone
    from flask import current_app
    from rapidfuzz import fuzz
    import imaplib

    with current_app.app_context():
        user = get_setting("MAIL_USERNAME")
        pwd = get_setting("MAIL_PASSWORD")

        if not user or not pwd:
            print("❌ MAIL_USERNAME or MAIL_PASSWORD is not set.")
            return

        threshold = int(get_setting("BANK_EMAIL_NAME_CONFIDANCE", "85"))
        gmail_label = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "InteractProcessed")

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, pwd)
        mail.select("inbox")

        matches = extract_interac_transfers(user, pwd, mail)

        for match in matches:
            name = match["bank_info_name"]
            amt = match["bank_info_amt"]
            from_email = match.get("from_email")
            uid = match.get("uid")
            subject = match["subject"]

            best_score = 0
            best_pass = None
            unpaid_passes = Pass.query.filter_by(paid_ind=False).all()

            for p in unpaid_passes:
                score = fuzz.partial_ratio(name.lower(), p.user_name.lower())
                if score >= threshold and abs(p.sold_amt - amt) < 1:
                    if score > best_score:
                        best_score = score
                        best_pass = p

            if best_pass:
                now_utc = datetime.now(timezone.utc)
                best_pass.paid_ind = True
                best_pass.paid_date = now_utc
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
                    note=f"Matched by Gmail Bot."
                ))

                db.session.commit()


                notify_pass_event(
                    app=current_app._get_current_object(),
                    event_type="payment_received",   
                    hockey_pass=best_pass,
                    admin_email="gmail-bot@system",
                    timestamp=now_utc
                )



                if uid:
                    mail.uid("COPY", uid, gmail_label)
                    mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
            else:
                db.session.add(EbankPayment(
                    from_email=from_email,
                    subject=subject,
                    bank_info_name=name,
                    bank_info_amt=amt,
                    name_score=0,
                    result="NO_MATCH",
                    mark_as_paid=False,
                    note="No matching pass found."
                ))

        db.session.commit()
        mail.expunge()
        mail.logout()




def render_and_send_email(
    app,
    *,
    user,
    subject_key,
    title_key,
    intro_key,
    conclusion_key,
    theme_key,
    context_extra=None,
    to_email=None,
    timestamp=None
):
    from utils import get_setting, send_email_async
    from flask import url_for
    from datetime import datetime, timezone
    import os

    timestamp = timestamp or datetime.now(timezone.utc)

    subject = get_setting(subject_key)
    title = get_setting(title_key)
    intro = get_setting(intro_key)
    conclusion = get_setting(conclusion_key)

    template_name = get_setting(theme_key) or "confirmation.html"

    # ✅ Convert theme like 'signup.html' to compiled version 'signup_compiled/index.html'
    if template_name.endswith(".html"):
        template_name = template_name.replace(".html", "_compiled/index.html")



    logo_path = "static/uploads/logo.png"
    inline_images = {
        "logo_image": open(logo_path, "rb").read() if os.path.exists(logo_path) else None
    }

 
    context = {
        "user_name": user.name,
        "user_email": user.email,
        "logo_url": url_for("static", filename="uploads/logo.png"),
        "title": title
    }

 

    if context_extra:
        context.update(context_extra)

    send_email_async(
        app,
        subject=subject,
        to_email=to_email or user.email,
        template_name=template_name,
        context=context,
        inline_images=inline_images,
        timestamp_override=timestamp
    )



def notify_signup_event(app, *, signup, activity, timestamp=None):
    from utils import render_and_send_email

    context_extra = {
        "activity_name": activity.name,
        "activity_price": f"${activity.price_per_user:.2f}",
        "sessions_included": activity.sessions_included,
        "payment_instructions": activity.payment_instructions
    }

    render_and_send_email(
        app,
        user=signup.user,
        subject_key="SUBJECT_signup",
        title_key="TITLE_signup",
        intro_key="INTRO_signup",
        conclusion_key="CONCLUSION_signup",
        theme_key="THEME_signup",
        context_extra=context_extra,
        timestamp=timestamp
    )
