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
import bleach
from urllib.parse import urlparse


def get_template_default_hero(template_type):
    """
    Load the default hero image from compiled template's inline_images.json
    
    Args:
        template_type: Type of template (newPass, paymentReceived, etc.)
        
    Returns:
        bytes: Hero image data, or None if not found
    """
    import os
    import json
    import base64
    
    # Map template types to their ORIGINAL folders (pristine defaults)
    template_map = {
        'newPass': 'newPass_original',
        'paymentReceived': 'paymentReceived_original',
        'latePayment': 'latePayment_original',
        'signup': 'signup_original',
        'waitlist': 'waitlist_original'
    }
    
    original_folder = template_map.get(template_type)
    if not original_folder:
        print(f"❌ Unknown template type: {template_type}")
        return None
    
    # Load inline_images.json from ORIGINAL template (pristine default)
    json_path = os.path.join('templates', 'email_templates', original_folder, 'inline_images.json')
    
    if not os.path.exists(json_path):
        print(f"❌ Template JSON not found: {json_path}")
        return None
    
    try:
        with open(json_path, 'r') as f:
            compiled_images = json.load(f)
        
        # Map template types to their hero image keys
        hero_key_map = {
            'newPass': 'hero_new_pass',
            'paymentReceived': 'hero_payment_received', 
            'latePayment': 'hero_late_payment',
            'signup': 'hero_signup',
            'waitlist': 'hero_waitlist'
        }
        
        hero_key = hero_key_map.get(template_type)
        if not hero_key or hero_key not in compiled_images:
            print(f"❌ Hero key '{hero_key}' not found in {json_path}")
            return None
        
        # Decode base64 image data
        hero_base64 = compiled_images[hero_key]
        hero_data = base64.b64decode(hero_base64)
        print(f"📦 Loaded original template default hero: {template_type} -> {hero_key}")
        return hero_data
        
    except Exception as e:
        print(f"❌ Error loading template hero: {e}")
        return None


def get_activity_hero_image(activity, template_type):
    """
    Hero image selection with CORRECT priority order:
    1. Custom uploaded hero (highest priority)
    2. Original template default (proper default) 
    3. Activity image (last resort only)
    
    Returns: tuple (image_data, is_custom, is_template_default)
    """
    import os
    
    print(f"🔍 get_activity_hero_image: activity={activity.id if activity else None}, template_type={template_type}")
    
    # Priority 1: Check for custom uploaded hero FIRST
    if activity:
        custom_hero_path = f"static/uploads/{activity.id}_{template_type}_hero.png"
        print(f"🔍 Checking for custom hero at: {custom_hero_path}")
        
        if os.path.exists(custom_hero_path):
            try:
                with open(custom_hero_path, "rb") as f:
                    hero_data = f.read()
                    print(f"✅ Found custom hero override for activity {activity.id}, template {template_type} - {len(hero_data)} bytes")
                    return hero_data, True, False
            except Exception as e:
                print(f"❌ Error reading custom hero file {custom_hero_path}: {e}")
        else:
            print(f"ℹ️ No custom hero found at {custom_hero_path}")
    
    # Priority 2: Load original template default (pristine version)
    template_hero_data = get_template_default_hero(template_type)
    if template_hero_data:
        print(f"📦 Using original template default hero for {template_type}")
        return template_hero_data, False, True  # is_template_default=True
    
    # Priority 3: Fall back to activity image only if no template exists (last resort)
    if activity and activity.image_filename:
        # Try both locations: main uploads and activity_images subdirectory
        activity_image_paths = [
            f"static/uploads/{activity.image_filename}",
            f"static/uploads/activity_images/{activity.image_filename}"
        ]
        
        for activity_image_path in activity_image_paths:
            if os.path.exists(activity_image_path):
                with open(activity_image_path, "rb") as f:
                    print(f"⚠️ Using activity image as fallback hero for {template_type}: {activity.image_filename}")
                    return f.read(), False, False  # is_template_default=False
    
    # No hero image found
    print(f"❌ No hero image found for {template_type}")
    return None, False, False


class ContentSanitizer:
    """
    Content sanitization class for email templates
    Provides HTML sanitization and URL validation for security
    """
    
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'a', 'ul', 'ol', 'li', 
        'blockquote', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'hr'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'target', 'rel']
    }
    
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
    
    @staticmethod
    def sanitize_html(content):
        """
        Sanitize HTML content to prevent XSS attacks
        
        Args:
            content (str): Raw HTML content
            
        Returns:
            str: Sanitized HTML content
        """
        if not content:
            return ''
            
        # First pass: Remove script tags and their content completely
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean the HTML content with bleach
        cleaned = bleach.clean(
            content,
            tags=ContentSanitizer.ALLOWED_TAGS,
            attributes=ContentSanitizer.ALLOWED_ATTRIBUTES,
            protocols=ContentSanitizer.ALLOWED_PROTOCOLS,
            strip=True
        )
        
        # Additional security checks
        # Remove any remaining javascript: protocols
        cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'on\w+\s*=', '', cleaned, flags=re.IGNORECASE)  # Remove event handlers
        
        return cleaned
    
    @staticmethod
    def validate_url(url):
        """
        Validate and sanitize URLs for CTA links
        
        Args:
            url (str): URL to validate
            
        Returns:
            str: Sanitized URL or empty string if invalid
        """
        if not url:
            return ''
            
        url = url.strip()
        
        # Check for dangerous protocols
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'ftp:']
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                return ''
        
        # Check for dangerous patterns that could be interpreted as protocols
        if ':' in url and not url.startswith(('http://', 'https://', 'mailto:')):
            # If it contains : but doesn't start with allowed protocols, reject it
            if not '@' in url:  # Unless it's an email without mailto:
                return ''
            
        # Add protocol if missing
        if not url.startswith(('http://', 'https://', 'mailto:')):
            if '@' in url:
                url = f'mailto:{url}'
            else:
                url = f'https://{url}'
        
        try:
            parsed = urlparse(url)
            # Ensure valid scheme
            if parsed.scheme not in ContentSanitizer.ALLOWED_PROTOCOLS:
                return ''
                
            # Basic validation for http/https URLs
            if parsed.scheme in ['http', 'https']:
                if not parsed.netloc:
                    return ''
                # Check for suspicious netloc
                if ':' in parsed.netloc.split('.')[0]:  # Port in first part might be suspicious
                    pass  # Actually ports are OK
                    
            return url
        except Exception:
            return ''
    
    @staticmethod
    def sanitize_email_template_data(template_data):
        """
        Sanitize all fields in email template data
        
        Args:
            template_data (dict): Template data dictionary
            
        Returns:
            dict: Sanitized template data
        """
        if not template_data:
            return {}
            
        sanitized = template_data.copy()
        
        # Fields that need HTML sanitization
        html_fields = ['intro_text', 'custom_message', 'conclusion_text']
        for field in html_fields:
            if field in sanitized:
                sanitized[field] = ContentSanitizer.sanitize_html(sanitized[field])
        
        # Fields that need URL validation
        if 'cta_url' in sanitized:
            sanitized['cta_url'] = ContentSanitizer.validate_url(sanitized['cta_url'])
        
        # Fields that need basic text sanitization (no HTML allowed)
        text_fields = ['subject', 'title', 'cta_text']
        for field in text_fields:
            if field in sanitized:
                # Strip HTML tags completely for these fields
                sanitized[field] = bleach.clean(sanitized[field], tags=[], strip=True)
                # Remove any remaining special characters that could be harmful
                sanitized[field] = re.sub(r'[<>"\']', '', sanitized[field])
        
        return sanitized


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


# ✅ PHASE 3: Optimized QR Code Generation & Hosted Image System
def generate_optimized_qr_code(pass_code):
    """Generate QR code optimized for email (200x200px)"""
    try:
        from PIL import Image
    except ImportError:
        # Fallback to original method if PIL not available
        return generate_qr_code_image(pass_code)
    
    import os
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,  # Smaller box size for 200x200
        border=2,
    )
    qr.add_data(pass_code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize to exactly 200x200
    img = img.resize((200, 200), Image.Resampling.LANCZOS)
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG", optimize=True)
    img_bytes.seek(0)
    
    return img_bytes


def save_qr_code_to_static(pass_code, qr_data, base_url):
    """Save QR code to static directory and return URL"""
    import os
    
    os.makedirs('static/uploads/qr', exist_ok=True)
    file_path = f'static/uploads/qr/{pass_code}.png'
    
    with open(file_path, 'wb') as f:
        f.write(qr_data)
    
    return f"{base_url}/static/uploads/qr/{pass_code}.png"


def get_or_create_qr_code_url(pass_code, base_url):
    """Get existing QR code URL or create new one"""
    import os
    
    qr_path = f'static/uploads/qr/{pass_code}.png'
    
    if os.path.exists(qr_path):
        return f"{base_url}/static/uploads/qr/{pass_code}.png"
    
    # Generate new optimized QR code
    qr_data = generate_optimized_qr_code(pass_code).read()
    return save_qr_code_to_static(pass_code, qr_data, base_url)


def generate_image_urls(context, base_url):
    """Generate URLs for email images based on context"""
    import os
    
    urls = {}
    
    # QR code URL
    if 'pass_code' in context:
        urls['qr_code_url'] = get_or_create_qr_code_url(context['pass_code'], base_url)
    
    # Hero image URL
    if 'activity_id' in context:
        activity_id = context['activity_id']
        # Check if custom hero exists
        hero_path = f'static/uploads/{activity_id}_hero.png'
        if os.path.exists(hero_path):
            urls['hero_image_url'] = f"{base_url}/static/uploads/{activity_id}_hero.png"
    
    # Logo URL  
    if 'activity_id' in context:
        activity_id = context['activity_id']
        logo_path = f'static/uploads/{activity_id}_owner_logo.png'
        if os.path.exists(logo_path):
            urls['logo_url'] = f"{base_url}/static/uploads/{activity_id}_owner_logo.png"
    
    return urls


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
            admin = db.session.get(Admin, created_by)
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
            # DEBUG: Show exact subject for troubleshooting
            print(f"🔍 DEBUG - Subject analysis:")
            print(f"   Raw subject: '{subject}'")
            print(f"   Subject length: {len(subject)}")
            print(f"   Contains 'reçu': {'reçu' in subject}")
            print(f"   Contains '$': {'$' in subject}")
            print(f"   Contains 'de': {'de' in subject}")
            
            # Updated regex to handle spaces in amounts like "98, 00" and proper $ escaping
            amount_match = re.search(r"reçu\s+([\d,\s]+)\s+\$\s+de", subject)
            name_match = re.search(r"de\s+(.+?)\s+et ce montant", subject)
            
            print(f"   Amount regex match: {amount_match is not None}")
            print(f"   Name regex match: {name_match is not None}")

            # 🔁 Fallback: e.g. "Remi Methot vous a envoyé 15,00 $"
            if not amount_match:
                amount_match = re.search(r"envoyé\s+([\d,\s]+)\s*\$", subject)
                print(f"   Fallback amount regex match: {amount_match is not None}")
            if not name_match:
                name_match = re.search(r":\s*(.*?)\svous a envoyé", subject)
                print(f"   Fallback name regex match: {name_match is not None}")

            # 🛡️ Skip if we still can't match
            if not (amount_match and name_match):
                print(f"❌ Skipped unmatched subject: {subject}")
                print(f"   Final amount_match: {amount_match is not None}")
                print(f"   Final name_match: {name_match is not None}")
                continue

            # 💵 Final parsing
            # Remove spaces and replace comma with period for proper float conversion
            amt_str = amount_match.group(1).replace(" ", "").replace(",", ".")
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
                day = (now - timedelta(days=i)).date()
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
                day = (now - timedelta(days=i)).date()
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
    from datetime import datetime, timezone, timedelta
    from flask import current_app
    from rapidfuzz import fuzz
    import imaplib
    import unicodedata

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
            
            # IMPROVED: Check if we already processed this payment (with time window to prevent duplicates)
            # Check for duplicates within last 48 hours to handle re-sent notifications
            time_window = datetime.now(timezone.utc) - timedelta(hours=48)
            existing_payment = EbankPayment.query.filter(
                EbankPayment.bank_info_name == name,
                EbankPayment.bank_info_amt == amt,
                EbankPayment.from_email == from_email,
                EbankPayment.timestamp >= time_window
            ).first()

            # Track if we're updating an existing record to avoid duplicates
            update_existing_record = False
            
            if existing_payment:
                if existing_payment.result == "MATCHED":
                    print(f"✅ ALREADY SUCCESSFULLY MATCHED: {name} - ${amt} from {from_email}")
                    print(f"   Processed on: {existing_payment.timestamp}")
                    print(f"   Matched to passport ID: {existing_payment.matched_pass_id}")
                    continue  # Skip only successfully matched payments
                elif existing_payment.result == "NO_MATCH":
                    print(f"🔄 RETRYING PREVIOUSLY FAILED MATCH: {name} - ${amt} from {from_email}")
                    print(f"   Previous attempt on: {existing_payment.timestamp}")
                    print(f"   Will update existing record if successful")
                    update_existing_record = True
                    # Continue processing to retry the match
            
            print(f"\n" + "="*80)
            print(f"💳 PROCESSING NEW PAYMENT")
            print(f"   From: {name}")
            print(f"   Amount: ${amt}")
            print(f"   Email: {from_email}")
            print(f"   Subject: {subject[:50]}...")

            # OPTIMIZATION: Filter by exact amount FIRST for massive performance gain
            # Convert to float for reliable comparison
            payment_amount = float(amt)

            # Get all unpaid passports first, then filter by amount in Python
            all_unpaid = Passport.query.filter_by(paid=False).all()
            unpaid_passports = [p for p in all_unpaid if float(p.sold_amt) == payment_amount]

            if not unpaid_passports:
                print(f"❌ NO UNPAID PASSPORTS FOUND for ${payment_amount:.2f}")

                # Check if a PAID passport exists with matching amount and similar name
                all_paid = Passport.query.filter_by(paid=True).all()
                paid_passports_same_amount = [p for p in all_paid if float(p.sold_amt) == payment_amount]

                # Normalize payment name for comparison
                def normalize_for_comparison(text):
                    normalized = unicodedata.normalize('NFD', text)
                    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
                    return without_accents.lower().strip()

                payment_name_normalized = normalize_for_comparison(name)

                # Check if any paid passport has matching name
                matching_paid_passport = None
                for p in paid_passports_same_amount:
                    passport_name_normalized = normalize_for_comparison(p.user.name)
                    if payment_name_normalized == passport_name_normalized:
                        matching_paid_passport = p
                        break

                # Determine appropriate note
                if matching_paid_passport:
                    note_text = f"Passport already marked as PAID (manually by admin) - {matching_paid_passport.user.name} ${payment_amount:.2f}"
                    print(f"   ⚠️ Found PAID passport: {matching_paid_passport.user.name}")
                else:
                    note_text = f"No unpaid passports for ${payment_amount:.2f} - payment may have arrived before passport creation"
                    print(f"   Payment may have arrived before passport creation")
                    # Debug: Show available amounts for troubleshooting
                    available_amounts = list(set(float(p.sold_amt) for p in all_unpaid))
                    available_amounts.sort()
                    print(f"   Available unpaid amounts: {[f'${a:.2f}' for a in available_amounts[:10]]}")

                if update_existing_record and existing_payment:
                    # Update existing record instead of creating new one
                    existing_payment.result = "NO_MATCH"
                    existing_payment.name_score = 0
                    existing_payment.note = note_text
                    existing_payment.timestamp = datetime.now(timezone.utc)
                    print(f"   📝 Updated existing NO_MATCH record")
                else:
                    # Create new record
                    db.session.add(EbankPayment(
                        from_email=from_email,
                        subject=subject,
                        bank_info_name=name,
                        bank_info_amt=amt,
                        name_score=0,
                        result="NO_MATCH",
                        mark_as_paid=False,
                        note=note_text
                    ))
                continue  # Skip to next payment

            print(f"🔍 Found {len(unpaid_passports)} unpaid passports for ${payment_amount:.2f}")
            print("="*80)

            # IMPROVED ALGORITHM: Stage 1 - Normalize names and try matching
            # Helper function to normalize names (remove accents)
            def normalize_name(text):
                """Remove accents and normalize text for better matching"""
                # NFD decompose, then filter out combining marks
                normalized = unicodedata.normalize('NFD', text)
                without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
                return without_accents.lower().strip()
            
            normalized_payment_name = normalize_name(name)
            print(f"📝 Normalized payment name: '{name}' → '{normalized_payment_name}'")
            
            exact_matches = []
            fuzzy_matches = []
            all_passport_amounts = {}  # Track all amounts for better logging
            
            for p in unpaid_passports:
                if not p.user:
                    continue
                
                # Store all passport amounts for this user for debugging
                user_key = normalize_name(p.user.name)
                if user_key not in all_passport_amounts:
                    all_passport_amounts[user_key] = []
                all_passport_amounts[user_key].append((p.id, p.sold_amt, p.user.name))
                
                # Calculate match score using normalized names
                normalized_passport_name = normalize_name(p.user.name)
                score = fuzz.ratio(normalized_payment_name, normalized_passport_name)
                
                # Only log high-scoring matches to reduce noise
                if score >= 70:
                    print(f"🔍 Checking: '{p.user.name}' (normalized: '{normalized_passport_name}') - Score: {score}%, Amount: ${p.sold_amt}")
                
                # NEW: Categorize matches by quality
                if score >= 95:  # Near-exact match (95-100%)
                    exact_matches.append((p, score))
                    print(f"🎯 EXACT MATCH: {p.user.name} (Score: {score})")
                elif score >= threshold:  # Fuzzy match (threshold-94%)
                    fuzzy_matches.append((p, score))
                    print(f"🔍 Fuzzy match: {p.user.name} (Score: {score})")

            print(f"📊 Stage 1: Found {len(exact_matches)} exact matches, {len(fuzzy_matches)} fuzzy matches for '{name}'")

            # NEW: Prioritize exact matches over fuzzy matches
            candidates = exact_matches if exact_matches else fuzzy_matches
            candidate_type = "exact" if exact_matches else "fuzzy"
            print(f"🎯 Using {candidate_type} matches for processing")

            # Stage 2: Select best match from candidates (all already have correct amount)
            best_passport = None
            best_score = 0

            # All candidates already have the correct amount, so just find best name match
            valid_matches = candidates  # All candidates are valid since amount already matches

            if len(valid_matches) > 1:
                # Check if we have multiple matches with similar scores (ambiguous)
                scores = [score for _, score in valid_matches]
                score_range = max(scores) - min(scores)
                print(f"⚠️ Multiple matches found! Score range: {score_range}")

                if score_range < 5:  # All scores within 5 points = ambiguous
                    print(f"🚨 AMBIGUOUS MATCH detected for '{name}' - Multiple similar candidates")
                    for p, score in valid_matches:
                        print(f"   - {p.user.name}: {score}% (Passport #{p.id})")

            # Select best match (highest score, then oldest)
            if valid_matches:
                # Sort by score (highest first), then by created_dt (oldest first)
                valid_matches.sort(key=lambda x: (-x[1], x[0].created_dt))
                best_passport = valid_matches[0][0]
                best_score = valid_matches[0][1]
                print(f"🎯 Selected passport: {best_passport.user.name} - ${best_passport.sold_amt} (Score: {best_score}%, created: {best_passport.created_dt})")

            if best_passport:
                print(f"\n🎯 FINAL MATCH: {best_passport.user.name} - ${best_passport.sold_amt} (Passport ID: {best_passport.id})")
            else:
                print(f"\n❌ NO MATCH FOUND")
                print(f"   Payment: {name} - ${amt}")

                # Log why no match was found (improved logic for amount-first filtering)
                if not candidates:
                    print(f"   Reason: No name matches above {threshold}% threshold")
                    # Show the closest matches for debugging
                    closest_matches = []
                    for p in unpaid_passports:
                        if not p.user:
                            continue
                        score = fuzz.ratio(normalize_name(name), normalize_name(p.user.name))
                        if score >= 50:  # Show matches above 50% for context
                            closest_matches.append((p.user.name, score))

                    if closest_matches:
                        closest_matches.sort(key=lambda x: x[1], reverse=True)
                        print(f"   Closest matches for ${amt}:")
                        for user_name, score in closest_matches[:3]:
                            print(f"      - {user_name}: {score}%")
                
            if best_passport:
                now_utc = datetime.now(timezone.utc)
                best_passport.paid = True
                best_passport.paid_date = now_utc
                db.session.add(best_passport)

                if update_existing_record and existing_payment:
                    # Update existing record instead of creating new one
                    existing_payment.matched_pass_id = best_passport.id
                    existing_payment.matched_name = best_passport.user.name
                    existing_payment.matched_amt = best_passport.sold_amt
                    existing_payment.name_score = best_score
                    existing_payment.result = "MATCHED"
                    existing_payment.mark_as_paid = True
                    existing_payment.note = "Matched by Gmail Bot (retry successful)."
                    existing_payment.timestamp = datetime.now(timezone.utc)
                    print(f"   📝 Updated existing record to MATCHED")
                else:
                    # Create new record
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
                # Improved: Calculate closest candidates for admin visibility
                all_candidates = []
                for p in unpaid_passports:
                    if not p.user:
                        continue
                    score = fuzz.ratio(normalize_name(name), normalize_name(p.user.name))
                    if score >= 50:  # Only show candidates above 50% to avoid noise
                        all_candidates.append((p.user.name, score))

                # Sort by score and take top 3
                all_candidates.sort(key=lambda x: x[1], reverse=True)
                top_candidates = all_candidates[:3]

                # Format candidates for note with more detail
                note_parts = [f"No names above {threshold}% threshold for ${amt}."]

                if top_candidates:
                    candidate_strs = [f"{name} ({score:.0f}%)" for name, score in top_candidates]
                    note_parts.append(f"Closest matches: {', '.join(candidate_strs)}")
                else:
                    note_parts.append("No similar names found.")

                note_text = " ".join(note_parts)
                
                if update_existing_record and existing_payment:
                    # Update existing record instead of creating new one
                    existing_payment.result = "NO_MATCH"
                    existing_payment.name_score = 0
                    existing_payment.mark_as_paid = False
                    existing_payment.note = note_text
                    existing_payment.timestamp = datetime.now(timezone.utc)
                    print(f"   📝 Updated existing NO_MATCH record")
                else:
                    # Create new record
                    db.session.add(EbankPayment(
                        from_email=from_email,
                        subject=subject,
                        bank_info_name=name,
                        bank_info_amt=amt,
                        name_score=0,
                        result="NO_MATCH",
                        mark_as_paid=False,
                        note=note_text
                    ))

        db.session.commit()
        mail.expunge()
        mail.logout()


def move_payment_email_by_criteria(bank_info_name, bank_info_amt, from_email):
    """
    Manually move a payment email to the manually_processed folder.
    Used when email wasn't automatically moved due to a glitch.

    Returns: (success: bool, message: str)
    """
    from utils import get_setting
    from models import EbankPayment, db
    from datetime import datetime, timezone
    import imaplib
    import email
    import re
    import unicodedata

    def normalize_name(text):
        """Normalize name for comparison - handles accents, special chars"""
        if not text:
            return ""
        # Normalize Unicode (NFKD = decompose accents)
        normalized = unicodedata.normalize('NFKD', str(text))
        # Remove accents by filtering out combining characters
        ascii_text = normalized.encode('ASCII', 'ignore').decode('ASCII')
        return ascii_text.lower().strip()

    user = get_setting("MAIL_USERNAME")
    pwd = get_setting("MAIL_PASSWORD")

    if not user or not pwd:
        return False, "Email credentials not configured"

    processed_folder = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "PaymentProcessed")
    manually_processed_folder = "ManualProcessed"

    # Get IMAP server
    imap_server = get_setting("IMAP_SERVER")
    if not imap_server:
        mail_server = get_setting("MAIL_SERVER")
        imap_server = mail_server if mail_server else "imap.gmail.com"

    try:
        # Connect to IMAP
        try:
            mail = imaplib.IMAP4_SSL(imap_server)
        except:
            mail = imaplib.IMAP4(imap_server, 143)
            mail.starttls()

        mail.login(user, pwd)
        mail.select("inbox")

        # Search for email matching criteria
        # Use the actual from_email parameter (from database) instead of setting
        print(f"🔍 SEARCH DEBUG: Searching inbox for emails from {from_email}")
        print(f"   Looking for: {bank_info_name}, ${bank_info_amt}")

        status, data = mail.search(None, f'FROM "{from_email}"')

        if status != "OK" or not data[0]:
            mail.logout()
            print(f"❌ SEARCH DEBUG: No emails found from {from_email}")
            return False, "No payment emails found in inbox"

        print(f"📧 SEARCH DEBUG: Found {len(data[0].split())} emails from {from_email}")

        email_found = False
        uid_to_move = None

        for num in data[0].split():
            # Fetch email
            status, msg_data = mail.fetch(num, "(BODY.PEEK[] UID)")
            print(f"📨 SEARCH DEBUG: Checking email #{num}")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            uid_line = msg_data[0][0].decode()
            uid_match = re.search(r"UID (\d+)", uid_line)
            uid = uid_match.group(1) if uid_match else None

            # Parse email
            msg = email.message_from_bytes(raw_email)
            subject = msg["Subject"]

            # Decode subject properly (handles encoded headers)
            decoded_parts = email.header.decode_header(subject)
            if decoded_parts:
                subject_text = ""
                for part, encoding in decoded_parts:
                    if isinstance(part, bytes):
                        subject_text += part.decode(encoding or 'utf-8', errors='ignore')
                    else:
                        subject_text += part
                subject = subject_text

            # Debug: Print FULL subject
            print(f"   📧 FULL SUBJECT: '{subject}'")
            print(f"   📧 Subject length: {len(subject)}")

            # Extract name and amount from subject
            amount_match = re.search(r"reçu\s+([\d,\s]+)\s+\$\s+de", subject)
            name_match = re.search(r"de\s+(.+?)\s+et ce montant", subject)

            print(f"   📊 Pattern 1 - Amount match: {amount_match is not None}")
            print(f"   📊 Pattern 1 - Name match: {name_match is not None}")

            if not amount_match:
                amount_match = re.search(r"envoyé\s+([\d,\s]+)\s*\$", subject)
                print(f"   📊 Pattern 2 - Amount match: {amount_match is not None}")
            if not name_match:
                name_match = re.search(r":\s*(.*?)\svous a envoyé", subject)
                print(f"   📊 Pattern 2 - Name match: {name_match is not None}")

            if amount_match and name_match:
                amt_str = amount_match.group(1).replace(" ", "").replace(",", ".")
                name = name_match.group(1).strip()

                print(f"   ✅ EXTRACTED: Name='{name}', Amount String='{amt_str}'")

                try:
                    amount = float(amt_str)
                except:
                    print(f"   ❌ Could not parse amount: {amt_str}")
                    continue

                print(f"   🎯 Comparing (normalized): '{normalize_name(name)}' vs '{normalize_name(bank_info_name)}'")
                print(f"   💰 Comparing: ${amount} vs ${float(bank_info_amt)}")

                # Check if this matches our criteria (with Unicode normalization)
                if (normalize_name(name) == normalize_name(bank_info_name) and
                    abs(amount - float(bank_info_amt)) < 0.01):
                    print(f"✅ SEARCH DEBUG: MATCH FOUND! UID={uid}")
                    email_found = True
                    uid_to_move = uid
                    break
                else:
                    print(f"❌ SEARCH DEBUG: No match (name or amount differs)")
            else:
                print(f"   ⚠️ Subject parsing failed - patterns didn't match")

        if not email_found or not uid_to_move:
            mail.logout()

            # Update database to MANUAL_PROCESSED to prevent button from showing again
            print(f"🔍 DEBUG: Searching for payment - Name: {bank_info_name}, Amount: {bank_info_amt}, Email: {from_email}")
            recent_payment = EbankPayment.query.filter(
                EbankPayment.bank_info_name == bank_info_name,
                EbankPayment.bank_info_amt == float(bank_info_amt),
                EbankPayment.from_email == from_email,
                EbankPayment.result == "NO_MATCH"
            ).order_by(EbankPayment.timestamp.desc()).first()

            print(f"🔍 DEBUG: Found payment? {recent_payment is not None}")
            if recent_payment:
                print(f"🔍 DEBUG: Updating payment ID {recent_payment.id} to MANUAL_PROCESSED")
                recent_payment.result = "MANUAL_PROCESSED"
                recent_payment.note = (recent_payment.note or "") + " [Email not found in inbox - already archived or deleted]"
                db.session.commit()
                print(f"✅ DEBUG: Database committed successfully")
                # Return success so page refreshes and button disappears
                return True, "Email not found in inbox (already archived). Database updated."
            else:
                print(f"⚠️ DEBUG: Payment record not found in database")
                return False, "Payment record not found in database"

        # Create manually_processed folder if it doesn't exist
        try:
            result, folder_list = mail.list()
            folder_exists = False
            if result == 'OK':
                for folder_info in folder_list:
                    if folder_info and manually_processed_folder in (folder_info.decode() if isinstance(folder_info, bytes) else folder_info):
                        folder_exists = True
                        break

            if not folder_exists:
                mail.create(manually_processed_folder)
        except Exception as e:
            print(f"Warning: Could not create folder: {e}")

        # Move email to manually_processed folder
        copy_result = mail.uid("COPY", uid_to_move, manually_processed_folder)
        if copy_result[0] == 'OK':
            mail.uid("STORE", uid_to_move, "+FLAGS", "(\\Deleted)")
            mail.expunge()

            # Update the most recent NO_MATCH entry for this payment
            recent_payment = EbankPayment.query.filter(
                EbankPayment.bank_info_name == bank_info_name,
                EbankPayment.bank_info_amt == bank_info_amt,
                EbankPayment.from_email == from_email,
                EbankPayment.result == "NO_MATCH"
            ).order_by(EbankPayment.timestamp.desc()).first()

            if recent_payment:
                # Change status to MANUAL_PROCESSED so it no longer shows Archive button
                recent_payment.result = "MANUAL_PROCESSED"
                recent_payment.note = (recent_payment.note or "") + f" [Email manually archived to {manually_processed_folder} folder]"
                db.session.commit()

            mail.logout()
            return True, f"Email successfully moved to {manually_processed_folder} folder"
        else:
            mail.logout()
            return False, f"Failed to move email: {copy_result}"

    except Exception as e:
        return False, f"Error: {str(e)}"


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
            # Skip specific API call logs that clutter the dashboard
            if ("API Call: GET get_kpi_data_api" in a.action or 
                "API Call: GET get_activity_dashboard_data" in a.action):
                continue
                
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
                # NEW: Show bank name and match score for transparency
                bank_name = p.bank_info_name or "Unknown"
                match_score = f"{p.name_score:.1f}" if p.name_score else "N/A"

                # NEW: Get activity name from the matched passport
                activity_name = ""
                if p.matched_pass_id:
                    from models import Passport
                    passport = db.session.get(Passport, p.matched_pass_id)
                    if passport and passport.activity:
                        activity_name = f" for Activity '{passport.activity.name}'"

                details = f"From {p.matched_name}, Amount: ${p.bank_info_amt:.2f} (Bank: '{bank_name}' matched at {match_score}%){activity_name}, Passport ID: {p.matched_pass_id}"
            elif p.result == "MANUAL_PROCESSED":
                log_type = "Payment Manually Processed"
                details = f"From {p.bank_info_name}, Amount: ${p.bank_info_amt:.2f} - Manually archived"
            else:
                log_type = "Payment No Match"
                details = f"From {p.bank_info_name}, Amount: ${p.bank_info_amt:.2f}"
                # NEW: Include candidate info if available in note
                if p.note and "Closest:" in p.note:
                    details += f" - {p.note}"

            log_entry = {
                "timestamp": p.timestamp,
                "type": log_type,
                "user": p.from_email or "-",
                "details": details
            }

            # Add extra fields for Payment No Match entries (for Archive Email button)
            # Do NOT add these for MANUAL_PROCESSED - we don't want the button to show
            if log_type == "Payment No Match":
                log_entry["bank_info_name"] = p.bank_info_name or ""
                log_entry["bank_info_amt"] = str(p.bank_info_amt) if p.bank_info_amt else ""
                log_entry["from_email"] = p.from_email or ""

            logs.append(log_entry)


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
        "unsubscribe_url": "",  # Will be filled by send_email with subdomain
        "privacy_url": "",      # Will be filled by send_email with subdomain
        "activity_name": activity.name if activity else "",
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


def send_email(subject, to_email, template_name=None, context=None, inline_images=None, html_body=None, timestamp_override=None, email_config=None, use_hosted_images=False, user=None, activity=None):
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

    # ✅ Check if user has opted out of emails
    from models import User
    email_user = User.query.filter_by(email=to_email).first()
    if email_user and email_user.email_opt_out:
        print(f"⚠️ Email blocked: {to_email} has opted out")
        return False
    
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

    # ✅ ORGANIZATION DETECTION & SUBDOMAIN-AWARE URLs
    from models import Organization
    from flask import session
    org = None
    
    # Priority 1: Get organization from activity parameter (most reliable)
    if activity and hasattr(activity, 'organization') and activity.organization:
        org = activity.organization
        print(f"📧 Using organization from activity: {org.name}")
    # Priority 2: Get from context
    elif context and 'organization_id' in context:
        org = db.session.get(Organization, context['organization_id'])
        print(f"📧 Using organization from context: {org.name if org else 'None'}")
    # Priority 3: Try session (for non-activity emails)
    else:
        # Safe session access for background threads
        try:
            if 'organization_domain' in session:
                org = Organization.query.filter_by(domain=session['organization_domain']).first()
                print(f"📧 Using organization from session: {org.name if org else 'None'}")
        except RuntimeError:
            # Working outside request context - skip session access
            pass
    
    # Generate URLs and organization info with proper data
    if org:
        # Use organization's actual domain
        base_url = f"https://{org.domain}.minipass.me" if org.domain else "https://minipass.me"
        context['organization_name'] = org.name
    else:
        # Fallback for system emails without organization context
        base_url = "https://lhgi.minipass.me"
        context['organization_name'] = "Foundation LHGI"
    
    # Use ORG_ADDRESS setting for address (consistent with survey code)
    context['organization_address'] = get_setting('ORG_ADDRESS', '821 rue des Sables, Rimouski, QC G5L 6Y7')
    
    # Always set these URLs and support email
    context['unsubscribe_url'] = f"{base_url}/unsubscribe?email={to_email}"
    context['privacy_url'] = f"{base_url}/privacy"
    context['base_url'] = base_url
    
    # Add support_email using MAIL_DEFAULT_SENDER setting
    context['support_email'] = get_setting("MAIL_DEFAULT_SENDER") or "lhgi@minipass.me"
    
    # Debug: Print context variables for ALL emails
    print(f"📧 SEND_EMAIL DEBUG - Template: {template_name}")
    print(f"  support_email: {context.get('support_email', 'MISSING!')}")
    print(f"  organization_name: {context.get('organization_name', 'MISSING!')}")
    print(f"  unsubscribe_url: {context.get('unsubscribe_url', 'MISSING!')}")
    print(f"  privacy_url: {context.get('privacy_url', 'MISSING!')}")
    print(f"  activity provided: {activity is not None}")
    print(f"  org detected: {org.name if org else 'None'}")
    
    # Debug: Print context variables for signup emails
    if template_name and 'signup' in template_name:
        print(f"📧 SIGNUP EMAIL DEBUG:")
        print(f"  support_email: {context['support_email']}")
        print(f"  organization_name: {context['organization_name']}")
        print(f"  unsubscribe_url: {context['unsubscribe_url']}")
        print(f"  privacy_url: {context['privacy_url']}")
    
    # Ensure activity_name is set for footer text
    if activity and not context.get('activity_name'):
        context['activity_name'] = activity.name
    
    print(f"📧 Email context: org={context['organization_name']}, base_url={base_url}, activity={context.get('activity_name', 'None')}")
    
    # Note: activity_name should be provided by the calling function - no fallback needed
    
    print(f"🏢 Organization detected: {org.name if org else 'None'}")
    print(f"🌐 Base URL: {base_url}")
    
    # ✅ PHASE 3: Hosted Image System
    if use_hosted_images:
        # Generate hosted image URLs instead of inline data
        image_urls = generate_image_urls(context, base_url)
        context.update(image_urls)
        
        print(f"🖼️ Using hosted images: {len(image_urls)} URLs generated")
        
        # Clear inline images for hosted mode
        inline_images = {}
    else:
        print(f"📎 Using inline images: {len(inline_images)} embedded")
    
    sys.stdout.flush()

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

    # ✅ PHASE 2: Dynamic subject line generation
    def generate_dynamic_subject(original_subject, template_name, context):
        """Generate context-aware subject lines - ONLY as fallback when no custom subject"""
        
        # Check if this is a custom subject (user-defined) vs default fallback
        # Custom subjects should NEVER be overridden
        default_fallbacks = [
            "Minipass Notification",
            "[Minipass]",
            "Confirmation d'inscription", 
            "Registration confirmation",
            "Payment confirmed",
            "Pass redeemed",
            "Payment reminder",
            "We'd love your feedback"
        ]
        
        # If original_subject is not a default fallback, it's a custom subject - keep it as-is
        is_custom_subject = not any(fallback in original_subject for fallback in default_fallbacks)
        if is_custom_subject:
            return original_subject
        
        # Only use dynamic templates for default fallback subjects
        subject_templates = {
            'newPass': 'Your digital pass is ready',
            'paymentReceived': 'Payment confirmed - Pass activated', 
            'signup': 'Registration confirmation',
            'redeemPass': 'Pass redeemed successfully',
            'latePayment': 'Payment reminder',
            'email_survey_invitation': 'We\'d love your feedback'
        }
        
        # Extract template type from template_name
        template_type = None
        if template_name:
            if 'newPass' in template_name:
                template_type = 'newPass'
            elif 'paymentReceived' in template_name:
                template_type = 'paymentReceived'
            elif 'signup' in template_name:
                template_type = 'signup'
            elif 'redeemPass' in template_name:
                template_type = 'redeemPass'
            elif 'latePayment' in template_name:
                template_type = 'latePayment'
            elif 'survey' in template_name:
                template_type = 'email_survey_invitation'
        
        # Use template-based subject only for fallback cases
        if template_type and template_type in subject_templates:
            return subject_templates[template_type]
        
        return original_subject
    
    # Generate dynamic subject if template and context available
    subject = generate_dynamic_subject(subject, template_name, context)

    # Build email
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["To"] = to_email

    from_email = get_setting("MAIL_DEFAULT_SENDER") or "noreply@minipass.me"
    sender_name = get_setting("MAIL_SENDER_NAME") or "Minipass"
    msg["From"] = formataddr((sender_name, from_email))
    
    # ✅ Add deliverability headers
    reply_to_email = from_email
    msg["Reply-To"] = reply_to_email
    msg["List-Unsubscribe"] = f"<{context['unsubscribe_url']}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg["Precedence"] = "bulk"
    msg["X-Mailer"] = "Minipass/1.0"
    
    # Generate unique Message-ID
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000000)  # microsecond precision
    msg["Message-ID"] = f"<{timestamp}@minipass.me>"
    
    # Add organization tracking if available
    if hasattr(context, 'get') and context.get('organization_id'):
        msg["X-Entity-Ref-ID"] = str(context['organization_id'])

    alt_part = MIMEMultipart("alternative")
    
    # ✅ PHASE 2: Generate comprehensive plain text from HTML
    def generate_plain_text(html_content, context):
        """Generate comprehensive plain text from HTML"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and preserve structure
            text = soup.get_text(separator='\n', strip=True)
            
            # Add important links in parentheses (only unsubscribe and important links)
            for link in soup.find_all('a', href=True):
                if 'unsubscribe' in link.get('href', '').lower() or 'privacy' in link.get('href', '').lower():
                    link_text = link.get_text(strip=True)
                    if link_text and link_text not in text:
                        text += f"\n\n{link_text}: {link['href']}"
            
            # Clean up extra whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
            
        except ImportError:
            # Fallback if BeautifulSoup not available
            return context.get('preview_text', context.get('heading', 'Your digital pass is ready'))
    
    # Generate plain text from HTML content
    if final_html:
        plain_text = generate_plain_text(final_html, context)
    else:
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
                part.add_header("Content-Disposition", "inline")
                # Debug: Log what we're attaching
                print(f"📎 Attaching inline image: {cid} (size: {len(img_data)} bytes)")
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
                        'survey_invitation': 'survey_invitation',
                        'email_templates/email_survey_invitation/index.html': 'survey_invitation',
                        'email_templates/email_survey_invitation_compiled/index.html': 'survey_invitation',
                        'email_survey_invitation': 'survey_invitation'
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

                # --- Determine organization from context ---
                org_id = None
                if activity and hasattr(activity, 'organization_id'):
                    org_id = activity.organization_id
                elif organization_id:
                    org_id = organization_id
                
                # Add organization_id to context for proper URL generation
                if org_id and 'organization_id' not in context:
                    context['organization_id'] = org_id
                
                # --- Send the email ---
                send_email(
                    subject=subject,
                    to_email=to_email,
                    template_name=template_name,
                    context=context,
                    inline_images=inline_images,
                    html_body=html_body,
                    timestamp_override=timestamp_override,
                    user=user,
                    activity=activity
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

    # Get passport type information if available
    passport_type = None
    if hasattr(signup, 'passport_type_id') and signup.passport_type_id:
        from models import PassportType
        passport_type = db.session.get(PassportType, signup.passport_type_id)

    # Check if activity has custom signup template
    has_custom_template = (activity.email_templates and 
                          'signup' in activity.email_templates and 
                          activity.email_templates['signup'])
    
    # If no custom template (reset/default state), use regular email path
    if not has_custom_template:
        # Use the standard send_email function with compiled template
        send_email_async(
            app=app,
            user=signup.user,
            activity=activity,
            subject="Confirmation d'inscription",
            to_email=signup.user.email,
            template_name="signup_compiled/index.html",
            context={
                "user_name": signup.user.name,
                "user_email": signup.user.email,
                "phone_number": signup.user.phone_number,
                "activity_name": activity.name,
                "activity_price": f"${passport_type.price_per_user:.2f}" if passport_type else "$0.00",
                "sessions_included": passport_type.sessions_included if passport_type else 1,
                "payment_instructions": passport_type.payment_instructions if passport_type else "",
                "title": "Votre Inscription est Confirmée",
                "intro_text": "Merci de vous être inscrit!",
                "conclusion_text": "Nous vous contacterons bientôt.",
                "logo_url": "/static/uploads/logo.png",
            },
            timestamp_override=timestamp
        )
        return
    
    # Build base context for custom templates
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
    theme = "signup_compiled/index.html"

    # Render intro and conclusion manually
    intro = render_template_string(intro_raw, user_name=signup.user.name, activity_name=activity.name)
    conclusion = render_template_string(conclusion_raw, user_name=signup.user.name, activity_name=activity.name)

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
    
    # Add organization variables for footer
    context['organization_name'] = activity.organization.name if activity.organization else "Fondation LHGI"
    context['organization_address'] = "821 rue des Sables, Rimouski, QC G5L 6Y7"

    # Find compiled template
    # For signup, theme is already "signup_compiled/index.html"
    if "_compiled" in theme:
        # Already pointing to compiled version
        template_dir = theme.replace("/index.html", "")
        compiled_folder = os.path.join("templates/email_templates", template_dir)
    else:
        # Legacy path for non-compiled templates
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
        
        # 🚫 DO NOT add logo attachments to signup emails
        # Signup emails should not have logo attachments - they're meant to be clean celebration emails
        # Logo is already embedded in the compiled template if needed
        
        # Don't replace hero image for signup emails - use the compiled template's celebration image
        
        send_email_async(
            app=app,
            user=signup.user,
            activity=activity,
            subject=subject,
            to_email=signup.user.email,
            template_name="signup_compiled/index.html",
            context=context,
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
    
    # Check if activity has custom template for this event type
    has_custom_template = (activity.email_templates and 
                          template_type in activity.email_templates and 
                          activity.email_templates[template_type])
    
    # If no custom template (reset/default state), use regular email path
    if not has_custom_template:
        # Map event type to compiled template paths
        template_mapping = {
            'pass_created': 'newPass_compiled/index.html',
            'payment_received': 'paymentReceived_compiled/index.html',
            'payment_late': 'latePayment_compiled/index.html',
            'pass_redeemed': 'redeemPass_compiled/index.html'
        }
        template_name = template_mapping.get(event_type, 'newPass_compiled/index.html')
        
        # Use the standard send_email function with compiled template
        send_email_async(
            app=app,
            user=pass_data.user,
            activity=activity,
            subject=f"[{activity.organization.name if activity and activity.organization else 'Foundation LHGI'}] {event_type.title()} Notification",
            to_email=pass_data.user.email,
            template_name=template_name,
            context={
                "pass_data": pass_data,
                "title": f"{event_type.title()} Confirmation",
                "intro_text": "Your pass has been updated.",
                "conclusion_text": f"Thank you for using {activity.organization.name if activity and activity.organization else 'Foundation LHGI'}!",
                "owner_html": render_template("email_blocks/owner_card_inline.html", pass_data=pass_data),
                "history_html": render_template("email_blocks/history_table_inline.html", history=get_pass_history_data(pass_data.pass_code, fallback_admin_email=admin_email)),
                "activity_name": activity.name if activity else "",
                "qr_code": generate_qr_code_image(pass_data.pass_code).read(),
            },
            timestamp_override=timestamp,
            inline_images={"qr_code": generate_qr_code_image(pass_data.pass_code).read()}
        )
        return
    
    # Build base context for custom templates
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
        "special_message": "",
        "activity_name": activity.name if activity else "",
        "unsubscribe_url": "",  # Will be filled by send_email with subdomain
        "privacy_url": "",      # Will be filled by send_email with subdomain
    }
    
    # Add organization variables for footer
    context['organization_name'] = activity.organization.name if activity.organization else "Fondation LHGI"
    context['organization_address'] = "821 rue des Sables, Rimouski, QC G5L 6Y7"

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
    
    # Use new hero image selection system
    hero_data, is_custom, is_template_default = get_activity_hero_image(activity, template_type)
    if hero_data and not is_template_default:
        # Replace template images with custom uploads or activity fallbacks
        # Template defaults are already loaded in inline_images from the JSON
        hero_cid_map = {
            'newPass': 'hero_new_pass',
            'paymentReceived': 'hero_payment_received', 
            'latePayment': 'hero_late_payment',
            'signup': 'hero_signup',
            'waitlist': 'hero_waitlist'
        }
        
        hero_cid = hero_cid_map.get(template_type)
        if hero_cid:
            inline_images[hero_cid] = hero_data  # Replace template default with custom/fallback
            hero_type = "custom" if is_custom else "activity fallback"
            print(f"✅ {hero_type} hero image applied: template={template_type}, cid={hero_cid}")
        else:
            print(f"⚠️ No CID mapping for template type: {template_type}")
    elif hero_data and is_template_default:
        print(f"📦 Using template default hero for {template_type} (already loaded)")
    else:
        print(f"📦 No hero image found for {template_type}")
    
    # Check for activity-specific owner logo (replaces 'logo' CID)
    activity_id = pass_data.activity.id if pass_data.activity else None
    logo_used = False
    if activity_id:
        activity_logo_path = os.path.join("static/uploads", f"{activity_id}_owner_logo.png")
        if os.path.exists(activity_logo_path):
            logo_data = open(activity_logo_path, "rb").read()
            inline_images['logo'] = logo_data  # For owner_card_inline.html
            print(f"Using activity-specific owner logo: {activity_id}_owner_logo.png")
            logo_used = True
    
    # Fallback to organization logo if no activity-specific logo
    if not logo_used:
        from utils import get_setting
        org_logo_filename = get_setting('LOGO_FILENAME', 'logo.png')
        org_logo_path = os.path.join("static/uploads", org_logo_filename)
        
        if os.path.exists(org_logo_path):
            logo_data = open(org_logo_path, "rb").read()
            inline_images['logo'] = logo_data  # For owner_card_inline.html
            print(f"Using organization logo: {org_logo_filename}")
        else:
            # Final fallback to default logo
            logo_data = open("static/uploads/logo.png", "rb").read()
            inline_images['logo'] = logo_data
            print("Using default Minipass logo")

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
            org = db.session.get(Organization, organization_id)
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
        org = db.session.get(Organization, organization_id)
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
        org = db.session.get(Organization, organization_id)
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

    # Add activity logo URL if not already provided in context
    # (URL should be built in request context before calling get_email_context)
    if 'activity_logo_url' not in context:
        # Fallback: try to build URL (only works in request context)
        try:
            if activity and activity.logo_filename:
                context['activity_logo_url'] = url_for('static', filename=f'uploads/logos/{activity.logo_filename}')
            else:
                # Use organization logo from settings instead of hardcoded Minipass logo
                org_logo = get_setting('LOGO_FILENAME', 'logo.png')
                context['activity_logo_url'] = url_for('static', filename=f'uploads/{org_logo}')
        except RuntimeError:
            # url_for() failed (not in request context) - use relative path as fallback
            if activity and activity.logo_filename:
                context['activity_logo_url'] = f'/static/uploads/logos/{activity.logo_filename}'
            else:
                org_logo = get_setting('LOGO_FILENAME', 'logo.png')
                context['activity_logo_url'] = f'/static/uploads/{org_logo}'

    return context


def get_template_hero_dimensions(template_type):
    """
    Get the expected dimensions for hero images based on template type.
    Returns (width, height) tuple or None if template doesn't use hero images.
    """
    # Template-specific hero image dimensions based on original template assets
    hero_dimensions = {
        'newPass': (1408, 768),      # Wide banner format
        'signup': (1600, 1200),      # Large hero format
        'welcome': (1408, 768),      # Same as newPass
        'renewal': (1408, 768),      # Same as newPass
        # Note: other templates (latePayment, paymentReceived, redeemPass) use small icons (128x128), not heroes
    }
    
    return hero_dimensions.get(template_type)

def resize_hero_image(image_data, template_type, max_file_size_mb=2):
    """
    Resize uploaded hero image to match the original template dimensions.
    
    Args:
        image_data: Raw image bytes
        template_type: Template type (e.g., 'newPass', 'signup')
        max_file_size_mb: Maximum file size in MB
    
    Returns:
        tuple: (resized_image_bytes, success_message) or (None, error_message)
    """
    try:
        from PIL import Image
        import io
        
        # Check file size
        if len(image_data) > max_file_size_mb * 1024 * 1024:
            return None, f"Image file too large. Maximum size is {max_file_size_mb}MB"
        
        # Get expected dimensions for this template type
        target_dimensions = get_template_hero_dimensions(template_type)
        if not target_dimensions:
            return None, f"Template type '{template_type}' does not support custom hero images"
        
        target_width, target_height = target_dimensions
        
        # Open and validate the image
        try:
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            return None, f"Invalid image file: {str(e)}"
        
        # Convert to RGB if needed (removes alpha channel for consistency)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        original_width, original_height = image.size
        print(f"🖼️ Resizing hero image: {original_width}x{original_height} → {target_width}x{target_height}")
        
        # Resize image to exact template dimensions
        # Use LANCZOS for high-quality resizing
        resized_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Save to bytes
        output_buffer = io.BytesIO()
        resized_image.save(output_buffer, format='PNG', optimize=True)
        resized_bytes = output_buffer.getvalue()
        
        print(f"🖼️ Hero image resized successfully: {len(image_data)} → {len(resized_bytes)} bytes")
        
        return resized_bytes, f"Image resized to {target_width}x{target_height} pixels"
        
    except ImportError:
        return None, "PIL (Pillow) library not available for image processing"
    except Exception as e:
        return None, f"Error resizing image: {str(e)}"


# ================================
# 📊 FINANCIAL REPORTING FUNCTIONS
# ================================

def get_financial_data(start_date=None, end_date=None, activity_id=None):
    """
    Aggregate financial data from Passport sales, Income, and Expenses.

    Args:
        start_date: datetime object for start of period (UTC, optional)
        end_date: datetime object for end of period (UTC, optional)
        activity_id: Optional activity ID to filter by specific activity

    Returns:
        dict: Financial data with summary and by-activity breakdown
    """
    from models import Passport, Income, Expense, Activity, User
    from sqlalchemy import func
    from datetime import datetime, timezone

    # Default to all-time if no dates provided
    if not start_date:
        start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    # Ensure dates are timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    # Build base queries with date filtering
    passport_query = db.session.query(Passport).filter(
        Passport.created_dt >= start_date,
        Passport.created_dt <= end_date
    )
    income_query = db.session.query(Income).filter(
        Income.date >= start_date,
        Income.date <= end_date
    )
    expense_query = db.session.query(Expense).filter(
        Expense.date >= start_date,
        Expense.date <= end_date
    )

    # Apply activity filter if provided
    if activity_id:
        passport_query = passport_query.filter(Passport.activity_id == activity_id)
        income_query = income_query.filter(Income.activity_id == activity_id)
        expense_query = expense_query.filter(Expense.activity_id == activity_id)

    # Get all activities involved
    if activity_id:
        activities = [db.session.get(Activity, activity_id)]
    else:
        activity_ids = set()
        for p in passport_query.all():
            activity_ids.add(p.activity_id)
        for i in income_query.all():
            activity_ids.add(i.activity_id)
        for e in expense_query.all():
            activity_ids.add(e.activity_id)
        activities = [db.session.get(Activity, aid) for aid in activity_ids if db.session.get(Activity, aid)]

    # Initialize summary
    total_revenue = 0.0
    total_expenses = 0.0
    by_activity = []
    all_transactions = []

    # Process each activity
    for activity in activities:
        activity_revenue = 0.0
        activity_expenses = 0.0
        activity_transactions = []

        # Get passport sales for this activity
        passports = passport_query.filter(Passport.activity_id == activity.id).all()
        for passport in passports:
            user = db.session.get(User, passport.user_id) if passport.user_id else None
            transaction = {
                'date': passport.created_dt.strftime('%Y-%m-%d'),
                'datetime': passport.created_dt,
                'type': 'Income',
                'category': 'Passport Sales',
                'description': f"{passport.passport_type_name or 'Passport'} - {user.name if user else 'Unknown'}",
                'amount': float(passport.sold_amt or 0),
                'receipt_filename': None,
                'activity_id': activity.id,
                'activity_name': activity.name
            }
            activity_revenue += transaction['amount']
            activity_transactions.append(transaction)
            all_transactions.append(transaction)

        # Get other income for this activity
        incomes = income_query.filter(Income.activity_id == activity.id).all()
        for income in incomes:
            transaction = {
                'date': income.date.strftime('%Y-%m-%d'),
                'datetime': income.date,
                'type': 'Income',
                'category': income.category,
                'description': income.note or income.category,
                'amount': float(income.amount),
                'receipt_filename': income.receipt_filename,
                'activity_id': activity.id,
                'activity_name': activity.name
            }
            activity_revenue += transaction['amount']
            activity_transactions.append(transaction)
            all_transactions.append(transaction)

        # Get expenses for this activity
        expenses = expense_query.filter(Expense.activity_id == activity.id).all()
        for expense in expenses:
            transaction = {
                'date': expense.date.strftime('%Y-%m-%d'),
                'datetime': expense.date,
                'type': 'Expense',
                'category': expense.category,
                'description': expense.description or expense.category,
                'amount': float(expense.amount),
                'receipt_filename': expense.receipt_filename,
                'activity_id': activity.id,
                'activity_name': activity.name
            }
            activity_expenses += transaction['amount']
            activity_transactions.append(transaction)
            all_transactions.append(transaction)

        # Sort activity transactions by date (newest first)
        activity_transactions.sort(key=lambda x: x['datetime'], reverse=True)

        # Add to by_activity list
        by_activity.append({
            'activity_id': activity.id,
            'activity_name': activity.name,
            'activity_image': activity.image_filename or activity.logo_filename,
            'total_revenue': activity_revenue,
            'total_expenses': activity_expenses,
            'net_income': activity_revenue - activity_expenses,
            'transactions': activity_transactions
        })

        total_revenue += activity_revenue
        total_expenses += activity_expenses

    # Sort activities by revenue (highest first)
    by_activity.sort(key=lambda x: x['total_revenue'], reverse=True)

    # Sort all transactions by date (newest first)
    all_transactions.sort(key=lambda x: x['datetime'], reverse=True)

    # Determine period label
    if start_date.year == 2000 and end_date >= datetime.now(timezone.utc):
        period_label = 'All Time'
    else:
        period_label = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"

    return {
        'summary': {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': total_revenue - total_expenses,
            'period_label': period_label,
            'start_date': start_date,
            'end_date': end_date
        },
        'by_activity': by_activity,
        'all_transactions': all_transactions
    }


def export_financial_csv(financial_data):
    """
    Export financial data to CSV format compatible with all accounting software.

    Args:
        financial_data: dict from get_financial_data()

    Returns:
        str: CSV formatted string
    """
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Date', 'Activity', 'Type', 'Category', 'Description', 'Amount', 'Receipt'])

    # Write all transactions
    for transaction in financial_data['all_transactions']:
        writer.writerow([
            transaction['date'],
            transaction['activity_name'],
            transaction['type'],
            transaction['category'],
            transaction['description'],
            f"{transaction['amount']:.2f}",
            transaction['receipt_filename'] or 'N/A'
        ])

    return output.getvalue()


# ================================
# 👥 USER CONTACT REPORT FUNCTIONS
# ================================

def get_user_contact_report(activity_id=None, start_date=None, end_date=None,
                           exclude_opt_outs=False, sort_by='passports_desc'):
    """
    Generate user contact list with engagement metrics.

    Args:
        activity_id: Optional activity ID to filter users by participation
        start_date: datetime object for start of period (UTC, optional)
        end_date: datetime object for end of period (UTC, optional)
        exclude_opt_outs: Boolean to exclude users who opted out of emails
        sort_by: Sort order - 'passports_desc', 'revenue_desc', 'last_activity', 'name_asc'

    Returns:
        dict: User contact data with summary and user list
    """
    from models import User, Passport, Activity, Signup
    from sqlalchemy import func, desc, asc
    from datetime import datetime, timezone

    # Default to all-time if no dates provided
    if not start_date:
        start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    # Ensure dates are timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    # Build query aggregated by name + email (to avoid duplicates from multiple User records)
    query = db.session.query(
        User.name,
        User.email,
        func.max(User.phone_number).label('phone_number'),  # Take most recent phone
        func.max(User.email_opt_out).label('email_opt_out'),  # If ANY record opted out, show opted out
        func.count(Passport.id).label('passport_count'),
        func.coalesce(func.sum(Passport.sold_amt), 0).label('total_revenue'),
        func.max(Passport.created_dt).label('last_activity_date')
    ).outerjoin(Passport, User.id == Passport.user_id)

    # Apply date filter on passports
    query = query.filter(
        db.or_(
            Passport.created_dt.is_(None),
            db.and_(
                Passport.created_dt >= start_date,
                Passport.created_dt <= end_date
            )
        )
    )

    # Apply activity filter if provided
    if activity_id:
        query = query.filter(
            db.or_(
                Passport.activity_id.is_(None),
                Passport.activity_id == activity_id
            )
        )

    # Exclude email opt-outs if requested
    if exclude_opt_outs:
        query = query.filter(User.email_opt_out == False)

    # Group by name and email (aggregate duplicates)
    query = query.group_by(User.name, User.email)

    # Apply sorting
    if sort_by == 'passports_desc':
        query = query.order_by(desc('passport_count'), User.name)
    elif sort_by == 'revenue_desc':
        query = query.order_by(desc('total_revenue'), User.name)
    elif sort_by == 'last_activity':
        query = query.order_by(desc('last_activity_date'), User.name)
    elif sort_by == 'name_asc':
        query = query.order_by(User.name)

    # Execute query
    user_data = query.all()

    # Build user list with activity participation
    users = []
    total_users = 0
    active_users = 0
    total_revenue = 0

    for user in user_data:
        # Get all User IDs with this name/email combination
        user_ids = db.session.query(User.id).filter(
            User.name == user.name,
            User.email == user.email
        ).all()
        user_ids = [u[0] for u in user_ids]

        # Get activities for all these user IDs
        activities_query = db.session.query(
            Activity.name
        ).join(Passport, Activity.id == Passport.activity_id).filter(
            Passport.user_id.in_(user_ids)
        )

        if start_date and end_date:
            activities_query = activities_query.filter(
                Passport.created_dt >= start_date,
                Passport.created_dt <= end_date
            )

        if activity_id:
            activities_query = activities_query.filter(Activity.id == activity_id)

        activities_query = activities_query.distinct()
        user_activities = [a[0] for a in activities_query.all()]

        users.append({
            'name': user.name,
            'email': user.email or '',
            'phone': user.phone_number or '',
            'passport_count': user.passport_count,
            'total_revenue': float(user.total_revenue),
            'activities': ', '.join(user_activities) if user_activities else 'None',
            'last_activity_date': user.last_activity_date.strftime('%Y-%m-%d') if user.last_activity_date else 'N/A',
            'email_opt_out': user.email_opt_out
        })

        total_users += 1
        if user.passport_count > 0:
            active_users += 1
        total_revenue += float(user.total_revenue)

    # Get period label
    if start_date.year == 2000:
        period_label = "All Time"
    else:
        period_label = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

    # Get activity name if filtered
    activity_name = "All Activities"
    if activity_id:
        activity = db.session.get(Activity, activity_id)
        if activity:
            activity_name = activity.name

    return {
        'users': users,
        'summary': {
            'total_users': total_users,
            'active_users': active_users,
            'total_revenue': total_revenue,
            'avg_passports': round(sum(u['passport_count'] for u in users) / total_users, 1) if total_users > 0 else 0,
            'period_label': period_label,
            'activity_name': activity_name,
            'excluded_opt_outs': exclude_opt_outs,
            'sort_by': sort_by
        }
    }


def export_user_contacts_csv(user_data):
    """
    Export user contact data to CSV format.

    Args:
        user_data: dict from get_user_contact_report()

    Returns:
        str: CSV formatted string
    """
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Write metadata header
    writer.writerow([f"# User Contact List - Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"])
    writer.writerow([f"# Period: {user_data['summary']['period_label']}"])
    writer.writerow([f"# Activity: {user_data['summary']['activity_name']}"])
    writer.writerow([f"# Excluded Opt-Outs: {user_data['summary']['excluded_opt_outs']}"])
    writer.writerow([])  # Blank line

    # Write column headers
    writer.writerow([
        'Name',
        'Email',
        'Phone',
        'Passports',
        'Total Revenue',
        'Activities',
        'Last Activity',
        'Email Opt-Out'
    ])

    # Write user data
    for user in user_data['users']:
        writer.writerow([
            user['name'],
            user['email'],
            user['phone'],
            user['passport_count'],
            f"{user['total_revenue']:.2f}",
            user['activities'],
            user['last_activity_date'],
            'Yes' if user['email_opt_out'] else 'No'
        ])

    return output.getvalue()



