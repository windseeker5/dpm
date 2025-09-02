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






# OBSOLETE - Use get_kpi_data() instead. This function will be removed in future version.

def get_kpi_data(activity_id=None, period='7d'):
    """
    Optimized KPI data retrieval function with direct SQL queries.
    
    Args:
        activity_id: Optional activity ID for activity-specific KPIs (None for global)
        period: Time period - '7d', '30d', '90d', or 'all'
        
    Returns:
        dict: KPI data with current values, previous values, changes, and trends
    """
    from datetime import datetime, timedelta, timezone
    from models import Passport, Signup, Income, db
    from flask import current_app
    from sqlalchemy import func, and_, or_
    
    with current_app.app_context():
        now = datetime.now(timezone.utc)
        
        # Define time ranges
        if period == '7d':
            current_start = now - timedelta(days=7)
            prev_start = now - timedelta(days=14)
            prev_end = now - timedelta(days=7)
            trend_days = 7
        elif period == '30d':
            current_start = now - timedelta(days=30)
            prev_start = now - timedelta(days=60)
            prev_end = now - timedelta(days=30)
            trend_days = 30
        elif period == '90d':
            current_start = now - timedelta(days=90)
            prev_start = now - timedelta(days=180)
            prev_end = now - timedelta(days=90)
            trend_days = 30  # Show last 30 days for trend
        elif period == 'all':
            current_start = datetime.min.replace(tzinfo=timezone.utc)
            prev_start = None  # No comparison for 'all'
            prev_end = None
            trend_days = 30  # Show last 30 days for trend
        else:
            raise ValueError(f"Invalid period: {period}")
            
        current_end = now
        
        # Helper function to build base queries
        def get_base_passport_query():
            query = Passport.query
            if activity_id:
                query = query.filter(Passport.activity_id == activity_id)
            return query
            
        def get_base_signup_query():
            query = Signup.query
            if activity_id:
                query = query.filter(Signup.activity_id == activity_id)
            return query
            
        def get_base_income_query():
            query = Income.query
            if activity_id:
                query = query.filter(Income.activity_id == activity_id)
            return query
        
        # KPI 1: Revenue (all passport amounts + income amounts)
        # Current period revenue
        passport_revenue = get_base_passport_query().filter(
            Passport.created_dt >= current_start,
            Passport.created_dt <= current_end
        ).with_entities(func.sum(Passport.sold_amt)).scalar() or 0
        
        income_revenue = get_base_income_query().filter(
            Income.date >= current_start,
            Income.date <= current_end
        ).with_entities(func.sum(Income.amount)).scalar() or 0
        
        current_revenue = passport_revenue + income_revenue
        
        # Previous period revenue (if not 'all')
        if period != 'all':
            prev_passport_revenue = get_base_passport_query().filter(
                Passport.created_dt >= prev_start,
                Passport.created_dt <= prev_end
            ).with_entities(func.sum(Passport.sold_amt)).scalar() or 0
            
            prev_income_revenue = get_base_income_query().filter(
                Income.date >= prev_start,
                Income.date <= prev_end
            ).with_entities(func.sum(Income.amount)).scalar() or 0
            
            prev_revenue = prev_passport_revenue + prev_income_revenue
            if prev_revenue > 0:
                revenue_change = ((current_revenue - prev_revenue) / prev_revenue * 100)
            elif current_revenue > 0:
                revenue_change = 100.0  # New revenue, show as 100% increase
            else:
                revenue_change = 0
        else:
            prev_revenue = None
            revenue_change = None
        
        # KPI 2: Active Users (passports with uses_remaining > 0)
        current_active_users = get_base_passport_query().filter(
            Passport.uses_remaining > 0
        ).count()
        
        if period != 'all':
            # For active users, we need a snapshot comparison, not creation-based
            # This is complex to calculate historically, so we'll skip the comparison
            # Alternative: Track this in a separate daily snapshot table for accurate trends
            prev_active_users = None
            active_users_change = None
        else:
            prev_active_users = None
            active_users_change = None
        
        # KPI 3: Passports Created
        current_passports_created = get_base_passport_query().filter(
            Passport.created_dt >= current_start,
            Passport.created_dt <= current_end
        ).count()
        
        if period != 'all':
            prev_passports_created = get_base_passport_query().filter(
                Passport.created_dt >= prev_start,
                Passport.created_dt <= prev_end
            ).count()
            if prev_passports_created > 0:
                passports_created_change = ((current_passports_created - prev_passports_created) / prev_passports_created * 100)
            elif current_passports_created > 0:
                passports_created_change = 100.0  # New passports, show as 100% increase
            else:
                passports_created_change = 0
        else:
            prev_passports_created = None
            passports_created_change = None
        
        # KPI 4: Passports Unpaid
        current_unpaid = get_base_passport_query().filter(
            Passport.paid == False
        ).count()
        
        if period != 'all':
            # For unpaid, compare new unpaid passports created in each period
            prev_unpaid = get_base_passport_query().filter(
                Passport.created_dt >= prev_start,
                Passport.created_dt <= prev_end,
                Passport.paid == False
            ).count()
            
            # Also get current period new unpaid for fair comparison
            current_period_unpaid = get_base_passport_query().filter(
                Passport.created_dt >= current_start,
                Passport.created_dt <= current_end,
                Passport.paid == False
            ).count()
            
            if prev_unpaid > 0:
                unpaid_change = ((current_period_unpaid - prev_unpaid) / prev_unpaid * 100)
            elif current_period_unpaid > 0:
                unpaid_change = 100.0  # New unpaid passports, show as 100% increase
            else:
                unpaid_change = 0
        else:
            prev_unpaid = None
            unpaid_change = None
        
        # Build trend data (optimized - single query with grouping)
        def build_trend(days):
            trend_start = now - timedelta(days=days)
            
            # Single query for passport revenue by day
            passport_daily = db.session.query(
                func.date(Passport.created_dt).label('day'),
                func.sum(Passport.sold_amt).label('revenue')
            )
            if activity_id:
                passport_daily = passport_daily.filter(Passport.activity_id == activity_id)
            passport_daily = passport_daily.filter(
                Passport.created_dt >= trend_start,
                Passport.created_dt <= now
            ).group_by(func.date(Passport.created_dt)).all()
            
            # Single query for income revenue by day
            income_daily = db.session.query(
                func.date(Income.date).label('day'),
                func.sum(Income.amount).label('revenue')
            )
            if activity_id:
                income_daily = income_daily.filter(Income.activity_id == activity_id)
            income_daily = income_daily.filter(
                Income.date >= trend_start,
                Income.date <= now
            ).group_by(func.date(Income.date)).all()
            
            # Convert to dictionaries for fast lookup
            passport_dict = {str(row.day): float(row.revenue or 0) for row in passport_daily}
            income_dict = {str(row.day): float(row.revenue or 0) for row in income_daily}
            
            # Build trend array
            trend = []
            for i in reversed(range(days)):
                day = (now - timedelta(days=i+1)).date()
                day_str = str(day)
                daily_revenue = passport_dict.get(day_str, 0) + income_dict.get(day_str, 0)
                trend.append(daily_revenue)
            return trend
        
        revenue_trend = build_trend(trend_days)
        
        # Build trends for other KPIs (optimized - single query with grouping)
        def build_count_trend(model, filter_condition, days):
            trend_start = now - timedelta(days=days)
            
            # Determine date column
            date_col = None
            if hasattr(model, 'created_dt'):
                date_col = model.created_dt
            elif hasattr(model, 'signed_up_at'):
                date_col = model.signed_up_at
            else:
                # Fallback to per-day queries if no date column
                return [0] * days
            
            # Single query with grouping
            query = db.session.query(
                func.date(date_col).label('day'),
                func.count().label('count')
            )
            
            if activity_id and hasattr(model, 'activity_id'):
                query = query.filter(model.activity_id == activity_id)
            
            query = query.filter(
                date_col >= trend_start,
                date_col <= now
            )
            
            if filter_condition is not None:
                query = query.filter(filter_condition)
            
            daily_counts = query.group_by(func.date(date_col)).all()
            
            # Convert to dictionary for fast lookup
            count_dict = {str(row.day): row.count for row in daily_counts}
            
            # Build trend array
            trend = []
            for i in reversed(range(days)):
                day = (now - timedelta(days=i+1)).date()
                day_str = str(day)
                trend.append(count_dict.get(day_str, 0))
            return trend
        
        active_users_trend = build_count_trend(Passport, Passport.uses_remaining > 0, trend_days)
        passports_created_trend = build_count_trend(Passport, None, trend_days)
        unpaid_trend = build_count_trend(Passport, Passport.paid == False, trend_days)
        
        return {
            'revenue': {
                'current': round(current_revenue, 2),
                'previous': round(prev_revenue, 2) if prev_revenue is not None else None,
                'change': round(revenue_change, 1) if revenue_change is not None else None,
                'trend_data': revenue_trend
            },
            'active_users': {
                'current': current_active_users,
                'previous': prev_active_users,
                'change': round(active_users_change, 1) if active_users_change is not None else None,
                'trend_data': active_users_trend
            },
            'passports_created': {
                'current': current_passports_created,
                'previous': prev_passports_created,
                'change': round(passports_created_change, 1) if passports_created_change is not None else None,
                'trend_data': passports_created_trend
            },
            'unpaid_passports': {
                'current': current_unpaid,
                'previous': prev_unpaid,
                'change': round(unpaid_change, 1) if unpaid_change is not None else None,
                'trend_data': unpaid_trend,
                'current_period': current_period_unpaid if period != 'all' else None  # New unpaid in current period
            }
        }


# Temporary compatibility shim for get_kpi_stats (to allow app to start during transition)





def send_unpaid_reminders(app, force_send=False):
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

        cutoff_date = datetime.now() - timedelta(days=days)
        
        if force_send:
            print("🔧 FORCE_SEND mode: Will bypass 'already reminded' checks")

        unpaid_passports = Passport.query.filter(
            Passport.paid == False,
            Passport.created_dt <= cutoff_date
        ).all()

        for p in unpaid_passports:
            recent_reminder = ReminderLog.query.filter_by(pass_id=p.id)\
                .order_by(ReminderLog.reminder_sent_at.desc())\
                .first()

            if not force_send and recent_reminder and recent_reminder.reminder_sent_at > datetime.now() - timedelta(days=days):
                print(f"⏳ Skipping reminder: {p.user.name if p.user else '-'} (already reminded)")
                continue

            # ✅ Send email FIRST, then log only if successful
            try:
                print(f"📬 Sending reminder to: {p.user.email if p.user else 'N/A'}")
                from flask import current_app
                notify_pass_event(
                    app=current_app._get_current_object(),
                    event_type="payment_late",
                    pass_data=p,  # using new models
                    activity=p.activity,
                    admin_email="auto-reminder@system",
                    timestamp=datetime.now()
                )
                
                # ✅ Only log to database AFTER email succeeds
                db.session.add(ReminderLog(
                    pass_id=p.id,
                    reminder_sent_at=datetime.now()
                ))
                db.session.commit()
                print(f"✅ Email sent and logged for: {p.user.name if p.user else '-'}")
                
            except Exception as e:
                print(f"❌ Failed to send email to {p.user.name if p.user else '-'}: {e}")
                # No database log if email failed - will retry next time





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
                    activity=best_passport.activity,
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
    import sys

    print("\n" + "🔵"*40)
    print("📨 SEND_EMAIL FUNCTION CALLED")
    print("🔵"*40)
    print(f"Subject: {subject}")
    print(f"To: {to_email}")
    print(f"Template: {template_name}")
    print(f"Has context: {context is not None}")
    print(f"Has inline_images: {len(inline_images) if inline_images else 0}")
    print(f"Has html_body: {html_body is not None}")
    sys.stdout.flush()

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
    # Generate plain text from context or use a better fallback
    plain_text = context.get('preview_text', context.get('heading', 'Your digital pass is ready'))
    if context.get('body_text'):
        plain_text = f"{plain_text}\n\n{context.get('body_text')}"
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
            print(f"📧 Using organization config: {smtp_host}:{smtp_port}")
        else:
            # Fall back to system settings
            smtp_host = get_setting("MAIL_SERVER")
            smtp_port = int(get_setting("MAIL_PORT", 587))
            smtp_user = get_setting("MAIL_USERNAME")
            smtp_pass = get_setting("MAIL_PASSWORD")
            use_tls = str(get_setting("MAIL_USE_TLS") or "true").lower() == "true"
            use_ssl = False
            print(f"📧 Using system config: {smtp_host}:{smtp_port}")

        print(f"🔌 Connecting to SMTP: {smtp_host}:{smtp_port}")
        print(f"   From: {from_email}")
        print(f"   User: {smtp_user}")
        print(f"   TLS: {use_tls}, SSL: {use_ssl}")
        sys.stdout.flush()

        # Choose connection type
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            
        server.ehlo()
        print("✅ SMTP connected and EHLO sent")
        
        if use_tls and not use_ssl:
            server.starttls()
            print("✅ STARTTLS completed")
            
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
            print("✅ SMTP login successful")

        print(f"📤 Sending email from {from_email} to {to_email}...")
        sys.stdout.flush()
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        
        config_type = "organization-specific" if email_config else "system default"
        print(f"✅✅✅ EMAIL SENT SUCCESSFULLY to {to_email}")
        print(f"   Subject: {subject}")
        print("🔵"*40 + "\n")
        sys.stdout.flush()
        logging.info(f"✅ Email sent to {to_email} with subject '{subject}' using {config_type} configuration")
        return True  # Return True on success

    except Exception as e:
        print(f"❌❌❌ FAILED TO SEND EMAIL: {e}")
        print("🔵"*40 + "\n")
        sys.stdout.flush()
        logging.exception(f"❌ Failed to send email to {to_email}: {e}")
        return False  # Return False on failure


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
                
                # 📧 Apply email template customizations if activity is provided
                if activity and template_name and not html_body:
                    # Map template names to our template types
                    template_type_mapping = {
                        'email_templates/newPass/index.html': 'newPass',
                        'email_templates/newPass_compiled/index.html': 'newPass',
                        'newPass': 'newPass',
                        'email_templates/paymentReceived/index.html': 'paymentReceived',
                        'email_templates/paymentReceived_compiled/index.html': 'paymentReceived',
                        'paymentReceived': 'paymentReceived',
                        'email_templates/latePayment/index.html': 'latePayment',
                        'email_templates/latePayment_compiled/index.html': 'latePayment',
                        'latePayment': 'latePayment',
                        'email_templates/signup/index.html': 'signup',
                        'email_templates/signup_compiled/index.html': 'signup',
                        'signup': 'signup',
                        'email_templates/redeemPass/index.html': 'redeemPass',
                        'email_templates/redeemPass_compiled/index.html': 'redeemPass',
                        'redeemPass': 'redeemPass',
                        'email_templates/survey_invitation/index.html': 'survey_invitation',
                        'email_templates/survey_invitation_compiled/index.html': 'survey_invitation',
                        'survey_invitation': 'survey_invitation'
                    }
                    
                    template_type = template_type_mapping.get(template_name)
                    if template_type:
                        from utils import get_email_context
                        # Apply activity customizations to context
                        context = get_email_context(activity, template_type, context)
                        # Update subject if customized
                        if context.get('subject'):
                            subject = context['subject']

                # Load inline images for compiled templates
                if template_name and not html_body:
                    # Normalize template name to get base name
                    base_template = template_name.replace('email_templates/', '').replace('/index.html', '').replace('.html', '')
                    compiled_folder = os.path.join("templates/email_templates", f"{base_template}_compiled")
                    json_path = os.path.join(compiled_folder, "inline_images.json")
                    
                    # If compiled version exists, load the inline images
                    if os.path.exists(json_path):
                        import base64
                        with open(json_path, "r") as f:
                            compiled_images = json.load(f)
                            for cid, img_base64 in compiled_images.items():
                                inline_images[cid] = base64.b64decode(img_base64)

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

                # Extract pass data if it exists (for backward compatibility)
                pass_code = None
                user_name = None
                if context:
                    # Try to get from hockey_pass structure (old format)
                    if "hockey_pass" in context:
                        pass_code = context.get("hockey_pass", {}).get("pass_code")
                        user_name = context.get("hockey_pass", {}).get("user_name")
                    # Also check for direct pass_code (new format)
                    elif "pass_code" in context:
                        pass_code = context.get("pass_code")
                        user_name = context.get("user_name")
                
                db.session.add(EmailLog(
                    to_email=to_email,
                    subject=subject,
                    pass_code=pass_code,
                    template_name=template_name or "",
                    context_json=json.dumps({
                        "user_name": user_name or context.get("user_name") if context else None,
                        "activity_name": context.get("activity_name") if context else None,
                        "template_type": template_name,
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

                # Try to extract pass_code safely for error log
                error_pass_code = None
                error_context = kwargs.get("context", {})
                if error_context:
                    if "hockey_pass" in error_context:
                        error_pass_code = error_context.get("hockey_pass", {}).get("pass_code")
                    elif "pass_code" in error_context:
                        error_pass_code = error_context.get("pass_code")
                
                db.session.add(EmailLog(
                    to_email=kwargs.get("to_email"),
                    subject=kwargs.get("subject"),
                    pass_code=error_pass_code,
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
    from utils import send_email_async, get_email_context
    from flask import render_template_string, url_for
    import os
    import json
    import base64
    from datetime import datetime, timezone

    timestamp = timestamp or datetime.now(timezone.utc)

    # Build base context
    base_context = {
        "user_name": signup.user.name,
        "activity_name": activity.name
    }
    
    # Get email context using activity-specific templates
    email_context = get_email_context(activity, 'signup', base_context)
    
    # Extract template values
    subject = email_context.get('subject', "Confirmation d'inscription")
    title = email_context.get('title', "Votre Inscription est Confirmée")
    intro_raw = email_context.get('intro_text', '')
    conclusion_raw = email_context.get('conclusion_text', '')
    theme = "signup/index.html"

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
        "logo_url": "/static/uploads/logo.png",
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


def notify_pass_event(app, *, event_type, pass_data, activity, admin_email=None, timestamp=None):
    from utils import send_email_async, get_pass_history_data, generate_qr_code_image, get_email_context
    from flask import render_template, render_template_string, url_for
    from datetime import datetime, timezone
    import json
    import base64
    import os

    timestamp = timestamp or datetime.now(timezone.utc)
    
    # Map event types to template keys used in activity.email_templates
    event_type_mapping = {
        'pass_created': 'newPass',
        'payment_received': 'paymentReceived', 
        'payment_late': 'latePayment',
        'pass_redeemed': 'redeemPass'
    }
    
    template_type = event_type_mapping.get(event_type, 'newPass')
    
    # Build base context
    base_context = {
        "pass_data": pass_data,
        "default_qt": getattr(pass_data, "uses_remaining", 0),
        "activity_list": getattr(pass_data.activity, "name", "") if pass_data.activity else ""
    }
    
    # Get email context using activity-specific templates
    email_context = get_email_context(activity, template_type, base_context)
    
    # Extract template values
    subject = email_context.get('subject', f"[Minipass] {event_type.title()} Notification")
    title = email_context.get('title', f"{event_type.title()} Confirmation")
    intro_raw = email_context.get('intro_text', '')
    conclusion_raw = email_context.get('conclusion_text', '')
    
    # Render intro and conclusion with pass_data context
    intro = render_template_string(intro_raw, pass_data=pass_data, default_qt=email_context.get('default_qt', 0), activity_list=email_context.get('activity_list', ''))
    conclusion = render_template_string(conclusion_raw, pass_data=pass_data, default_qt=email_context.get('default_qt', 0), activity_list=email_context.get('activity_list', ''))

    print("🔔 Email debug - subject:", subject)
    print("🔔 Email debug - title:", title)
    print("🔔 Email debug - intro:", intro[:80])

    qr_data = generate_qr_code_image(pass_data.pass_code).read()
    history = get_pass_history_data(pass_data.pass_code, fallback_admin_email=admin_email)

    # Map event type to template directory - Use compiled template paths
    template_mapping = {
        'pass_created': 'newPass_compiled/index.html',
        'payment_received': 'paymentReceived_compiled/index.html',
        'payment_late': 'latePayment_compiled/index.html',
        'pass_redeemed': 'redeemPass_compiled/index.html'
    }
    theme = template_mapping.get(event_type, 'newPass_compiled/index.html')
    
    context = {
        "pass_data": {
            "pass_code": pass_data.pass_code,
            "user_name": pass_data.user.name if pass_data.user else "",
            "activity": pass_data.activity.name if pass_data.activity else "",
            "games_remaining": pass_data.uses_remaining,
            "sold_amt": pass_data.sold_amt,
            "user_email": pass_data.user.email if pass_data.user else "",
            "phone_number": pass_data.user.phone_number if pass_data.user else "",
            "pass_created_dt": pass_data.created_dt,
            "paid_ind": pass_data.paid
        },
        "title": title,
        "intro_text": intro,
        "conclusion_text": conclusion,
        "owner_html": render_template("email_blocks/owner_card_inline.html", pass_data=pass_data),
        "history_html": render_template("email_blocks/history_table_inline.html", history=history),
        "email_info": "",
        "logo_url": "/static/uploads/logo.png",
        "special_message": ""
    }

    # Load compiled inline_images.json
    import json
    import base64
    import os
    compiled_folder = theme.replace('/index.html', '')
    json_path = os.path.join('templates/email_templates', compiled_folder, 'inline_images.json')

    inline_images = {}
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            compiled_images = json.load(f)
            for cid, img_base64 in compiled_images.items():
                inline_images[cid] = base64.b64decode(img_base64)
        print(f"Loaded {len(inline_images)} inline images from compiled template")

    # Add dynamic content (QR code must be generated per passport)
    inline_images['qr_code'] = qr_data
    inline_images['logo_image'] = open("static/uploads/logo.png", "rb").read()

    # Determine user and activity for email context
    user_obj = getattr(pass_data, "user", None)
    activity_obj = getattr(pass_data, "activity", None)
    
    send_email_async(
        app,
        user=user_obj,
        activity=activity_obj,
        subject=subject,
        to_email=pass_data.user.email if pass_data.user else None,
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


def get_email_context(activity, template_type, base_context=None):
    """
    Merge activity email template customizations with default values
    
    CRITICAL: Preserves email blocks (owner_html, history_html) from base_context.
    These blocks are never overridden by user customizations.
    
    Args:
        activity: Activity model instance
        template_type: Template type (newPass, paymentReceived, etc.)
        base_context: Base context dictionary to merge with
    
    Returns:
        Dictionary with merged email context
    """
    # Default email template values
    defaults = {
        'subject': 'Minipass Notification',
        'title': 'Welcome to Minipass',
        'intro_text': 'Thank you for using our service.',
        'conclusion_text': 'We appreciate your business!',
        'hero_image': None,
        'cta_text': None,
        'cta_url': None,
        'custom_message': None
    }
    
    # Start with base context if provided
    context = base_context.copy() if base_context else {}
    
    # Apply defaults for missing keys
    for key, value in defaults.items():
        if key not in context:
            context[key] = value
    
    # Preserve email blocks from base_context - NEVER override these
    protected_blocks = {}
    if base_context:
        if 'owner_html' in base_context:
            protected_blocks['owner_html'] = base_context['owner_html']
        if 'history_html' in base_context:
            protected_blocks['history_html'] = base_context['history_html']
    
    # Apply activity-specific customizations if they exist
    if activity and activity.email_templates:
        template_customizations = activity.email_templates.get(template_type, {})
        for key, value in template_customizations.items():
            # NEVER allow customizations to override email blocks
            if key not in ['owner_html', 'history_html']:
                if value is not None and value != '':
                    context[key] = value
    
    # Restore protected blocks to ensure they're never overridden
    context.update(protected_blocks)
    
    return context




