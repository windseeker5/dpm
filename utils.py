import smtplib
import qrcode
import base64
import io
import socket
import traceback

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# from models import Setting, db, Pass, Redemption, Admin, EbankPayment, ReminderLog
from models import Setting, db, Passport, Redemption, Admin, EbankPayment, ReminderLog, Organization




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
import uuid


def get_gravatar_url(email, size=64):
    """
    Generate Gravatar URL for email address with identicon fallback
    
    Args:
        email (str): User's email address
        size (int): Size of the avatar image (default: 64)
    
    Returns:
        str: Gravatar URL
    """
    import hashlib
    
    if not email:
        email = 'unknown@example.com'
    
    # Create MD5 hash of lowercase email
    email_hash = hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()
    
    # Return Gravatar URL with identicon fallback
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"


def utc_to_local(dt_utc):
    if not dt_utc:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = utc.localize(dt_utc)

    eastern = pytz_timezone("America/Toronto")
    return dt_utc.astimezone(eastern)



def get_setting(key, default=""):
    """
    Legacy function for backwards compatibility.
    New code should use SettingsManager.get() instead.
    """
    with current_app.app_context():
        try:
            from models.settings import SettingsManager
            return SettingsManager.get(key, default)
        except ImportError:
            # Fallback to old method if new settings system not available
            setting = Setting.query.filter_by(key=key).first()
            if setting and setting.value not in [None, ""]:
                return setting.value
            return default



def save_setting(key, value, changed_by=None, change_reason=None):
    """
    Legacy function for backwards compatibility.
    New code should use SettingsManager.set() instead.
    """
    with current_app.app_context():
        try:
            from models.settings import SettingsManager
            from flask import request
            
            request_info = None
            if request:
                request_info = {
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent')
                }
            
            return SettingsManager.set(
                key, value, 
                changed_by=changed_by or 'legacy_function',
                change_reason=change_reason or 'Legacy save_setting call',
                request_info=request_info
            )
        except ImportError:
            # Fallback to old method if new settings system not available
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value)
                db.session.add(setting)
            db.session.commit()
            return value



def generate_pass_code():
    """
    Securely generates a random Pass Code for passports.
    Example Output: MP-8ab94c7efb29
    """
    return f"MP-{str(uuid.uuid4()).replace('-', '')[:12]}"



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
        else:
            redemptions = (
                Redemption.query
                .filter_by(passport_id=hockey_pass.id)
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
        paid_date = getattr(hockey_pass, "paid_date", None)  # ✅ Always get paid_date

        if paid and paid_date:
            paid_dt = utc_to_local(paid_date)
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
            # Get IMAP server from settings, same logic as in match_gmail_payments_to_passes
            imap_server = get_setting("IMAP_SERVER")
            if not imap_server:
                mail_server = get_setting("MAIL_SERVER")
                if mail_server:
                    imap_server = mail_server
                else:
                    imap_server = "imap.gmail.com"
            
            try:
                mail = imaplib.IMAP4_SSL(imap_server)
            except:
                mail = imaplib.IMAP4(imap_server, 143)
                mail.starttls()
            
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






def get_kpi_stats(activity_id=None):
    from datetime import datetime, timedelta, timezone
    from models import Passport, Signup
    from flask import current_app
    import math

    with current_app.app_context():
        now = datetime.now(timezone.utc)

        def build_daily_series(model, date_attr, filter_fn=None, days=7, aggregate_fn=None):
            """Build a daily series with proper data validation"""
            import math
            trend = []
            for i in reversed(range(days)):
                try:
                    start = now - timedelta(days=i+1)
                    end = now - timedelta(days=i)
                    query = model.query.filter(getattr(model, date_attr) >= start, getattr(model, date_attr) < end)
                    
                    # Add activity filter if activity_id is provided
                    if activity_id and hasattr(model, 'activity_id'):
                        query = query.filter(model.activity_id == activity_id)
                    
                    if filter_fn:
                        query = query.filter(filter_fn)
                    
                    if aggregate_fn:
                        # Use custom aggregation function (e.g., sum revenue)
                        result = aggregate_fn(query.all())
                    else:
                        # Default to count
                        result = query.count()
                    
                    # Validate the result
                    if result is None or (isinstance(result, float) and (math.isnan(result) or math.isinf(result))):
                        result = 0
                    elif isinstance(result, (int, float)):
                        result = round(float(result), 2)
                    else:
                        result = 0
                        
                    trend.append(result)
                except Exception as e:
                    print(f"Error building daily series for day {i}: {e}")
                    trend.append(0)
            return trend
        
        def build_revenue_series(days=7):
            """Build daily revenue series from paid passports using paid_date with data validation"""
            import math
            trend = []
            for i in reversed(range(days)):
                try:
                    start = now - timedelta(days=i+1)
                    end = now - timedelta(days=i)
                    # Use paid_date for accurate revenue tracking, fallback to created_dt if null
                    query = Passport.query.filter(Passport.paid == True)
                    
                    # Add activity filter if activity_id is provided
                    if activity_id:
                        query = query.filter(Passport.activity_id == activity_id)
                    
                    passports = query.filter(
                        db.or_(
                            db.and_(Passport.paid_date.isnot(None), Passport.paid_date >= start, Passport.paid_date < end),
                            db.and_(Passport.paid_date.is_(None), Passport.created_dt >= start, Passport.created_dt < end)
                        )
                    ).all()
                    
                    # Calculate daily revenue with validation
                    daily_revenue = 0
                    for p in passports:
                        if p.sold_amt is not None:
                            try:
                                amount = float(p.sold_amt)
                                if not (math.isnan(amount) or math.isinf(amount)):
                                    daily_revenue += amount
                            except (TypeError, ValueError):
                                continue
                    
                    trend.append(round(daily_revenue, 2))
                except Exception as e:
                    print(f"Error building revenue series for day {i}: {e}")
                    trend.append(0.0)
            return trend

        ranges = {
            "7d": (now - timedelta(days=7), now, 7),
            "30d": (now - timedelta(days=30), now, 30),
            "90d": (now - timedelta(days=90), now, 90),
            "all": (datetime.min.replace(tzinfo=timezone.utc), now, 30),
        }
        previous_ranges = {
            "7d": (now - timedelta(days=14), now - timedelta(days=7)),
            "30d": (now - timedelta(days=60), now - timedelta(days=30)),
            "90d": (now - timedelta(days=180), now - timedelta(days=90)),
            "all": (datetime.min.replace(tzinfo=timezone.utc), now),
        }

        kpis = {}

        for label, (start, end, trend_days) in ranges.items():
            prev_start, prev_end = previous_ranges[label]

            # Get current period paid passports using paid_date (with fallback to created_dt)
            current_revenue_query = Passport.query.filter(Passport.paid == True)
            if activity_id:
                current_revenue_query = current_revenue_query.filter(Passport.activity_id == activity_id)
            current_revenue_passports = current_revenue_query.filter(
                db.or_(
                    db.and_(Passport.paid_date.isnot(None), Passport.paid_date >= start, Passport.paid_date <= end),
                    db.and_(Passport.paid_date.is_(None), Passport.created_dt >= start, Passport.created_dt <= end)
                )
            ).all()
            
            # Get previous period paid passports using paid_date (with fallback to created_dt)
            previous_revenue_query = Passport.query.filter(Passport.paid == True)
            if activity_id:
                previous_revenue_query = previous_revenue_query.filter(Passport.activity_id == activity_id)
            previous_revenue_passports = previous_revenue_query.filter(
                db.or_(
                    db.and_(Passport.paid_date.isnot(None), Passport.paid_date >= prev_start, Passport.paid_date <= prev_end),
                    db.and_(Passport.paid_date.is_(None), Passport.created_dt >= prev_start, Passport.created_dt <= prev_end)
                )
            ).all()
            
            # For other metrics, use created_dt as they track passport creation, not revenue
            current_passports_query = Passport.query.filter(Passport.created_dt >= start, Passport.created_dt <= end)
            previous_passports_query = Passport.query.filter(Passport.created_dt >= prev_start, Passport.created_dt <= prev_end)
            if activity_id:
                current_passports_query = current_passports_query.filter(Passport.activity_id == activity_id)
                previous_passports_query = previous_passports_query.filter(Passport.activity_id == activity_id)
            current_passports = current_passports_query.all()
            previous_passports = previous_passports_query.all()

            def revenue_total(passports): return sum(p.sold_amt for p in passports if p.sold_amt is not None)
            def created(passports): return len(passports)
            def active(passports): return len([p for p in passports if p.uses_remaining > 0])
            def pending_signups_count(): 
                query = Signup.query.filter(Signup.status == "pending", Signup.signed_up_at >= start, Signup.signed_up_at <= end)
                if activity_id:
                    query = query.filter(Signup.activity_id == activity_id)
                return query.count()

            # Helper function to safely calculate percentage changes
            def safe_percentage_change(current, previous):
                """Calculate percentage change with validation"""
                try:
                    if previous is None or previous == 0:
                        return 0
                    if current is None:
                        current = 0
                    change = ((current - previous) / previous) * 100
                    return round(change, 1) if not (math.isnan(change) or math.isinf(change)) else 0
                except (TypeError, ValueError, ZeroDivisionError):
                    return 0
            
            # Calculate percentage changes with validation
            current_revenue = revenue_total(current_revenue_passports)
            previous_revenue = revenue_total(previous_revenue_passports)
            revenue_change = safe_percentage_change(current_revenue, previous_revenue)
            
            current_active = active(current_passports)
            previous_active = active(previous_passports)
            passport_change = safe_percentage_change(current_active, previous_active)
            
            current_created = created(current_passports)
            previous_created = created(previous_passports)
            new_passports_change = safe_percentage_change(current_created, previous_created)
            
            prev_signups_query = Signup.query.filter(Signup.status == "pending", Signup.signed_up_at >= prev_start, Signup.signed_up_at <= prev_end)
            if activity_id:
                prev_signups_query = prev_signups_query.filter(Signup.activity_id == activity_id)
            prev_signups = prev_signups_query.count()
            current_signups = pending_signups_count()
            signup_change = safe_percentage_change(current_signups, prev_signups)
            
            # Helper function to safely round numbers
            def safe_round(value, decimals=2):
                """Safely round numbers, handling None and invalid values"""
                try:
                    if value is None:
                        return 0
                    num_val = float(value)
                    return round(num_val, decimals) if not (math.isnan(num_val) or math.isinf(num_val)) else 0
                except (TypeError, ValueError):
                    return 0
            
            kpis[label] = {
                "revenue": safe_round(current_revenue, 2),
                "revenue_prev": safe_round(previous_revenue, 2),
                "revenue_change": revenue_change,
                "pass_created": max(0, int(current_created)),
                "pass_created_prev": max(0, int(previous_created)),
                "new_passports_change": new_passports_change,
                "active_users": max(0, int(current_active)),
                "active_users_prev": max(0, int(previous_active)),
                "passport_change": passport_change,
                "pending_signups": max(0, int(current_signups)),
                "signup_change": signup_change,
                # Real trend arrays - use proper functions
                "revenue_trend": build_revenue_series(trend_days),
                "active_users_trend": build_daily_series(Passport, "created_dt", lambda: Passport.uses_remaining > 0, trend_days),
                "pass_created_trend": build_daily_series(Passport, "created_dt", None, trend_days),
                "pending_signups_trend": build_daily_series(Signup, "signed_up_at", lambda: Signup.status == "pending", trend_days)
            }

        return kpis





def send_unpaid_reminders(app):
    from utils import get_setting, notify_pass_event
    from models import ReminderLog, Passport, db
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

        unpaid_passports = Passport.query.filter(
            Passport.paid == False,
            Passport.created_dt <= cutoff_date
        ).all()

        for p in unpaid_passports:
            recent_reminder = ReminderLog.query.filter_by(pass_id=p.id)\
                .order_by(ReminderLog.reminder_sent_at.desc())\
                .first()

            if recent_reminder and ensure_utc_aware(recent_reminder.reminder_sent_at) > datetime.now(timezone.utc) - timedelta(days=days):
                print(f"⏳ Skipping reminder: {p.user.name if p.user else '-'} (already reminded)")
                continue

            # ✅ Log the reminder FIRST
            db.session.add(ReminderLog(
                pass_id=p.id,
                reminder_sent_at=datetime.now(timezone.utc)
            ))
            db.session.commit()
            print(f"✅ Logged late reminder for: {p.user.name if p.user else '-'}")

            # ✅ THEN send reminder email
            print(f"📬 Sending reminder to: {p.user.email if p.user else 'N/A'}")
            notify_pass_event(
                app=app,
                event_type="payment_late",
                pass_data=p,  # using new models
                admin_email="auto-reminder@system",
                timestamp=datetime.now(timezone.utc)
            )





def match_gmail_payments_to_passes():
    from utils import extract_interac_transfers, get_setting, notify_pass_event
    from models import EbankPayment, Passport, db
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
        processed_folder = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "PaymentProcessed")

        # Get IMAP server from settings, fallback to MAIL_SERVER or Gmail
        imap_server = get_setting("IMAP_SERVER")
        if not imap_server:
            mail_server = get_setting("MAIL_SERVER")
            if mail_server:
                # Try to use the mail server for IMAP (often works for custom domains)
                imap_server = mail_server
            else:
                # Fallback to Gmail for backward compatibility
                imap_server = "imap.gmail.com"
        
        print(f"🔌 Connecting to IMAP server: {imap_server}")
        
        try:
            # Try SSL connection first (port 993)
            mail = imaplib.IMAP4_SSL(imap_server)
        except:
            # If SSL fails, try TLS (port 143)
            print(f"⚠️ SSL connection failed, trying TLS...")
            mail = imaplib.IMAP4(imap_server, 143)
            mail.starttls()
        
        mail.login(user, pwd)
        mail.select("inbox")

        matches = extract_interac_transfers(user, pwd, mail)
        
        print(f"🔍 DEBUG: Found {len(matches)} email matches")
        for i, match in enumerate(matches):
            print(f"🔍 Email {i+1}: {match.get('subject', 'No subject')[:50]}...")

        for match in matches:
            name = match["bank_info_name"]
            amt = match["bank_info_amt"]
            from_email = match.get("from_email")
            uid = match.get("uid")
            subject = match["subject"]
            
            print(f"🔍 Processing payment: Name='{name}', Amount=${amt}, From={from_email}")

            best_score = 0
            best_passport = None
            unpaid_passports = Passport.query.filter_by(paid=False).all()
            
            print(f"🔍 Found {len(unpaid_passports)} unpaid passports to match against")

            for p in unpaid_passports:
                if not p.user:
                    continue  # Safety check
                score = fuzz.partial_ratio(name.lower(), p.user.name.lower())
                print(f"🔍 Checking passport: User='{p.user.name}', Amount=${p.sold_amt}, Score={score} (threshold={threshold})")
                if score >= threshold and abs(p.sold_amt - amt) < 1:
                    print(f"✅ MATCH FOUND! Score={score}, Amount match: ${p.sold_amt} ≈ ${amt}")
                    if score > best_score:
                        best_score = score
                        best_passport = p
                else:
                    if score < threshold:
                        print(f"❌ Score too low: {score} < {threshold}")
                    if abs(p.sold_amt - amt) >= 1:
                        print(f"❌ Amount mismatch: ${p.sold_amt} vs ${amt} (diff: ${abs(p.sold_amt - amt)})")

            if best_passport:
                print(f"🎯 PROCESSING MATCH: {best_passport.user.name} - ${best_passport.sold_amt}")
            else:
                print(f"❌ NO MATCH FOUND for payment: Name='{name}', Amount=${amt}")
                
            if best_passport:
                now_utc = datetime.now(timezone.utc)
                best_passport.paid = True
                best_passport.paid_date = now_utc
                db.session.add(best_passport)

                db.session.add(EbankPayment(
                    from_email=from_email,
                    subject=subject,
                    bank_info_name=name,
                    bank_info_amt=amt,
                    matched_pass_id=best_passport.id,
                    matched_name=best_passport.user.name,
                    matched_amt=best_passport.sold_amt,
                    name_score=best_score,
                    result="MATCHED",
                    mark_as_paid=True,
                    note="Matched by Gmail Bot."
                ))

                db.session.commit()

                notify_pass_event(
                    app=current_app._get_current_object(),
                    event_type="payment_received",
                    pass_data=best_passport,  # ✅ update keyword
                    admin_email="gmail-bot@system",
                    timestamp=now_utc
                )

                # Emit SSE notification for payment
                try:
                    from api.notifications import emit_payment_notification
                    emit_payment_notification(best_passport)
                except Exception as e:
                    print(f"⚠️ Failed to emit payment notification: {e}")

                if uid:
                    # Check if the processed folder exists, create if needed
                    try:
                        # List all folders to check if our processed folder exists
                        folder_exists = False
                        result, folder_list = mail.list()
                        if result == 'OK':
                            for folder_info in folder_list:
                                if folder_info:
                                    # Parse folder name from IMAP list response
                                    folder_str = folder_info.decode() if isinstance(folder_info, bytes) else folder_info
                                    # Check if our folder name appears in the response
                                    if processed_folder in folder_str:
                                        folder_exists = True
                                        break
                        
                        # Create folder if it doesn't exist
                        if not folder_exists:
                            print(f"📁 Creating folder: {processed_folder}")
                            try:
                                mail.create(processed_folder)
                            except Exception as create_error:
                                # Some servers don't allow folder creation or folder already exists
                                print(f"⚠️ Could not create folder {processed_folder}: {create_error}")
                        
                        # Try to copy the email to the processed folder
                        copy_result = mail.uid("COPY", uid, processed_folder)
                        if copy_result[0] == 'OK':
                            # Only mark as deleted if copy was successful
                            mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                            print(f"✅ Email moved to {processed_folder} folder")
                        else:
                            print(f"⚠️ Could not copy email to {processed_folder}: {copy_result}")
                            # Don't delete if we couldn't copy
                            
                    except Exception as e:
                        print(f"⚠️ Error moving email to processed folder: {e}")
                        # Don't delete the email if we couldn't move it
            else:
                db.session.add(EbankPayment(
                    from_email=from_email,
                    subject=subject,
                    bank_info_name=name,
                    bank_info_amt=amt,
                    name_score=0,
                    result="NO_MATCH",
                    mark_as_paid=False,
                    note="No matching passport found."
                ))

        db.session.commit()
        mail.expunge()
        mail.logout()




def strip_html_tags(html):
    return re.sub('<[^<]+?>', '', html)



# ✅ Log admin action centrally
def log_admin_action(action: str):
    from models import AdminActionLog, db
    from flask import session

    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=action
    ))
    db.session.commit()




def get_all_activity_logs():
    from models import Passport, Redemption, EmailLog, EbankPayment, ReminderLog, AdminActionLog, Signup
    from utils import utc_to_local
    from flask import current_app

    logs = []

    with current_app.app_context():
        # 🟢 Admin Actions (Passport Created, Activity Created, etc.)
        for a in AdminActionLog.query.all():
            action_text = a.action.lower()

            if "passport created" in action_text:
                log_type = "Passport Created"
            elif "passport" in action_text and "redeemed" in action_text:
                log_type = "Passport Redeemed"
            elif "marked" in action_text and "paid" in action_text:
                log_type = "Marked Paid"
            elif "approved" in action_text and "signup" in action_text:
                log_type = "Signup Approved"
            elif "rejected" in action_text and "signup" in action_text:
                log_type = "Signup Rejected"
            elif "cancelled" in action_text and "signup" in action_text:
                log_type = "Signup Cancelled"  # ✅ NEW detection for cancelled
            elif "activity created" in action_text:
                log_type = "Activity Created"
            else:
                log_type = "Admin Action"

            # ✅ Add "by admin" only if not already in the text
            if "by" not in a.action.lower():
                details = f"{a.action} by {a.admin_email or '-'}"
            else:
                details = a.action

            logs.append({
                "timestamp": a.timestamp,
                "type": log_type,
                "user": a.admin_email or "-",
                "details": details
            })

        # 🟠 Email Sent
        for e in EmailLog.query.all():
            pass_code_display = e.pass_code if e.pass_code else "App-Sent"
            logs.append({
                "timestamp": e.timestamp,
                "type": "Email Sent",
                "user": e.to_email,
                "details": f"To {e.to_email} — \"{e.subject}\" (Code: {pass_code_display})"
            })

        # 🔵 Payments
        for p in EbankPayment.query.all():
            if p.result == "MATCHED":
                log_type = "Interact Payment"
                details = f"From {p.matched_name}, Amount: {p.bank_info_amt:.2f}, Passport ID: {p.matched_pass_id}"
            else:
                log_type = "Payment No Match"
                details = f"From {p.bank_info_name}, Amount: {p.bank_info_amt:.2f}"

            logs.append({
                "timestamp": p.timestamp,
                "type": log_type,
                "user": p.from_email or "-",
                "details": details
            })


        # 🟣 Reminders
        for r in ReminderLog.query.all():
            from models import Passport
            passport = db.session.get(Passport, r.pass_id)

            user_name = passport.user.name if passport and passport.user else "-"
            activity_name = passport.activity.name if passport and passport.activity else "-"

            logs.append({
                "timestamp": r.reminder_sent_at,
                "type": "Late Reminder Detected",
                "user": "auto-reminder@system",
                "details": f"Late payment detected for {user_name} for Activity '{activity_name}' by App Bot"
            })



        # 🧡 User Signups
        for s in Signup.query.all():
            user_name = s.user.name if s.user else "-"
            activity_name = s.activity.name if s.activity else "-"
            logs.append({
                "timestamp": s.signed_up_at,
                "type": "Signup Submitted",
                "user": user_name,
                "details": f"User {user_name} signed up for Activity '{activity_name}' from online form"
            })

    # 📈 Sort newest first
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return logs






##
## EMAIL STUFF
##

def safe_template(template_name: str) -> str:
    """
    Corrects template path.
    - If a compiled version exists, redirect to compiled/index.html.
    - If a folder with index.html exists, redirect to folder/index.html.
    - Otherwise normal path.
    """

    template_name = template_name.lstrip("/")
    base_name = template_name.replace(".html", "")

    # Check if compiled version exists
    compiled_folder = os.path.join("templates", "email_templates", f"{base_name}_compiled", "index.html")
    if os.path.exists(compiled_folder):
        return f"email_templates/{base_name}_compiled/index.html"

    # Check if folder with index.html exists
    folder_index = os.path.join("templates", "email_templates", base_name, "index.html")
    if os.path.exists(folder_index):
        return f"email_templates/{base_name}/index.html"

    # Otherwise fallback normal
    if not template_name.startswith("email_templates/"):
        return f"email_templates/{template_name}"
    return template_name


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
    timestamp=None,
    activity=None,
    organization_id=None
):
    from utils import get_setting, send_email_async
    from flask import url_for, render_template_string
    from datetime import datetime, timezone
    import os
    import json
    import base64

    timestamp = timestamp or datetime.now(timezone.utc)

    subject = get_setting(subject_key)
    title = get_setting(title_key)
    intro = get_setting(intro_key)
    conclusion = get_setting(conclusion_key)

    template_name = get_setting(theme_key) or "confirmation.html"

    context = {
        "user_name": user.name,
        "user_email": user.email,
        "title": title,
        "intro_text": intro,
        "conclusion_text": conclusion,
    }

    if context_extra:
        context.update(context_extra)

    inline_images = {}
    final_html = None

    # 🧠 Detect compiled email (ex: signup)
    if template_name.endswith(".html"):
        compiled_folder = template_name.replace(".html", "_compiled")
        compiled_index_path = os.path.join("app", "templates", "email_templates", compiled_folder, "index.html")
        inline_images_json_path = os.path.join("app", "templates", "email_templates", compiled_folder, "inline_images.json")

        if os.path.exists(compiled_index_path):
            # ✅ Read and render compiled index.html
            with open(compiled_index_path, "r", encoding="utf-8") as f:
                raw_html = f.read()

            final_html = render_template_string(raw_html, **context)

            # ✅ Load compiled inline images if any
            if os.path.exists(inline_images_json_path):
                with open(inline_images_json_path, "r", encoding="utf-8") as f:
                    cid_map = json.load(f)
                for cid, img_base64 in cid_map.items():
                    inline_images[cid] = base64.b64decode(img_base64)

    # 🧠 Fallback for non-compiled (classic templates)
    if not final_html:
        logo_path = os.path.join("static", "uploads", "logo.png")
        if os.path.exists(logo_path):
            inline_images["logo_image"] = open(logo_path, "rb").read()
            context["logo_url"] = url_for("static", filename="uploads/logo.png")

    # 🛡️ Finally SEND

    if final_html:
        send_email_async(
            app=app,
            user=user,
            activity=activity,
            organization_id=organization_id,
            subject=subject,
            to_email=to_email or user.email,
            html_body=final_html,
            inline_images=inline_images if inline_images else None,
            timestamp_override=timestamp
        )
    else:
        send_email_async(
            app=app,
            user=user,
            activity=activity,
            organization_id=organization_id,
            subject=subject,
            to_email=to_email or user.email,
            template_name=template_name,
            context=context,
            inline_images=inline_images if inline_images else None,
            timestamp_override=timestamp
        )


def send_email(subject, to_email, template_name=None, context=None, inline_images=None, html_body=None, timestamp_override=None, email_config=None):
    from flask import render_template
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    from email.utils import formataddr
    from premailer import transform
    import logging
    from utils import get_setting, safe_template
    from datetime import datetime

    context = context or {}
    inline_images = inline_images or {}

    # 🛡️ FINAL FIX: Render properly depending on whether html_body is given
    if html_body:
        final_html = html_body
    else:
        if template_name and context:
            final_html = render_template(safe_template(template_name), **context)
        else:
            final_html = "No content."

    # 🧠 Inline CSS
    final_html = transform(final_html)

    # Build email
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["To"] = to_email

    from_email = get_setting("MAIL_DEFAULT_SENDER") or "noreply@minipass.me"
    sender_name = get_setting("MAIL_SENDER_NAME") or "Minipass"
    msg["From"] = formataddr((sender_name, from_email))

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText("Votre passe numérique est prête.", "plain"))
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
        # Use provided email config or fall back to system settings
        if email_config:
            smtp_host = email_config['MAIL_SERVER']
            smtp_port = email_config['MAIL_PORT']
            smtp_user = email_config['MAIL_USERNAME']
            smtp_pass = decrypt_password(email_config['MAIL_PASSWORD']) if email_config['MAIL_PASSWORD'] else None
            use_tls = email_config.get('MAIL_USE_TLS', True)
            use_ssl = email_config.get('MAIL_USE_SSL', False)
            sender_name = email_config.get('SENDER_NAME', 'Minipass')
            
            # Update the From header with organization-specific sender
            from_email = email_config['MAIL_DEFAULT_SENDER']
            msg['From'] = formataddr((sender_name, from_email))
        else:
            # Fall back to system settings
            smtp_host = get_setting("MAIL_SERVER")
            smtp_port = int(get_setting("MAIL_PORT", 587))
            smtp_user = get_setting("MAIL_USERNAME")
            smtp_pass = get_setting("MAIL_PASSWORD")
            use_tls = str(get_setting("MAIL_USE_TLS") or "true").lower() == "true"
            use_ssl = False

        # Choose connection type
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            
        server.ehlo()
        
        if use_tls and not use_ssl:
            server.starttls()
            
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)

        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        
        config_type = "organization-specific" if email_config else "system default"
        logging.info(f"✅ Email sent to {to_email} with subject '{subject}' using {config_type} configuration")

    except Exception as e:
        logging.exception(f"❌ Failed to send email to {to_email}: {e}")


def send_email_async(app, user=None, activity=None, organization_id=None, **kwargs):
    import threading
    def send_in_thread():
        with app.app_context():
            try:
                from utils import send_email
                from models import EmailLog
                import json
                from datetime import datetime, timezone

                # --- Extract arguments ---
                subject = kwargs.get("subject")
                to_email = kwargs.get("to_email")
                template_name = kwargs.get("template_name")
                context = kwargs.get("context", {})
                inline_images = kwargs.get("inline_images", {})
                html_body = kwargs.get("html_body")
                timestamp_override = kwargs.get("timestamp_override")

                # ✅ FINAL SAFETY: If html_body exists, force clear template_name/context
                if html_body:
                    template_name = None
                    context = {}

                # --- Send the email ---
                send_email(
                    subject=subject,
                    to_email=to_email,
                    template_name=template_name,
                    context=context,
                    inline_images=inline_images,
                    html_body=html_body,
                    timestamp_override=timestamp_override
                )

                # --- Save EmailLog after successful send ---
                def format_dt(dt):
                    return dt.strftime('%Y-%m-%d %H:%M') if isinstance(dt, datetime) else dt

                db.session.add(EmailLog(
                    to_email=to_email,
                    subject=subject,
                    pass_code=context.get("hockey_pass", {}).get("pass_code") if context else None,
                    template_name=template_name or "",
                    context_json=json.dumps({
                        "user_name": context.get("hockey_pass", {}).get("user_name") if context else None,
                        "created_date": format_dt(context.get("hockey_pass", {}).get("pass_created_dt")) if context else None,
                        "remaining_games": context.get("hockey_pass", {}).get("games_remaining") if context else None,
                        "special_message": context.get("special_message", "") if context else ""
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
                    pass_code=kwargs.get("context", {}).get("hockey_pass", {}).get("pass_code") if kwargs.get("context") else None,
                    template_name=kwargs.get("template_name") or "",
                    context_json=json.dumps({"error": str(e)}),
                    result="FAILED",
                    error_message=str(e),
                    timestamp=kwargs.get("timestamp_override") or datetime.now(timezone.utc)
                ))
                db.session.commit()

    thread = threading.Thread(target=send_in_thread)
    thread.start()


def notify_signup_event(app, *, signup, activity, timestamp=None):
    from utils import send_email_async, get_setting
    from flask import render_template_string, url_for
    import os
    import json
    import base64
    from datetime import datetime, timezone

    timestamp = timestamp or datetime.now(timezone.utc)

    # 🧠 Same logic as notify_pass_event
    subject = get_setting("SUBJECT_signup", "Confirmation d'inscription")
    title = get_setting("TITLE_signup", "Votre Inscription est Confirmée")
    intro_raw = get_setting("INTRO_signup", "")
    conclusion_raw = get_setting("CONCLUSION_signup", "")
    theme = get_setting("THEME_signup", "signup.html")

    # Render intro and conclusion manually
    intro = render_template_string(intro_raw, user_name=signup.user.name, activity_name=activity.name)
    conclusion = render_template_string(conclusion_raw, user_name=signup.user.name, activity_name=activity.name)

    # Get passport type information if available
    passport_type = None
    if hasattr(signup, 'passport_type_id') and signup.passport_type_id:
        from models import PassportType
        passport_type = PassportType.query.get(signup.passport_type_id)
    
    # Build context
    context = {
        "user_name": signup.user.name,
        "user_email": signup.user.email,
        "phone_number": signup.user.phone_number,
        "activity_name": activity.name,
        "activity_price": f"${passport_type.price_per_user:.2f}" if passport_type else "$0.00",
        "sessions_included": passport_type.sessions_included if passport_type else 1,
        "payment_instructions": passport_type.payment_instructions if passport_type else "",
        "title": title,
        "intro_text": intro,
        "conclusion_text": conclusion,
        "logo_url": url_for("static", filename="uploads/logo.png"),
    }

    # Find compiled template
    compiled_folder = os.path.join("templates/email_templates", theme.replace(".html", "_compiled"))
    index_path = os.path.join(compiled_folder, "index.html")
    json_path = os.path.join(compiled_folder, "inline_images.json")
    use_compiled = os.path.exists(index_path) and os.path.exists(json_path)

    inline_images = {}

    if use_compiled:
        with open(index_path, "r", encoding="utf-8") as f:
            raw_html = f.read()
        html_body = render_template_string(raw_html, **context)

        with open(json_path, "r", encoding="utf-8") as f:
            cid_map = json.load(f)
        for cid, img_base64 in cid_map.items():
            inline_images[cid] = base64.b64decode(img_base64)

        send_email_async(
            app=app,
            user=signup.user,
            activity=activity,
            subject=subject,
            to_email=signup.user.email,
            html_body=html_body,
            inline_images=inline_images,
            timestamp_override=timestamp
        )

    else:
        # fallback if compiled missing
        send_email_async(
            app=app,
            user=signup.user,
            activity=activity,
            subject=subject,
            to_email=signup.user.email,
            template_name=theme,
            context=context,
            timestamp_override=timestamp
        )


def notify_pass_event(app, *, event_type, pass_data, admin_email=None, timestamp=None):
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
    games_remaining = getattr(pass_data, "games_remaining", None) or getattr(pass_data, "uses_remaining", 0)
    activity_display = getattr(pass_data, "activity", "")
    if hasattr(activity_display, "name"):
        activity_display = activity_display.name

    intro = render_template_string(intro_raw, pass_data=pass_data, default_qt=games_remaining, activity_list=activity_display)
    conclusion = render_template_string(conclusion_raw, pass_data=pass_data, default_qt=games_remaining, activity_list=activity_display)

    print("🔔 Email debug - subject:", subject)
    print("🔔 Email debug - title:", title)
    print("🔔 Email debug - intro:", intro[:80])

    qr_data = generate_qr_code_image(pass_data.pass_code).read()
    history = get_pass_history_data(pass_data.pass_code, fallback_admin_email=admin_email)

    context = {
        "pass_data": {
            "pass_code": pass_data.pass_code,
            "user_name": getattr(pass_data, "user_name", None) or getattr(getattr(pass_data, "user", None), "name", ""),
            "activity": activity_display,
            "games_remaining": games_remaining,
            "sold_amt": pass_data.sold_amt,
            "user_email": getattr(pass_data, "user_email", None) or getattr(getattr(pass_data, "user", None), "email", ""),
            "phone_number": getattr(pass_data, "phone_number", None) or getattr(getattr(pass_data, "user", None), "phone_number", ""),
            "pass_created_dt": getattr(pass_data, "pass_created_dt", getattr(pass_data, "created_dt", None)),
            "paid_ind": getattr(pass_data, "paid_ind", getattr(pass_data, "paid", False))
        },
        "title": title,
        "intro_text": intro,
        "conclusion_text": conclusion,
        "owner_html": render_template("email_blocks/owner_card_inline.html", pass_data=pass_data),
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

        # Determine user and activity for email context
        user_obj = getattr(pass_data, "user", None)
        activity_obj = getattr(pass_data, "activity", None)
        
        send_email_async(
            app,
            user=user_obj,
            activity=activity_obj,
            subject=subject,
            to_email=getattr(pass_data, "user_email", None) or getattr(getattr(pass_data, "user", None), "email", None),
            html_body=html_body,
            inline_images=inline_images,
            timestamp_override=timestamp
        )
    else:
        inline_images = {
            "qr_code": qr_data,
            "logo_image": open("static/uploads/logo.png", "rb").read()
        }

        # Determine user and activity for email context
        user_obj = getattr(pass_data, "user", None)
        activity_obj = getattr(pass_data, "activity", None)
        
        send_email_async(
            app,
            user=user_obj,
            activity=activity_obj,
            subject=subject,
            to_email=pass_data.user_email,
            template_name=theme,
            context=context,
            inline_images=inline_images,
            timestamp_override=timestamp
        )


# ================================
# 📋 SURVEY UTILITIES
# ================================

def generate_survey_token():
    """Generate a secure random token for surveys"""
    import secrets
    return secrets.token_urlsafe(24)


def generate_response_token():
    """Generate a secure random token for survey responses"""
    import secrets
    return secrets.token_urlsafe(24)


# ================================
# 📧 ORGANIZATION EMAIL CONFIGURATION
# ================================

def get_email_config_for_context(user=None, activity=None, organization_id=None):
    """
    Determine the appropriate email configuration based on context.
    Priority: organization_id > activity.organization > user.organization > system default
    
    Args:
        user: User object
        activity: Activity object  
        organization_id: Direct organization ID
    
    Returns:
        dict: Email configuration or None for system default
    """
    from flask import current_app
    
    with current_app.app_context():
        # Priority 1: Direct organization_id
        if organization_id:
            org = Organization.query.get(organization_id)
            if org and org.email_enabled and org.is_active:
                return org.get_email_config()
        
        # Priority 2: Activity's organization
        if activity and hasattr(activity, 'organization') and activity.organization:
            if activity.organization.email_enabled and activity.organization.is_active:
                return activity.organization.get_email_config()
        
        # Priority 3: User's organization
        if user and hasattr(user, 'organization') and user.organization:
            if user.organization.email_enabled and user.organization.is_active:
                return user.organization.get_email_config()
        
        # Priority 4: System default (return None to use global settings)
        return None


def get_organization_by_domain(domain):
    """
    Get organization by domain name.
    
    Args:
        domain: Domain part of email (e.g., 'lhgi' from 'lhgi@minipass.me')
    
    Returns:
        Organization object or None
    """
    return Organization.query.filter_by(domain=domain, is_active=True).first()


def encrypt_password(password):
    """
    Encrypt password for secure storage.
    Using simple base64 encoding for now - in production should use proper encryption.
    """
    import base64
    if not password:
        return None
    return base64.b64encode(password.encode()).decode()


def decrypt_password(encrypted_password):
    """
    Decrypt stored password.
    Using simple base64 decoding for now - in production should use proper decryption.
    """
    import base64
    if not encrypted_password:
        return None
    try:
        return base64.b64decode(encrypted_password.encode()).decode()
    except:
        return None


def create_organization_email_config(name, domain, mail_server, mail_username, mail_password, 
                                    mail_sender_name=None, mail_port=587, mail_use_tls=True, 
                                    created_by=None):
    """
    Create a new organization with email configuration.
    
    Args:
        name: Organization name
        domain: Domain for email (without @minipass.me)
        mail_server: SMTP server
        mail_username: SMTP username
        mail_password: SMTP password (will be encrypted)
        mail_sender_name: Display name for sender
        mail_port: SMTP port (default 587)
        mail_use_tls: Use TLS (default True)
        created_by: Admin who created this config
    
    Returns:
        Organization object
    """
    from flask import current_app
    
    with current_app.app_context():
        # Check if organization with this domain already exists
        existing = Organization.query.filter_by(domain=domain).first()
        if existing:
            raise ValueError(f"Organization with domain '{domain}' already exists")
        
        # Create new organization
        org = Organization(
            name=name,
            domain=domain,
            email_enabled=True,
            mail_server=mail_server,
            mail_port=mail_port,
            mail_use_tls=mail_use_tls,
            mail_username=mail_username,
            mail_password=encrypt_password(mail_password),
            mail_sender_name=mail_sender_name,
            mail_sender_email=f"{domain}@minipass.me",
            is_active=True,
            fallback_to_system_email=True,
            created_by=created_by,
            updated_by=created_by
        )
        
        db.session.add(org)
        db.session.commit()
        
        return org


def update_organization_email_config(organization_id, **kwargs):
    """
    Update organization email configuration.
    
    Args:
        organization_id: ID of organization to update
        **kwargs: Fields to update
    
    Returns:
        Organization object
    """
    from flask import current_app
    
    with current_app.app_context():
        org = Organization.query.get(organization_id)
        if not org:
            raise ValueError(f"Organization with ID {organization_id} not found")
        
        # Update fields
        for field, value in kwargs.items():
            if field == 'mail_password' and value:
                value = encrypt_password(value)
            
            if hasattr(org, field):
                setattr(org, field, value)
        
        org.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return org


def test_organization_email_config(organization_id):
    """
    Test organization email configuration by attempting to connect to SMTP server.
    
    Args:
        organization_id: ID of organization to test
    
    Returns:
        tuple: (success: bool, message: str)
    """
    from flask import current_app
    import smtplib
    
    with current_app.app_context():
        org = Organization.query.get(organization_id)
        if not org or not org.email_enabled:
            return False, "Organization not found or email not enabled"
        
        config = org.get_email_config()
        if not config:
            return False, "Email configuration not available"
        
        try:
            # Test SMTP connection
            server = smtplib.SMTP(config['MAIL_SERVER'], config['MAIL_PORT'])
            server.ehlo()
            
            if config.get('MAIL_USE_TLS'):
                server.starttls()
            
            if config.get('MAIL_USERNAME') and config.get('MAIL_PASSWORD'):
                decrypted_password = decrypt_password(config['MAIL_PASSWORD'])
                server.login(config['MAIL_USERNAME'], decrypted_password)
            
            server.quit()
            return True, "Email configuration test successful"
            
        except Exception as e:
            return False, f"Email configuration test failed: {str(e)}"



