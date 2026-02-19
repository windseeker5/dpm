import smtplib
import qrcode
import base64
import io
import socket
import traceback
from functools import lru_cache

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from models import Setting, db, Passport, Redemption, Admin, EbankPayment, ReminderLog




import threading
import logging
from datetime import datetime
 
from flask import render_template, render_template_string, url_for, current_app, session


from pprint import pprint
from email.utils import parsedate_to_datetime
import imaplib
import email
import re


# ================================
# EMAIL TEMPLATE CONSTANTS
# ================================

# Hero image CID mappings for email templates (matches compiled template structure)
# This constant prevents code duplication and ensures consistency across all email functions
HERO_CID_MAP = {
    'newPass': 'hero_new_pass',
    'paymentReceived': 'currency-dollar',
    'latePayment': 'thumb-down',
    'signup': 'good-news',
    'signup_payment_first': 'good-news',
    'redeemPass': 'hand-rock',
    'survey_invitation': 'sondage'
}

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
import unicodedata


def normalize_name(text):
    """
    Normalize name for comparison: remove accents, lowercase, strip.

    This handles accent variations (Hélène vs Helene) and case differences.
    Used for payment matching and conflict detection.

    Args:
        text: Name string to normalize

    Returns:
        Normalized lowercase string without accents
    """
    if not text:
        return ""
    normalized = unicodedata.normalize('NFD', str(text))
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents.lower().strip()


def has_conflicting_unpaid_signup(signup, activity):
    """
    Check if there are OTHER unpaid signups for this activity
    with the same normalized name AND same requested_amount.

    This is used to determine if a signup code is needed for payment disambiguation.
    In 99% of cases, name + amount uniquely identifies the payer, so no code is needed.
    Only when there's a conflict (same name AND same amount) do we require the code.

    Args:
        signup: The Signup object to check
        activity: The Activity the signup belongs to

    Returns:
        True if there's a naming conflict requiring the signup code for disambiguation
    """
    from models import Signup

    current_name = normalize_name(signup.user.name)
    current_amount = signup.requested_amount or 0.0

    # Find other unpaid signups for same activity
    potential_conflicts = Signup.query.filter(
        Signup.activity_id == activity.id,
        Signup.id != signup.id,  # Exclude current
        Signup.paid == False,
        Signup.status.in_(['pending', 'approved'])
    ).all()

    # Check for same name AND same amount
    for other in potential_conflicts:
        other_name = normalize_name(other.user.name)
        other_amount = other.requested_amount or 0.0
        if current_name == other_name and abs(current_amount - other_amount) < 0.01:
            return True

    return False


@lru_cache(maxsize=20)
def get_template_default_hero(template_type):
    """
    Load the default hero image from compiled template's inline_images.json

    Note: Cached with @lru_cache for performance (avoids repeated JSON reads + base64 decoding)
    Use clear_hero_image_cache() to clear after updating templates
    
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
        'signup_payment_first': 'signup_payment_first_original',
        'redeemPass': 'redeemPass_original',
        'survey_invitation': 'survey_invitation_original'
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
        
        # Map template types to their hero image keys (as they actually appear in inline_images.json)
        hero_key_map = {
            'newPass': 'hero_new_pass',
            'paymentReceived': 'currency-dollar',
            'latePayment': 'thumb-down',
            'signup': 'good-news',
            'signup_payment_first': 'good-news',
            'redeemPass': 'hand-rock',
            'survey_invitation': 'sondage'
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


def clear_hero_image_cache():
    """
    Clear the lru_cache for get_template_default_hero.
    Call this after updating/recompiling email templates to ensure
    the latest hero images are used.
    """
    get_template_default_hero.cache_clear()
    print("✅ Hero image cache cleared")


def get_activity_hero_image(activity, template_type):
    """
    Hero image selection with CORRECT priority order:
    1. Custom uploaded hero (highest priority)
    2. Original template default (proper default)
    3. Activity image (ONLY if template has active customizations - NOT after reset)

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

    # Priority 3: Fall back to activity image ONLY if template has active customizations
    # (NOT after reset - this prevents showing activity image when user clicked "reset to default")
    if activity and activity.image_filename:
        # Check if this template has any customizations in the database
        has_customizations = False
        if activity.email_templates and template_type in activity.email_templates:
            template_data = activity.email_templates[template_type]
            # Check if there are any actual custom values (not just empty dict)
            customizable_fields = ['subject', 'title', 'intro_text', 'conclusion_text', 'hero_image', 'activity_logo']
            has_customizations = any(field in template_data and template_data[field] for field in customizable_fields)

        # Only use activity image if template was customized (user intentionally didn't upload hero)
        # Do NOT use activity image if template was reset or never customized
        if has_customizations:
            # Try both locations: main uploads and activity_images subdirectory
            activity_image_paths = [
                f"static/uploads/{activity.image_filename}",
                f"static/uploads/activity_images/{activity.image_filename}"
            ]

            for activity_image_path in activity_image_paths:
                if os.path.exists(activity_image_path):
                    with open(activity_image_path, "rb") as f:
                        print(f"⚠️ Using activity image as fallback hero for customized template {template_type}: {activity.image_filename}")
                        return f.read(), False, False  # is_template_default=False
        else:
            print(f"ℹ️ Template {template_type} has no customizations, skipping activity image fallback")

    # Priority 4: Generate placeholder cover from activity name
    if activity and activity.name:
        try:
            placeholder_buf = generate_placeholder_cover_image(activity.name)
            print(f"🎨 Using generated placeholder cover for activity '{activity.name}'")
            return placeholder_buf.read(), False, False
        except Exception as e:
            print(f"❌ Error generating placeholder cover: {e}")

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

    Priority order:
    1. Environment variable (from docker-compose)
    2. Database setting table
    3. Default value
    """
    import os

    # First check environment variables (from docker-compose)
    env_value = os.environ.get(key)
    if env_value is not None and env_value != "":
        return env_value

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


def get_remaining_capacity(activity_id):
    """
    Calculate remaining capacity for a quantity-limited activity.

    Returns the number of spots/sessions still available for signup.
    For non-limited activities, returns None.

    Args:
        activity_id: The activity ID to check capacity for

    Returns:
        int or None: Remaining spots, or None if not quantity-limited
    """
    from models import Activity, Passport
    from sqlalchemy import func

    activity = Activity.query.get(activity_id)
    if not activity or not activity.is_quantity_limited or not activity.max_sessions:
        return None

    # Sum all uses_remaining from active passports for this activity
    # This counts total sessions sold/reserved
    total_sold = db.session.query(func.coalesce(func.sum(Passport.uses_remaining), 0))\
        .filter(Passport.activity_id == activity_id)\
        .scalar()

    remaining = activity.max_sessions - total_sold
    return max(0, remaining)


def get_fiscal_year_range(reference_date=None):
    """
    Get the start and end dates for the fiscal year containing the reference date.
    Uses FISCAL_YEAR_START_MONTH setting (default: 1 = January = calendar year).

    Args:
        reference_date: Date to find fiscal year for (default: today)

    Returns:
        tuple: (start_date, end_date) as datetime objects with UTC timezone
    """
    from datetime import datetime, timezone

    if reference_date is None:
        reference_date = datetime.now(timezone.utc)

    # Get fiscal year start month from settings (default: 1 = January)
    try:
        start_month = int(get_setting("FISCAL_YEAR_START_MONTH", "1"))
        if start_month < 1 or start_month > 12:
            start_month = 1
    except (ValueError, TypeError):
        start_month = 1

    # Determine fiscal year based on reference date
    ref_month = reference_date.month
    ref_year = reference_date.year

    if ref_month >= start_month:
        # We're in the fiscal year that started this calendar year
        fy_start_year = ref_year
    else:
        # We're in the fiscal year that started last calendar year
        fy_start_year = ref_year - 1

    # Calculate start date (first day of start_month in fy_start_year)
    start_date = datetime(fy_start_year, start_month, 1, tzinfo=timezone.utc)

    # Calculate end date (last day before next fiscal year starts)
    if start_month == 1:
        # Calendar year: Jan 1 to Dec 31
        end_date = datetime(fy_start_year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    else:
        # Fiscal year: start_month/year to (start_month-1)/next_year
        end_year = fy_start_year + 1
        end_month = start_month - 1
        # Get last day of end_month
        if end_month in [1, 3, 5, 7, 8, 10, 12]:
            last_day = 31
        elif end_month in [4, 6, 9, 11]:
            last_day = 30
        else:  # February
            # Check for leap year
            if (end_year % 4 == 0 and end_year % 100 != 0) or (end_year % 400 == 0):
                last_day = 29
            else:
                last_day = 28
        end_date = datetime(end_year, end_month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    return start_date, end_date


def get_fiscal_year_display(reference_date=None):
    """
    Get a human-readable display string for the current fiscal year.

    Returns:
        str: e.g., "Jan 1, 2025 - Dec 31, 2025" or "Apr 1, 2025 - Mar 31, 2026"
    """
    start_date, end_date = get_fiscal_year_range(reference_date)
    return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"


def generate_pass_code():
    """
    Securely generates a random Pass Code for passports.
    Example Output: MP-8ab94c7efb29
    """
    return f"MP-{str(uuid.uuid4()).replace('-', '')[:12]}"



# ── Placeholder Gradients for Missing Activity Covers & Org Logos ──

PLACEHOLDER_GRADIENTS = [
    ('135deg', '#FF6B6B', '#EE5A24'),  # Coral
    ('135deg', '#0ABDE3', '#006266'),  # Ocean
    ('135deg', '#10AC84', '#01A3A4'),  # Forest
    ('135deg', '#9B59B6', '#6C3483'),  # Purple
    ('135deg', '#F39C12', '#E67E22'),  # Amber
    ('135deg', '#2C3E50', '#34495E'),  # Navy
    ('135deg', '#E84393', '#D63031'),  # Berry
    ('135deg', '#6C5CE7', '#4834D4'),  # Indigo
    ('135deg', '#00B894', '#00CEC9'),  # Emerald
    ('135deg', '#636E72', '#2D3436'),  # Slate
    ('135deg', '#B53471', '#6F1E51'),  # Wine
    ('135deg', '#0984E3', '#74B9FF'),  # Azure
]

PLACEHOLDER_SOLID_COLORS = [
    '#EE5A24', '#006266', '#01A3A4', '#6C3483',
    '#E67E22', '#34495E', '#D63031', '#4834D4',
    '#00CEC9', '#2D3436', '#6F1E51', '#0984E3',
]


def get_placeholder_index(name):
    if not name:
        return 0
    return sum(ord(c) for c in name.lower()) % len(PLACEHOLDER_GRADIENTS)


def get_placeholder_letter(name):
    if not name:
        return 'A'
    for c in name:
        if c.isalpha():
            return c.upper()
    return name[0].upper() if name else 'A'


def get_placeholder_css(name):
    idx = get_placeholder_index(name)
    angle, c1, c2 = PLACEHOLDER_GRADIENTS[idx]
    return f'linear-gradient({angle}, {c1} 0%, {c2} 100%)'


def get_placeholder_color(name):
    idx = get_placeholder_index(name)
    return PLACEHOLDER_SOLID_COLORS[idx]


def generate_placeholder_cover_image(name, width=800, height=400):
    from PIL import Image, ImageDraw, ImageFont
    idx = get_placeholder_index(name)
    _, c1_hex, c2_hex = PLACEHOLDER_GRADIENTS[idx]

    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    c1 = hex_to_rgb(c1_hex)
    c2 = hex_to_rgb(c2_hex)

    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / height
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    letter = get_placeholder_letter(name)
    try:
        font = ImageFont.truetype('/usr/share/fonts/TTF/Inter-Bold.ttf', int(height * 0.4))
    except (IOError, OSError):
        try:
            font = ImageFont.truetype('/usr/share/fonts/noto/NotoSans-Bold.ttf', int(height * 0.4))
        except (IOError, OSError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - tw) / 2 - bbox[0]
    y_pos = (height - th) / 2 - bbox[1]
    draw.text((x, y_pos), letter, fill=(255, 255, 255, 230), font=font)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def generate_placeholder_logo_image(name, size=200):
    from PIL import Image, ImageDraw, ImageFont
    idx = get_placeholder_index(name)
    color_hex = PLACEHOLDER_SOLID_COLORS[idx]

    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    color = hex_to_rgb(color_hex)

    img = Image.new('RGB', (size, size), color)
    draw = ImageDraw.Draw(img)

    letter = get_placeholder_letter(name)
    try:
        font = ImageFont.truetype('/usr/share/fonts/TTF/Inter-Bold.ttf', int(size * 0.5))
    except (IOError, OSError):
        try:
            font = ImageFont.truetype('/usr/share/fonts/noto/NotoSans-Bold.ttf', int(size * 0.5))
        except (IOError, OSError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), letter, fill=(255, 255, 255), font=font)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


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


def auto_create_passport_from_signup(signup, payment_record=None, marked_paid_by="minipass-bot@system"):
    """
    Create a passport automatically when payment matches a signup (payment-first workflow).

    This function is called by the payment matching logic when a payment is matched
    to a signup that doesn't have a passport yet.

    Args:
        signup: Signup model instance that has been paid
        payment_record: Optional EbankPayment record for tracking
        marked_paid_by: Who/what marked the payment as paid

    Returns:
        Passport: The newly created passport, or None if creation failed
    """
    from models import Passport, PassportType, Activity
    from datetime import datetime, timezone

    try:
        activity = Activity.query.get(signup.activity_id)
        if not activity:
            print(f"   [auto_create_passport] ERROR: Activity {signup.activity_id} not found")
            return None

        passport_type = None
        if signup.passport_type_id:
            passport_type = PassportType.query.get(signup.passport_type_id)

        # Generate unique pass code
        pass_code = generate_pass_code()

        # Create the passport
        now_utc = datetime.now(timezone.utc)
        passport = Passport(
            pass_code=pass_code,
            user_id=signup.user_id,
            activity_id=signup.activity_id,
            passport_type_id=signup.passport_type_id,
            passport_type_name=passport_type.name if passport_type else None,
            uses_remaining=signup.requested_sessions,
            sold_amt=signup.requested_amount,
            paid=True,
            paid_date=now_utc,
            marked_paid_by=marked_paid_by,
            created_dt=now_utc,
            notes=f"Auto-created from signup #{signup.id} (payment-first workflow)"
        )

        db.session.add(passport)
        db.session.flush()  # Get the passport ID

        # Link signup to passport
        signup.passport_id = passport.id
        signup.paid = True
        signup.paid_at = now_utc
        signup.status = "completed"

        db.session.commit()

        print(f"   [auto_create_passport] SUCCESS: Created passport {pass_code} for {signup.user.name}")
        print(f"      Sessions: {passport.uses_remaining}, Amount: ${passport.sold_amt}")

        # Note: Email notification is handled by the caller via notify_pass_event()
        # to use the standard paymentReceived template with QR code and history

        return passport

    except Exception as e:
        print(f"   [auto_create_passport] ERROR: {e}")
        db.session.rollback()
        return None


# ✅ PHASE 3: Optimized QR Code Generation & Hosted Image System
def get_pass_history_data(pass_code: str, fallback_admin_email=None) -> dict:
    """
    Builds the history log for a digital pass, converting UTC timestamps to local time (America/Toronto).
    Returns a dictionary including: created, paid, redemptions, expired, and who performed each action.

    Accepts fallback_admin_email for use in background tasks (outside of request context).
    """
    with current_app.app_context():
        from models import Admin, EbankPayment, Redemption, Passport
        DATETIME_FORMAT = "%Y-%m-%d %H:%M"

        # 🔍 Get passport
        passport = Passport.query.filter_by(pass_code=pass_code).first()

        if not passport:
            return {"error": "Pass not found."}

        # 🔁 Fetch redemptions
        redemptions = (
            Redemption.query
            .filter_by(passport_id=passport.id)
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
        created_dt = passport.created_dt
        if created_dt:
            history["created"] = utc_to_local(created_dt).strftime(DATETIME_FORMAT)

        # 👤 Created by
        if passport.created_by:
            admin = db.session.get(Admin, passport.created_by)
            history["created_by"] = admin.email if admin else "-"

        # 💵 Payment info
        paid = passport.paid
        paid_date = passport.paid_date

        if paid and paid_date:
            paid_dt = utc_to_local(paid_date)
            history["paid"] = paid_dt.strftime(DATETIME_FORMAT)

            # Check marked_paid_by field first
            if passport.marked_paid_by:
                # Use actual marked_paid_by from database
                history["paid_by"] = passport.marked_paid_by
            elif fallback_admin_email:
                # Fallback to session admin if available
                history["paid_by"] = fallback_admin_email
            else:
                # Last resort: indicate no audit trail
                history["paid_by"] = "system (no audit trail)"





        # 🎮 Redemptions
        for r in redemptions:
            local_used = utc_to_local(r.date_used)
            history["redemptions"].append({
                "date": local_used.strftime(DATETIME_FORMAT),
                "by": r.redeemed_by or "-"
            })

        # ❌ Expired if no uses remaining
        if passport.uses_remaining == 0 and redemptions:
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

            # 📧 Extract Reply-To header (real sender)
            reply_to_header = msg.get("Reply-To")
            reply_to_email = None
            if reply_to_header:
                reply_to_email = email.utils.parseaddr(reply_to_header)[1]
                if reply_to_email and '@' in reply_to_email:
                    print(f"📧 Reply-To found: {reply_to_email}")

            subject_raw = msg["Subject"]
            subject = email.header.decode_header(subject_raw)[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            # 📅 Extract email received date
            email_date_str = msg.get("Date")
            email_received_date = None
            if email_date_str:
                try:
                    # Parse email date to datetime object
                    email_received_date = parsedate_to_datetime(email_date_str)
                    # Convert to UTC if needed
                    if email_received_date.tzinfo is None:
                        email_received_date = email_received_date.replace(tzinfo=timezone.utc)
                    else:
                        email_received_date = email_received_date.astimezone(timezone.utc)
                except Exception as e:
                    print(f"⚠️ Could not parse email date '{email_date_str}': {e}")
                    email_received_date = None

            # 📝 Extract transfer message from email body (for signup code matching)
            transfer_message = None
            try:
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode('utf-8', errors='ignore')
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')

                # Extract message field from Interac email body
                # French: "Message :" or "Message de l'expéditeur:"
                if body:
                    message_match = re.search(r'Message\s*(?:de l[\'\u2019]exp[ée]diteur)?\s*:\s*["\']?(.+?)["\']?\s*(?:\n|$)', body, re.IGNORECASE)
                    if message_match:
                        transfer_message = message_match.group(1).strip()
                        print(f"📝 Transfer message found: '{transfer_message}'")
                    else:
                        print(f"⚠️ No transfer message found in email body")
                        print(f"   Body preview (first 500 chars): {body[:500] if body else 'EMPTY'}")
            except Exception as e:
                print(f"⚠️ Could not extract transfer message: {e}")

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
                "reply_to_email": reply_to_email,
                "uid": uid,
                "email_received_date": email_received_date,
                "transfer_message": transfer_message,
                "email_body": body  # Store full body for fallback signup code search
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
        period: Time period - '7d', '30d', '90d', 'fy' (fiscal year), or 'all'

    Returns:
        dict: KPI data with current values, previous values, changes, and trends
    """
    from datetime import datetime, timedelta, timezone
    from models import Passport, Signup, Income, Redemption, db
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
        elif period == 'fy':
            # Fiscal year period
            current_start, current_end_fy = get_fiscal_year_range()
            # Get previous fiscal year for comparison
            prev_fy_start, prev_fy_end = get_fiscal_year_range(current_start - timedelta(days=1))
            prev_start = prev_fy_start
            prev_end = prev_fy_end
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
        
        # KPI 1: Revenue - Using SQL views for consistency with Financial Report
        from sqlalchemy import text
        from models import Activity

        # Convert datetime ranges to date strings for view queries
        current_start_date = current_start.strftime('%Y-%m-%d')
        current_end_date = current_end.strftime('%Y-%m-%d')
        current_start_month = current_start.strftime('%Y-%m')
        current_end_month = current_end.strftime('%Y-%m')

        # Build query for current period using financial summary view
        revenue_query = """
            SELECT COALESCE(SUM(cash_received), 0) as total_revenue
            FROM monthly_financial_summary
            WHERE month >= :start_month AND month <= :end_month
        """
        params = {'start_month': current_start_month, 'end_month': current_end_month}

        # Add activity filter if specified
        if activity_id:
            activity = Activity.query.get(activity_id)
            if activity:
                revenue_query += " AND account = :activity_name"
                params['activity_name'] = activity.name

        # Execute query for current period
        result = db.session.execute(text(revenue_query), params)
        current_revenue = float(result.scalar() or 0)

        # Previous period revenue (if not 'all')
        if period != 'all':
            prev_start_month = prev_start.strftime('%Y-%m')
            prev_end_month = prev_end.strftime('%Y-%m')

            prev_params = {'start_month': prev_start_month, 'end_month': prev_end_month}
            if activity_id and activity:
                prev_params['activity_name'] = activity.name

            result = db.session.execute(text(revenue_query), prev_params)
            prev_revenue = float(result.scalar() or 0)

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

        # KPI 5: Passports Redeemed
        # Count redemptions by joining Redemption with Passport for activity filtering
        redemption_query = db.session.query(Redemption).join(Passport)
        if activity_id:
            redemption_query = redemption_query.filter(Passport.activity_id == activity_id)

        current_passports_redeemed = redemption_query.filter(
            Redemption.date_used >= current_start,
            Redemption.date_used <= current_end
        ).count()

        if period != 'all':
            prev_redemption_query = db.session.query(Redemption).join(Passport)
            if activity_id:
                prev_redemption_query = prev_redemption_query.filter(Passport.activity_id == activity_id)

            prev_passports_redeemed = prev_redemption_query.filter(
                Redemption.date_used >= prev_start,
                Redemption.date_used <= prev_end
            ).count()

            if prev_passports_redeemed > 0:
                passports_redeemed_change = ((current_passports_redeemed - prev_passports_redeemed) / prev_passports_redeemed * 100)
            elif current_passports_redeemed > 0:
                passports_redeemed_change = 100.0  # New redemptions, show as 100% increase
            else:
                passports_redeemed_change = 0
        else:
            prev_passports_redeemed = None
            passports_redeemed_change = None

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

        # Build redemptions trend (requires join with Passport for activity filtering)
        def build_redemptions_trend(days):
            trend_start = now - timedelta(days=days)

            query = db.session.query(
                func.date(Redemption.date_used).label('day'),
                func.count().label('count')
            ).join(Passport)

            if activity_id:
                query = query.filter(Passport.activity_id == activity_id)

            query = query.filter(
                Redemption.date_used >= trend_start,
                Redemption.date_used <= now
            )

            daily_counts = query.group_by(func.date(Redemption.date_used)).all()

            # Convert to dictionary for fast lookup
            count_dict = {str(row.day): row.count for row in daily_counts}

            # Build trend array
            trend = []
            for i in reversed(range(days)):
                day = (now - timedelta(days=i)).date()
                day_str = str(day)
                trend.append(count_dict.get(day_str, 0))
            return trend

        passports_redeemed_trend = build_redemptions_trend(trend_days)

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
            },
            'passports_redeemed': {
                'current': current_passports_redeemed,
                'previous': prev_passports_redeemed,
                'change': round(passports_redeemed_change, 1) if passports_redeemed_change is not None else None,
                'trend_data': passports_redeemed_trend
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

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        if force_send:
            print("🔧 FORCE_SEND mode: Will bypass 'already reminded' checks")

        unpaid_passports = Passport.query.filter(
            Passport.paid == False,
            Passport.created_dt <= cutoff_date
        ).all()

        for p in unpaid_passports:
            recent_reminder = ReminderLog.query.filter_by(passport_id=p.id)\
                .order_by(ReminderLog.reminder_sent_at.desc())\
                .first()

            if not force_send and recent_reminder and recent_reminder.reminder_sent_at > datetime.now(timezone.utc) - timedelta(days=days):
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
                    timestamp=datetime.now(timezone.utc)
                )
                
                # ✅ Only log to database AFTER email succeeds
                db.session.add(ReminderLog(
                    passport_id=p.id,
                    reminder_sent_at=datetime.now(timezone.utc)
                ))
                db.session.commit()
                print(f"✅ Email sent and logged for: {p.user.name if p.user else '-'}")
                
            except Exception as e:
                print(f"❌ Failed to send email to {p.user.name if p.user else '-'}: {e}")
                # No database log if email failed - will retry next time

def cleanup_duplicate_payment_logs_auto():
    """
    Auto-cleanup duplicate NO_MATCH payment logs.
    Called automatically by payment bot every 30 minutes.
    Keeps only the latest entry for each unique payment.
    """
    try:
        from models import EbankPayment, db

        # Find all NO_MATCH entries that are NOT the latest for each unique payment
        duplicates_query = db.session.query(EbankPayment).filter(
            EbankPayment.result == "NO_MATCH",
            EbankPayment.id.notin_(
                db.session.query(db.func.max(EbankPayment.id))
                .filter(EbankPayment.result == "NO_MATCH")
                .group_by(
                    EbankPayment.bank_info_name,
                    EbankPayment.bank_info_amt,
                    EbankPayment.from_email
                )
            )
        )

        duplicate_count = duplicates_query.count()

        if duplicate_count > 0:
            duplicates_query.delete(synchronize_session=False)
            db.session.commit()
            print(f"🧹 Auto-cleaned {duplicate_count} duplicate payment logs")
        else:
            print(f"✓ Auto-cleanup: No duplicates found (logs are clean)")

    except Exception as e:
        print(f"⚠️ Auto-cleanup error: {e}")
        db.session.rollback()


def match_gmail_payments_to_passes():
    from utils import extract_interac_transfers, get_setting, notify_pass_event
    from models import EbankPayment, Passport, Signup, db
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
        DIAGNOSTIC_MIN = 50  # Show candidates above 50% for context in diagnostic messages
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

        # Track results for flash message
        results = {"matched": 0, "no_match": 0, "skipped": 0, "emails_found": len(matches)}

        print(f"🔍 DEBUG: Found {len(matches)} email matches")
        for i, match in enumerate(matches):
            print(f"🔍 Email {i+1}: {match.get('subject', 'No subject')[:50]}...")

        for match in matches:
            name = match["bank_info_name"]
            amt = match["bank_info_amt"]
            from_email = match.get("from_email")
            reply_to_email = match.get("reply_to_email")  # Real sender from Reply-To header
            uid = match.get("uid")
            subject = match["subject"]
            email_received_date = match.get("email_received_date")  # Extract email received date
            transfer_message = match.get("transfer_message")  # Extract transfer message for signup code matching
            email_body = match.get("email_body", "")  # Store full body for fallback signup code search

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
                    # Check if this is truly the SAME email or a DIFFERENT payment
                    # Same person can pay same amount multiple times - compare email dates
                    is_same_email = False
                    if email_received_date and existing_payment.email_received_date:
                        # Ensure both datetimes are timezone-aware for comparison
                        new_date = email_received_date if email_received_date.tzinfo else email_received_date.replace(tzinfo=timezone.utc)
                        existing_date = existing_payment.email_received_date
                        if existing_date.tzinfo is None:
                            existing_date = existing_date.replace(tzinfo=timezone.utc)
                        time_diff = abs((new_date - existing_date).total_seconds())
                        is_same_email = time_diff < 300  # 5 minutes tolerance

                    if is_same_email:
                        # Check if this email has a DIFFERENT signup code - means it's a different payment
                        code_match = None
                        if transfer_message:
                            code_match = re.search(r'MP-INS-(\d{7})', transfer_message)
                        # FALLBACK: Search entire email body for signup code
                        if not code_match and email_body:
                            code_match = re.search(r'MP-INS-(\d{7})', email_body)

                        if code_match:
                            new_signup_code = f"MP-INS-{code_match.group(1)}"
                            # Check if we already matched THIS specific signup code
                            existing_for_code = EbankPayment.query.join(Passport).join(Signup).filter(
                                Signup.signup_code == new_signup_code,
                                EbankPayment.result == "MATCHED"
                            ).first()
                            if not existing_for_code:
                                print(f"🆕 DIFFERENT SIGNUP CODE: {new_signup_code} - processing as new payment")
                                # Don't skip - this is a different signup, fall through to process
                            else:
                                print(f"✅ ALREADY MATCHED THIS CODE: {new_signup_code}")
                                results["skipped"] += 1
                                continue
                        else:
                            # No signup code found anywhere - use normal duplicate logic
                            print(f"✅ ALREADY SUCCESSFULLY MATCHED: {name} - ${amt} from {from_email}")
                            print(f"   Processed on: {existing_payment.timestamp}")
                            print(f"   Matched to passport ID: {existing_payment.matched_pass_id}")
                            results["skipped"] += 1
                            continue
                    else:
                        print(f"🆕 NEW PAYMENT (different date): {name} - ${amt} from {from_email}")
                        print(f"   Existing payment date: {existing_payment.email_received_date}")
                        print(f"   New email date: {email_received_date}")
                        # Continue processing - this is a NEW payment from same person
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
                # No passport match found - check for payment-first signups
                print(f"\n🔍 No passport match - checking payment-first signups...")
                from models import Signup, Activity

                # Find signups without passports for payment-first activities
                unmatched_signups = db.session.query(Signup).join(Activity).filter(
                    Signup.passport_id == None,
                    Signup.requested_amount == payment_amount,
                    Activity.workflow_type == "payment_first"
                ).all()

                print(f"   Found {len(unmatched_signups)} unmatched payment-first signups for ${payment_amount:.2f}")

                best_signup = None
                best_signup_score = 0

                # STRATEGY: Name-first matching with signup code for disambiguation
                # - Most users (~60%) may forget to include the code
                # - Most names are unique → name matching works fine
                # - Signup code is a disambiguation tool, not the primary matcher

                # STEP 1: Collect ALL fuzzy name matches above threshold
                name_matches = []
                for s in unmatched_signups:
                    if not s.user:
                        continue
                    signup_name_normalized = normalize_name(s.user.name)
                    score = fuzz.ratio(normalized_payment_name, signup_name_normalized)
                    if score >= threshold:
                        name_matches.append((s, score))
                        print(f"   🔍 Name match: {s.user.name} (Score: {score}%)")

                print(f"   📊 Found {len(name_matches)} name matches above {threshold}% threshold")

                # STEP 2: Decide based on match count
                if len(name_matches) == 1:
                    # Single match → use it directly
                    best_signup = name_matches[0][0]
                    best_signup_score = name_matches[0][1]
                    print(f"   ✅ Single match: {best_signup.user.name}")

                elif len(name_matches) > 1:
                    # Multiple matches → check for ambiguity
                    scores = [score for _, score in name_matches]
                    score_range = max(scores) - min(scores)

                    if score_range < 5:  # Ambiguous - scores too close
                        print(f"   🚨 AMBIGUOUS: {len(name_matches)} matches with similar scores (range: {score_range}%)")
                        for s, score in name_matches:
                            print(f"      - {s.user.name}: {score}% (code: {s.signup_code})")

                        # Try to disambiguate using signup code
                        code_match = None
                        if transfer_message:
                            code_match = re.search(r'MP-INS-(\d{7})', transfer_message)

                        # FALLBACK: If not found in transfer_message, search entire email body
                        if not code_match and email_body:
                            print(f"   🔍 Searching full email body for signup code...")
                            code_match = re.search(r'MP-INS-(\d{7})', email_body)

                        if code_match:
                            signup_code = f"MP-INS-{code_match.group(1)}"
                            print(f"   🔑 Signup code found: {signup_code}")
                            # Find which candidate has this code
                            for s, score in name_matches:
                                if s.signup_code == signup_code:
                                    print(f"   ✅ DISAMBIGUATED by code: {signup_code}")
                                    best_signup = s
                                    best_signup_score = 100
                                    break

                        if not best_signup:
                            # Still ambiguous → flag for manual review (don't auto-match)
                            print(f"   ⚠️ Cannot disambiguate - needs manual review")
                    else:
                        # Clear winner by score
                        name_matches.sort(key=lambda x: -x[1])
                        best_signup = name_matches[0][0]
                        best_signup_score = name_matches[0][1]
                        print(f"   ✅ Clear winner: {best_signup.user.name} ({best_signup_score}%)")

                if best_signup:
                    print(f"\n✅ PAYMENT-FIRST SIGNUP MATCH: {best_signup.user.name} - ${best_signup.requested_amount}")
                    # Auto-create passport from signup
                    try:
                        from utils import auto_create_passport_from_signup
                        new_passport = auto_create_passport_from_signup(best_signup, marked_paid_by="minipass-bot@system")
                        if new_passport:
                            print(f"   ✅ Auto-created passport: {new_passport.pass_code}")
                            # Record the payment
                            db.session.add(EbankPayment(
                                from_email=from_email,
                                reply_to_email=reply_to_email,
                                subject=subject,
                                bank_info_name=name,
                                bank_info_amt=amt,
                                matched_pass_id=new_passport.id,
                                matched_name=best_signup.user.name,
                                matched_amt=best_signup.requested_amount,
                                name_score=best_signup_score,
                                result="MATCHED",
                                mark_as_paid=True,
                                note="Matched to signup (payment-first), auto-created passport.",
                                email_received_date=email_received_date
                            ))
                            db.session.commit()
                            results["matched"] += 1

                            # Send payment confirmation email to user
                            try:
                                now_utc = datetime.now(timezone.utc)
                                notify_pass_event(
                                    app=current_app._get_current_object(),
                                    event_type="payment_received",
                                    pass_data=new_passport,
                                    activity=new_passport.activity,
                                    admin_email="minipass-bot@system",
                                    timestamp=now_utc
                                )
                                print(f"   📧 Payment confirmation email sent to {new_passport.user.email}")
                            except Exception as email_error:
                                print(f"   ⚠️ Email notification failed: {email_error}")

                            # Move email to processed folder
                            if uid:
                                try:
                                    copy_result = mail.uid("COPY", uid, processed_folder)
                                    if copy_result[0] == 'OK':
                                        mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                                        print(f"   ✅ Email moved to {processed_folder}")
                                except Exception as e:
                                    print(f"   ⚠️ Could not move email: {e}")

                            continue  # Skip the "NO MATCH FOUND" block
                    except Exception as e:
                        print(f"   ❌ Error creating passport from signup: {e}")
                        db.session.rollback()

                # Still no match - log it
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
                try:
                    now_utc = datetime.now(timezone.utc)

                    print(f"\n{'='*80}")
                    print(f"🎯 MATCH FOUND - STARTING PAYMENT PROCESSING")
                    print(f"   Passport ID: {best_passport.id}")
                    print(f"   Pass Code: {best_passport.pass_code}")
                    print(f"   User: {best_passport.user.name if best_passport.user else 'NO USER'}")
                    print(f"   Amount: ${best_passport.sold_amt}")
                    print(f"{'='*80}\n")

                    # CRITICAL FIX: Move email BEFORE database commit (transaction safety)
                    # If email move fails, we skip the payment processing to prevent reprocessing
                    email_moved = False
                    if uid:
                        print(f"📧 STEP 1: Moving email to processed folder BEFORE DB commit")
                        try:
                            # Check if the processed folder exists, create if needed
                            folder_exists = False
                            result, folder_list = mail.list()
                            if result == 'OK':
                                for folder_info in folder_list:
                                    if folder_info:
                                        folder_str = folder_info.decode() if isinstance(folder_info, bytes) else folder_info
                                        if processed_folder in folder_str:
                                            folder_exists = True
                                            break

                            # Create folder if it doesn't exist
                            if not folder_exists:
                                print(f"📁 Creating folder: {processed_folder}")
                                try:
                                    mail.create(processed_folder)
                                except Exception as create_error:
                                    print(f"⚠️ Could not create folder {processed_folder}: {create_error}")

                            # Try to copy the email to the processed folder
                            copy_result = mail.uid("COPY", uid, processed_folder)
                            if copy_result[0] == 'OK':
                                # Only mark as deleted if copy was successful
                                mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                                email_moved = True
                                print(f"✅ Email moved to {processed_folder} folder")
                            else:
                                print(f"❌ Could not copy email to {processed_folder}: {copy_result}")
                                print(f"⚠️ SKIPPING payment processing - will retry on next run")
                        except Exception as e:
                            print(f"❌ Error moving email to processed folder: {e}")
                            print(f"⚠️ SKIPPING payment processing - will retry on next run")
                    else:
                        # No uid means this is a test/manual run, proceed without email move
                        email_moved = True
                        print(f"ℹ️ No email UID - proceeding without email move (test mode)")

                    # Only proceed with payment processing if email was moved (or no uid)
                    if not email_moved:
                        print(f"🔄 Payment skipped due to email move failure - will retry on next run")
                        continue

                    print(f"💾 STEP 2: Processing payment in database")
                    best_passport.paid = True
                    best_passport.paid_date = now_utc
                    best_passport.marked_paid_by = "minipass-bot@system"

                    print(f"🔍 PRE-COMMIT STATE:")
                    print(f"   passport.paid = {best_passport.paid}")
                    print(f"   passport.paid_date = {best_passport.paid_date}")
                    print(f"   passport.marked_paid_by = {repr(best_passport.marked_paid_by)}")

                    db.session.add(best_passport)

                    if update_existing_record and existing_payment:
                        # Update existing record instead of creating new one
                        existing_payment.matched_pass_id = best_passport.id
                        existing_payment.matched_name = best_passport.user.name
                        existing_payment.matched_amt = best_passport.sold_amt
                        existing_payment.name_score = best_score
                        existing_payment.result = "MATCHED"
                        existing_payment.mark_as_paid = True
                        existing_payment.note = "Matched by Minipass Bot (retry successful)."
                        existing_payment.timestamp = datetime.now(timezone.utc)
                        existing_payment.reply_to_email = reply_to_email
                        existing_payment.from_email = from_email
                        existing_payment.subject = subject
                        if email_received_date:
                            existing_payment.email_received_date = email_received_date
                        print(f"   📝 Updated existing EbankPayment record to MATCHED")
                    else:
                        # Create new record
                        print(f"   📝 Creating new EbankPayment MATCHED record")
                        db.session.add(EbankPayment(
                            from_email=from_email,
                            reply_to_email=reply_to_email,
                            subject=subject,
                            bank_info_name=name,
                            bank_info_amt=amt,
                            matched_pass_id=best_passport.id,
                            matched_name=best_passport.user.name,
                            matched_amt=best_passport.sold_amt,
                            name_score=best_score,
                            result="MATCHED",
                            mark_as_paid=True,
                            note="Matched by Minipass Bot.",
                            email_received_date=email_received_date
                        ))

                    print(f"🔍 PRE-FLUSH")
                    db.session.flush()  # Explicitly flush changes to session
                    print(f"✅ FLUSHED - changes written to session")

                    print(f"🔍 PRE-COMMIT")
                    db.session.commit()
                    print(f"✅ COMMITTED to database")

                    # Verify what actually persisted
                    db.session.expire(best_passport)
                    db.session.refresh(best_passport)
                    print(f"🔍 POST-COMMIT VERIFICATION (refreshed from DB):")
                    print(f"   passport.marked_paid_by = {repr(best_passport.marked_paid_by)}")

                    if best_passport.marked_paid_by != "minipass-bot@system":
                        print(f"❌ BUG DETECTED: marked_paid_by didn't persist!")
                        print(f"   Expected: 'minipass-bot@system'")
                        print(f"   Got: {repr(best_passport.marked_paid_by)}")
                    else:
                        print(f"✅ marked_paid_by persisted correctly")

                except Exception as e:
                    print(f"\n{'='*80}")
                    print(f"❌ EXCEPTION during payment processing for {name} (${amt})")
                    print(f"   Error: {e}")
                    print(f"{'='*80}")
                    import traceback
                    traceback.print_exc()
                    print(f"{'='*80}\n")

                    # Rollback the transaction
                    db.session.rollback()
                    print(f"🔄 Transaction rolled back")

                    # Continue to next payment
                    continue

                notify_pass_event(
                    app=current_app._get_current_object(),
                    event_type="payment_received",
                    pass_data=best_passport,  # ✅ update keyword
                    activity=best_passport.activity,
                    admin_email="minipass-bot@system",
                    timestamp=now_utc
                )

                # Emit SSE notification for payment
                try:
                    from api.notifications import emit_payment_notification
                    emit_payment_notification(best_passport)
                except Exception as e:
                    print(f"⚠️ Failed to emit payment notification: {e}")

                # Send push notification for successful payment match
                try:
                    send_push_notification_to_admins(
                        title=f"Payment Matched: ${amt:.2f}",
                        body=f"{best_passport.user.name} - {best_passport.activity.name}",
                        url=f"/payment-bot-matches?filter=matched",
                        tag=f"payment-{best_passport.id}"
                    )
                except Exception as e:
                    print(f"⚠️ Push notification error (payment match): {e}")

                # Track successful match
                results["matched"] += 1

                # Email was already moved BEFORE DB commit (see STEP 1 above)
                # This ensures transaction safety - if email move fails, payment isn't processed
            else:
                # NO MATCH FOUND in unpaid passports - Check if this is a duplicate payment for an already-paid passport
                print(f"\n❌ NO MATCH FOUND in unpaid passports")
                results["no_match"] += 1

                # Normalize payment name for comparison
                def normalize_for_comparison(text):
                    normalized = unicodedata.normalize('NFD', text)
                    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
                    return without_accents.lower().strip()

                payment_name_normalized = normalize_for_comparison(name)

                # Check if a PAID passport exists with matching amount and name (exact match only)
                all_paid = Passport.query.filter_by(paid=True).all()
                paid_passports_same_amount = [p for p in all_paid if float(p.sold_amt) == payment_amount]

                matching_paid_passport = None
                for p in paid_passports_same_amount:
                    if not p.user:
                        continue
                    passport_name_normalized = normalize_for_comparison(p.user.name)
                    # Use strict matching (95%+) to avoid false positives
                    score = fuzz.ratio(payment_name_normalized, passport_name_normalized)
                    if score >= 95:
                        matching_paid_passport = p
                        print(f"   ⚠️ Found PAID passport: {p.user.name} (Score: {score}%, Passport #{p.id})")
                        break

                # If found a matching PAID passport, this is likely a duplicate payment
                if matching_paid_passport:
                    # Found a matching PAID passport - provide detailed info
                    paid_by = matching_paid_passport.marked_paid_by or "unknown admin"
                    paid_date_str = matching_paid_passport.paid_date.strftime("%Y-%m-%d %H:%M") if matching_paid_passport.paid_date else "unknown date"

                    # Calculate time difference if both dates available
                    time_diff_info = ""
                    if matching_paid_passport.paid_date and email_received_date:
                        # Ensure both datetimes are timezone-aware for comparison
                        from datetime import timezone as tz
                        paid_dt = matching_paid_passport.paid_date if matching_paid_passport.paid_date.tzinfo else matching_paid_passport.paid_date.replace(tzinfo=tz.utc)
                        email_dt = email_received_date if email_received_date.tzinfo else email_received_date.replace(tzinfo=tz.utc)

                        diff_seconds = (email_dt - paid_dt).total_seconds()
                        if diff_seconds > 0:
                            diff_minutes = int(diff_seconds / 60)
                            time_diff_info = f" ({diff_minutes} min after passport marked paid)"
                        else:
                            diff_minutes = int(abs(diff_seconds) / 60)
                            time_diff_info = f" ({diff_minutes} min before email received)"

                    note_text = f"MATCH FOUND: {matching_paid_passport.user.name} (${payment_amount:.2f}, Passport #{matching_paid_passport.id}) - Already marked PAID by {paid_by} on {paid_date_str}{time_diff_info}"
                    print(f"   💡 Likely duplicate payment - passport already paid")
                else:
                    # Truly no match - create detailed diagnostic note
                    print(f"   💡 No paid passport match either - creating detailed NO_MATCH note")
                    all_candidates = []
                    for p in unpaid_passports:
                        if not p.user:
                            continue
                        score = fuzz.ratio(normalize_name(name), normalize_name(p.user.name))
                        if score >= DIAGNOSTIC_MIN:  # Only show candidates above 50% to avoid noise
                            all_candidates.append((p.user.name, score))

                    # Sort by score and take top 3
                    all_candidates.sort(key=lambda x: x[1], reverse=True)
                    top_candidates = all_candidates[:3]

                    # Build detailed note explaining why no match
                    note_parts = [f"No match found for '{name}' (${amt})."]

                    # Show how many unpaid passports exist for this amount
                    note_parts.append(f"Found {len(unpaid_passports)} unpaid passport(s) for ${amt}, but")

                    if top_candidates:
                        # Show the closest name matches and their scores
                        candidate_strs = [f"{cname} ({score:.0f}%)" for cname, score in top_candidates]
                        note_parts.append(f"all names below {threshold}% threshold. Closest: {', '.join(candidate_strs)}.")
                    else:
                        # No candidates above diagnostic threshold
                        note_parts.append(f"all names below {threshold}% threshold (no candidates above {DIAGNOSTIC_MIN}%).")
                        # Show a few example names for context
                        if unpaid_passports:
                            example_names = [p.user.name for p in unpaid_passports[:3] if p.user]
                            if example_names:
                                note_parts.append(f"Available names: {', '.join(example_names[:3])}")

                    note_text = " ".join(note_parts)
                
                if update_existing_record and existing_payment:
                    # Update existing record instead of creating new one
                    existing_payment.result = "NO_MATCH"
                    existing_payment.name_score = 0
                    existing_payment.mark_as_paid = False
                    existing_payment.note = note_text
                    existing_payment.timestamp = datetime.now(timezone.utc)
                    existing_payment.reply_to_email = reply_to_email
                    existing_payment.from_email = from_email
                    existing_payment.subject = subject
                    if email_received_date:
                        existing_payment.email_received_date = email_received_date
                    if uid:
                        existing_payment.email_uid = uid  # Store UID for moving email later
                    print(f"   📝 Updated existing NO_MATCH record")
                else:
                    # Create new record
                    db.session.add(EbankPayment(
                        from_email=from_email,
                        reply_to_email=reply_to_email,
                        subject=subject,
                        bank_info_name=name,
                        bank_info_amt=amt,
                        name_score=0,
                        result="NO_MATCH",
                        mark_as_paid=False,
                        note=note_text,
                        email_received_date=email_received_date,
                        email_uid=uid  # Store UID for moving email later
                    ))

                # Send push notification for NO_MATCH payment (needs manual review)
                try:
                    send_push_notification_to_admins(
                        title=f"Payment No Match: ${amt:.2f}",
                        body=f"From: {name} - needs manual review",
                        url=f"/payment-bot-matches?filter=no_match",
                        tag=f"nomatch-{name}-{amt}"
                    )
                except Exception as e:
                    print(f"⚠️ Push notification error (payment no-match): {e}")

        db.session.commit()
        mail.expunge()
        mail.logout()

        # Return results summary
        print(f"\n📊 PAYMENT BOT SUMMARY: {results['matched']} matched, {results['no_match']} no-match, {results['skipped']} skipped")
        return results


def move_payment_email_by_criteria(bank_info_name, bank_info_amt, from_email, custom_note=None):
    """
    Manually move a payment email to the manually_processed folder.
    Used when email wasn't automatically moved due to a glitch.

    Args:
        bank_info_name: Name from payment email
        bank_info_amt: Amount from payment email
        from_email: Email sender
        custom_note: Optional custom note to replace default reason

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

            # Email not in inbox - likely already archived
            # Update database to MANUAL_PROCESSED so button disappears
            recent_payment = EbankPayment.query.filter(
                EbankPayment.bank_info_name == bank_info_name,
                EbankPayment.bank_info_amt == float(bank_info_amt),
                EbankPayment.from_email == from_email,
                EbankPayment.result == "NO_MATCH"
            ).order_by(EbankPayment.timestamp.desc()).first()

            if recent_payment:
                recent_payment.result = "MANUAL_PROCESSED"
                # Use custom note if provided, otherwise use default
                if custom_note:
                    recent_payment.note = custom_note
                else:
                    recent_payment.note = (recent_payment.note or "") + " [Email not found in inbox - already archived or deleted]"
                db.session.commit()
                # Return success with helpful message
                return True, "Email already archived (not found in inbox). Record updated."
            else:
                return False, "Payment record not found in database"

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
                # Use custom note if provided, otherwise use default
                if custom_note:
                    recent_payment.note = custom_note
                else:
                    recent_payment.note = (recent_payment.note or "") + " [Email not found in inbox - already archived or deleted]"
                db.session.commit()
                print(f"✅ DEBUG: Database committed successfully")
                # Return success so page refreshes and button disappears
                return True, "Email already archived (specific payment not found in inbox). Record updated."
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
            # CRITICAL: Must call expunge() to actually delete from inbox
            # Some IMAP servers require this to commit the deletion
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
                # Use custom note if provided, otherwise append default note
                if custom_note:
                    recent_payment.note = custom_note
                else:
                    recent_payment.note = (recent_payment.note or "") + f" [Email manually archived to {manually_processed_folder} folder]"
                db.session.commit()

            mail.logout()
            return True, f"Email successfully moved to {manually_processed_folder} folder"
        else:
            mail.logout()
            return False, f"Failed to move email: {copy_result}"

    except Exception as e:
        return False, f"Error: {str(e)}"


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
            elif "added income" in action_text:
                log_type = "Income Added"
            elif "updated income" in action_text:
                log_type = "Income Updated"
            elif "deleted income" in action_text:
                log_type = "Income Deleted"
            elif "added expense" in action_text:
                log_type = "Expense Added"
            elif "updated expense" in action_text:
                log_type = "Expense Updated"
            elif "deleted expense" in action_text:
                log_type = "Expense Deleted"
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
                log_type = "Payment Matched"
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
            passport = db.session.get(Passport, r.passport_id)

            user_name = passport.user.name if passport and passport.user else "-"
            activity_name = passport.activity.name if passport and passport.activity else "-"

            logs.append({
                "timestamp": r.reminder_sent_at,
                "type": "Reminder Sent",
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
        logo_path = os.path.join("static", "minipass_logo.png")
        if os.path.exists(logo_path):
            inline_images["logo_image"] = open(logo_path, "rb").read()
            context["logo_url"] = url_for("static", filename="minipass_logo.png")

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
    from email.utils import formataddr, formatdate
    from premailer import transform
    import logging
    from utils import get_setting, safe_template
    from datetime import datetime, timezone
    import sys

    def clean_mime_headers(msg):
        """Remove MIME-Version from nested parts to avoid Amavis BAD-HEADER-7 quarantine.

        Python's email.mime library adds MIME-Version: 1.0 to every MIME part,
        but mail servers like Amavis flag multiple MIME-Version headers as suspicious.
        This removes MIME-Version from all nested parts, keeping only the root header.
        """
        if msg.is_multipart():
            for part in msg.get_payload():
                if 'MIME-Version' in part:
                    del part['MIME-Version']
                clean_mime_headers(part)

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

    # ✅ Set default organization info and URLs
    base_url = get_setting('SITE_URL', '').rstrip('/')

    # Set organization name if not already in context
    if 'organization_name' not in context:
        context['organization_name'] = "Fondation LHGI"

    # Set payment email from settings if not in context
    if 'payment_email' not in context:
        payment_email_setting = get_setting("MAIL_USERNAME")
        if payment_email_setting:
            context['payment_email'] = payment_email_setting

    # Use ORG_ADDRESS setting for address
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
    print(f"  payment_email: {context.get('payment_email', 'NOT SET')}")
    print(f"  unsubscribe_url: {context.get('unsubscribe_url', 'MISSING!')}")
    print(f"  privacy_url: {context.get('privacy_url', 'MISSING!')}")
    print(f"  activity provided: {activity is not None}")
    
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
    
    print(f"🌐 Base URL: {base_url}")
    
    # ✅ PHASE 3: Hybrid Hosted Images
    if use_hosted_images:
        # Keep only QR code as CID attachment — all other images (hero, logo, interac)
        # are served via HTTP URLs already present in the template context from Step 3.
        inline_images = {k: v for k, v in inline_images.items() if k == 'qr_code'}
        print(f"🌐 Hosted images mode: {len(inline_images)} CID attachment(s) (QR code only)")
    else:
        print(f"📎 Inline images mode: {len(inline_images)} embedded")
    
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
            'signup_payment_first': 'Registration confirmed - Payment instructions',
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
            elif 'signup_payment_first' in template_name:
                template_type = 'signup_payment_first'
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
    msg["Return-Path"] = from_email

    # ✅ Add deliverability headers
    reply_to_email = from_email
    msg["Reply-To"] = reply_to_email
    msg["List-Unsubscribe"] = f"<{context['unsubscribe_url']}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

    # Set email priority based on template type (transactional vs bulk)
    # Survey invitations are relationship emails, not bulk marketing
    is_transactional = template_name and ('survey' in template_name or 'Pass' in template_name or 'payment' in template_name or 'signup' in template_name)
    if is_transactional:
        msg["Precedence"] = "normal"  # Transactional email
        msg["X-Priority"] = "3"  # Normal priority (1=high, 3=normal, 5=low)
        msg["Importance"] = "normal"
    else:
        msg["Precedence"] = "bulk"  # Bulk/newsletter emails

    msg["X-Mailer"] = "Minipass/1.0"
    msg["Auto-Submitted"] = "auto-generated"

    # Generate unique Message-ID
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000000)  # microsecond precision
    msg["Message-ID"] = f"<{timestamp}@minipass.me>"
    msg["Date"] = formatdate(localtime=True)

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
    
    alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
    alt_part.attach(MIMEText(final_html, "html", "utf-8"))
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

        # Fix: Remove duplicate MIME-Version headers from nested parts
        # Prevents Amavis BAD-HEADER-7 quarantine
        clean_mime_headers(msg)

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


def send_email_async(app, user=None, activity=None, **kwargs):
    import threading

    # Extract activity ID before thread starts (avoid detached instance error)
    activity_id = activity.id if activity and hasattr(activity, 'id') else None

    def send_in_thread():
        with app.app_context():
            try:
                from utils import send_email
                from models import EmailLog, Activity
                import json
                from datetime import datetime, timezone

                # Reload activity in thread context if needed
                if activity_id:
                    activity_in_thread = Activity.query.get(activity_id)
                else:
                    activity_in_thread = None

                # --- Extract arguments ---
                subject = kwargs.get("subject")
                to_email = kwargs.get("to_email")
                template_name = kwargs.get("template_name")
                context = kwargs.get("context", {})
                inline_images = kwargs.get("inline_images", {})
                html_body = kwargs.get("html_body")
                timestamp_override = kwargs.get("timestamp_override")
                organization_id = kwargs.get("organization_id")
                use_hosted_images = kwargs.get("use_hosted_images", False)

                # ✅ FINAL SAFETY: If html_body exists, force clear template_name/context
                if html_body:
                    template_name = None
                    context = {}
                
                # 📧 Apply email template customizations if activity is provided
                # Skip if context already has rendered Jinja2 variables (indicated by _skip_email_context flag)
                skip_context_processing = context.get('_skip_email_context', False) if context else False

                if activity_in_thread and template_name and not html_body and not skip_context_processing:
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
                        'email_templates/signup_payment_first/index.html': 'signup_payment_first',
                        'email_templates/signup_payment_first_compiled/index.html': 'signup_payment_first',
                        'signup_payment_first': 'signup_payment_first',
                        'signup_payment_first_compiled/index.html': 'signup_payment_first',
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
                        context = get_email_context(activity_in_thread, template_type, context)
                        # Update subject if customized
                        if context.get('subject'):
                            subject = context['subject']

                # Clean up internal flag before rendering
                if context and '_skip_email_context' in context:
                    del context['_skip_email_context']

                # Load inline images for compiled templates (skip if Phase 3 hosted images)
                if template_name and not html_body and not use_hosted_images:
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

                    # Load custom hero images for activity (if activity provided)
                    if activity_in_thread:
                        from utils import get_activity_hero_image

                        # Map template names to template types
                        template_type_map = {
                            'newPass': 'newPass',
                            'paymentReceived': 'paymentReceived',
                            'latePayment': 'latePayment',
                            'signup': 'signup',
                            'signup_payment_first': 'signup_payment_first',
                            'redeemPass': 'redeemPass',
                            'survey_invitation': 'survey_invitation'
                        }

                        template_type = template_type_map.get(base_template)
                        if template_type:
                            hero_data, is_custom, is_template_default = get_activity_hero_image(activity_in_thread, template_type)

                            if hero_data and not is_template_default:
                                # Use shared constant for hero CID mappings
                                hero_cid = HERO_CID_MAP.get(template_type)
                                if hero_cid:
                                    inline_images[hero_cid] = hero_data
                                    hero_type = "custom" if is_custom else "activity fallback"
                                    print(f"✅ {hero_type} hero image loaded in send_email_async: template={template_type}, cid={hero_cid}, size={len(hero_data)} bytes")

                # --- Determine organization from context ---
                org_id = None
                if activity_in_thread and hasattr(activity_in_thread, 'organization_id'):
                    org_id = activity_in_thread.organization_id
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
                    activity=activity_in_thread,
                    use_hosted_images=use_hosted_images
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
    from utils import send_email_async, get_email_context, get_setting
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

    # Always send signup email with custom templates

    # Determine email template based on workflow type
    # payment_first: User pays first, then gets passport automatically
    # approval_first: Admin approves first, then user pays
    is_payment_first = getattr(activity, 'workflow_type', 'approval_first') == 'payment_first'
    template_type = 'signup_payment_first' if is_payment_first else 'signup'

    # Build base context for custom templates
    base_context = {
        "user_name": signup.user.name,
        "activity_name": activity.name
    }

    # Add payment-first specific context
    if is_payment_first:
        display_email = get_setting("DISPLAY_PAYMENT_EMAIL")
        payment_email = display_email if display_email else get_setting('MAIL_USERNAME', 'paiement@minipass.me')

        # Only require signup code when there's a naming conflict
        # (another unpaid signup with same name AND same amount)
        needs_signup_code = has_conflicting_unpaid_signup(signup, activity)

        base_context["needs_signup_code"] = needs_signup_code
        base_context["signup_code"] = (signup.signup_code or f"MP-INS-{signup.id:07d}") if needs_signup_code else ""
        base_context["requested_amount"] = f"${signup.requested_amount:.2f}" if signup.requested_amount else "$0.00"
        base_context["payment_email"] = payment_email

    # Get email context using activity-specific templates
    email_context = get_email_context(activity, template_type, base_context)
    
    # Extract template values
    subject = email_context.get('subject', "Confirmation d'inscription")
    title = email_context.get('title', "Votre Inscription est Confirmée")
    intro_raw = email_context.get('intro_text', '')
    conclusion_raw = email_context.get('conclusion_text', '')
    # Use correct compiled template folder based on workflow type
    template_folder = 'signup_payment_first_compiled' if is_payment_first else 'signup_compiled'
    theme = f"{template_folder}/index.html"

    # Render intro and conclusion manually with full context
    render_context = {
        "user_name": signup.user.name,
        "activity_name": activity.name,
        "activity": activity,
        "organization_name": get_setting('ORG_NAME', 'Fondation LHGI')
    }
    # Add payment-first variables if applicable
    if is_payment_first:
        display_email = get_setting("DISPLAY_PAYMENT_EMAIL")
        payment_email = display_email if display_email else get_setting('MAIL_USERNAME', 'paiement@minipass.me')

        # Use the same needs_signup_code value from base_context
        needs_signup_code = base_context.get("needs_signup_code", False)

        render_context["needs_signup_code"] = needs_signup_code
        render_context["signup_code"] = (signup.signup_code or f"MP-INS-{signup.id:07d}") if needs_signup_code else ""
        render_context["requested_amount"] = f"${signup.requested_amount:.2f}" if signup.requested_amount else "$0.00"
        render_context["payment_email"] = payment_email

    intro = render_template_string(intro_raw, **render_context)
    conclusion = render_template_string(conclusion_raw, **render_context)

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
        "logo_url": "/static/minipass_logo.png",
        # CRITICAL: Flag to prevent send_email_async from re-applying get_email_context()
        "_skip_email_context": True
    }
    
    # Add organization variables for footer (from Settings table)
    context['organization_name'] = get_setting('ORG_NAME', 'Fondation LHGI')
    context['organization_address'] = get_setting('ORG_ADDRESS', '821 rue des Sables, Rimouski, QC G5L 6Y7')

    # Phase 3: copy hosted image URLs from email_context (get_email_context already computed them)
    context['hero_image_url'] = email_context.get('hero_image_url', '')
    context['owner_logo_url'] = email_context.get('owner_logo_url')
    context['site_url'] = email_context.get('site_url', '')

    # Add payment-first variables if applicable (for signup_payment_first template)
    if is_payment_first:
        context['payment_email'] = base_context['payment_email']
        context['needs_signup_code'] = base_context['needs_signup_code']
        context['signup_code'] = base_context['signup_code']
        context['requested_amount'] = base_context['requested_amount']

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
        # Phase 3: images are served via hosted URLs — no CID attachments needed
        # inline_images stays empty; send_email_async handles any QR code if needed
        print(f"✅ Phase 3: signup email using hosted images for {template_type}")

        send_email_async(
            app=app,
            user=signup.user,
            activity=activity,
            subject=subject,
            to_email=signup.user.email,
            template_name=theme,
            context=context,
            inline_images=inline_images,
            timestamp_override=timestamp,
            use_hosted_images=True
        )

    else:
        # fallback if compiled missing - use base template (signup or signup_payment_first)
        base_template = 'signup_payment_first' if is_payment_first else 'signup'
        send_email_async(
            app=app,
            user=signup.user,
            activity=activity,
            subject=subject,
            to_email=signup.user.email,
            template_name=f"{base_template}/index.html",
            context=context,
            timestamp_override=timestamp
        )

    # Send push notification to all subscribed admins
    try:
        passport_type_name = f" ({passport_type.name})" if passport_type else ""
        send_push_notification_to_admins(
            title=f"New Signup: {activity.name}",
            body=f"{signup.user.name} signed up{passport_type_name}",
            url=f"/signups?q={signup.user.name}",
            tag=f"signup-{signup.id}"
        )
    except Exception as e:
        print(f"⚠️ Push notification error (signup): {e}")


def notify_pass_event(app, *, event_type, pass_data, activity, admin_email=None, timestamp=None):
    from utils import send_email_async, get_pass_history_data, generate_qr_code_image, get_email_context, get_setting
    from flask import render_template, render_template_string, url_for
    from datetime import datetime, timezone
    import json
    import base64
    import os

    timestamp = timestamp or datetime.now(timezone.utc)
    
    # Map event types to template keys used in activity.email_templates
    event_type_mapping = {
        'pass_created': 'newPass',
        'pass_paid': 'paymentReceived',  # When passport is marked paid
        'payment_received': 'paymentReceived',
        'payment_late': 'latePayment',
        'pass_redeemed': 'redeemPass'
    }
    
    template_type = event_type_mapping.get(event_type, 'newPass')
    
    # Check if activity has custom template for this event type
    has_custom_template = (activity.email_templates and
                          template_type in activity.email_templates and
                          activity.email_templates[template_type])

    # DEBUG: Log the template state
    print(f"🔍 DEBUG notify_pass_event: template_type={template_type}")
    print(f"🔍 DEBUG: activity.email_templates = {activity.email_templates}")
    print(f"🔍 DEBUG: has_custom_template = {has_custom_template}")
    if activity.email_templates and template_type in activity.email_templates:
        print(f"🔍 DEBUG: show_qr_code in templates = {activity.email_templates[template_type].get('show_qr_code', 'NOT SET')}")

    # If no custom template (reset/default state), use regular email path
    if not has_custom_template:
        # Map event type to compiled template paths
        template_mapping = {
            'pass_created': 'newPass_compiled/index.html',
            'pass_paid': 'paymentReceived_compiled/index.html',  # When passport is marked paid
            'payment_received': 'paymentReceived_compiled/index.html',
            'payment_late': 'latePayment_compiled/index.html',
            'pass_redeemed': 'redeemPass_compiled/index.html'
        }
        template_name = template_mapping.get(event_type, 'newPass_compiled/index.html')

        # Get show_qr_code setting (default True for non-customized templates)
        show_qr_code = True

        # Compute owner_logo_url before rendering owner card (Phase 3 — hosted images)
        _BASE_URL = get_setting('SITE_URL', '').rstrip('/')
        _activity_logo_path = os.path.join("static/uploads", f"{activity.id}_owner_logo.png") if activity else None
        if _activity_logo_path and os.path.exists(_activity_logo_path):
            _owner_logo_url = f"{_BASE_URL}/static/uploads/{activity.id}_owner_logo.png"
        else:
            _org_logo_filename = get_setting('LOGO_FILENAME', 'logo.png')
            _org_logo_path = os.path.join("static/uploads", _org_logo_filename)
            _owner_logo_url = f"{_BASE_URL}/static/uploads/{_org_logo_filename}" if os.path.exists(_org_logo_path) else None

        # Build base context with pass data
        base_context = {
            "pass_data": pass_data,
            "owner_html": render_template("email_blocks/owner_card_inline.html", pass_data=pass_data, owner_logo_url=_owner_logo_url),
            "history_html": render_template("email_blocks/history_table_inline.html", history=get_pass_history_data(pass_data.pass_code, fallback_admin_email=admin_email)),
            "activity_name": activity.name if activity else "",
            "show_qr_code": show_qr_code,
            "owner_logo_url": _owner_logo_url,
        }

        # Use get_email_context to load defaults from email_defaults.json and add variables
        context = get_email_context(activity, template_type, base_context)

        # Build inline_images - only include QR code if enabled
        inline_images = {}
        if show_qr_code:
            inline_images["qr_code"] = generate_qr_code_image(pass_data.pass_code).read()

        # Use the standard send_email function with compiled template
        send_email_async(
            app=app,
            user=pass_data.user,
            activity=activity,
            subject=context.get('subject', 'Notification'),
            to_email=pass_data.user.email,
            template_name=template_name,
            context=context,
            timestamp_override=timestamp,
            inline_images=inline_images,
            use_hosted_images=True
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

    # Get show_qr_code setting from activity's email templates (default True)
    show_qr_code = True
    if activity.email_templates and template_type in activity.email_templates:
        show_qr_code = activity.email_templates[template_type].get('show_qr_code', True)

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

    # Only generate QR code if enabled
    qr_data = generate_qr_code_image(pass_data.pass_code).read() if show_qr_code else None
    history = get_pass_history_data(pass_data.pass_code, fallback_admin_email=admin_email)

    # Map event type to template directory - Use compiled template paths
    template_mapping = {
        'pass_created': 'newPass_compiled/index.html',
        'pass_paid': 'paymentReceived_compiled/index.html',  # When passport is marked paid
        'payment_received': 'paymentReceived_compiled/index.html',
        'payment_late': 'latePayment_compiled/index.html',
        'pass_redeemed': 'redeemPass_compiled/index.html'
    }
    theme = template_mapping.get(event_type, 'newPass_compiled/index.html')

    # Compute hosted image URLs (Phase 3 — Hybrid Hosted Images)
    _BASE_URL = get_setting('SITE_URL', '').rstrip('/')
    _hero_image_url = f"{_BASE_URL}/activity/{activity.id}/hero-image/{template_type}" if activity else None
    _activity_logo_path = os.path.join("static/uploads", f"{activity.id}_owner_logo.png") if activity else None
    if _activity_logo_path and os.path.exists(_activity_logo_path):
        _owner_logo_url = f"{_BASE_URL}/static/uploads/{activity.id}_owner_logo.png"
    else:
        _org_logo_filename = get_setting('LOGO_FILENAME', 'logo.png')
        _org_logo_path = os.path.join("static/uploads", _org_logo_filename)
        _owner_logo_url = f"{_BASE_URL}/static/uploads/{_org_logo_filename}" if os.path.exists(_org_logo_path) else None

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
        "owner_html": render_template("email_blocks/owner_card_inline.html", pass_data=pass_data, owner_logo_url=_owner_logo_url),
        "history_html": render_template("email_blocks/history_table_inline.html", history=history),
        "email_info": "",
        "logo_url": "/static/minipass_logo.png",
        "special_message": "",
        "activity_name": activity.name if activity else "",
        "unsubscribe_url": "",  # Will be filled by send_email with subdomain
        "privacy_url": "",      # Will be filled by send_email with subdomain
        "show_qr_code": show_qr_code,  # For conditional QR display in template
        "hero_image_url": _hero_image_url,
        "owner_logo_url": _owner_logo_url,
        # CRITICAL: Flag to prevent send_email_async from re-applying get_email_context()
        "_skip_email_context": True
    }

    # Add organization variables for footer (from Settings table)
    context['organization_name'] = get_setting('ORG_NAME', 'Fondation LHGI')
    context['organization_address'] = get_setting('ORG_ADDRESS', '821 rue des Sables, Rimouski, QC G5L 6Y7')

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

    # Add dynamic content (QR code must be generated per passport, only if enabled)
    if show_qr_code and qr_data:
        inline_images['qr_code'] = qr_data
    
    # Use new hero image selection system
    hero_data, is_custom, is_template_default = get_activity_hero_image(activity, template_type)
    if hero_data and not is_template_default:
        # Replace template images with custom uploads or activity fallbacks
        # Template defaults are already loaded in inline_images from the JSON
        hero_cid = HERO_CID_MAP.get(template_type)
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
            # Try generating a placeholder logo from org name
            try:
                org_name = get_setting('ORG_NAME', 'Minipass')
                placeholder_logo_buf = generate_placeholder_logo_image(org_name)
                logo_data = placeholder_logo_buf.read()
                inline_images['logo'] = logo_data
                print(f"🎨 Using generated placeholder logo for '{org_name}'")
            except Exception:
                # Final fallback to default logo
                logo_data = open("static/minipass_logo.png", "rb").read()
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
        timestamp_override=timestamp,
        use_hosted_images=True
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
# 📧 EMAIL UTILITY FUNCTIONS
# ================================


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
    # Default email template values (hardcoded fallback)
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

    # Load template-specific defaults from email_defaults.json
    from utils_email_defaults import get_default_email_templates
    try:
        all_defaults = get_default_email_templates()
        template_defaults = all_defaults.get(template_type, {})
        # Override hardcoded defaults with values from email_defaults.json
        defaults.update(template_defaults)
    except Exception as e:
        print(f"Warning: Could not load email defaults from file: {e}")
        # Continue with hardcoded defaults

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

    # Add organization_name and payment_email BEFORE Jinja2 rendering
    if 'organization_name' not in context:
        # Get from Settings table (organization table removed)
        context['organization_name'] = get_setting('ORG_NAME', 'Fondation LHGI')
        print(f"✅ Set organization_name from settings: {context['organization_name']}")

    if 'payment_email' not in context:
        print(f"🔍 Checking for payment_email...")
        # Check for display override first (for legacy email forwarding setups)
        display_email = get_setting("DISPLAY_PAYMENT_EMAIL")
        if display_email:
            context['payment_email'] = display_email
            print(f"✅ Set payment_email from DISPLAY_PAYMENT_EMAIL: {display_email}")
        else:
            # Fall back to inbox email (MAIL_USERNAME)
            payment_email_setting = get_setting("MAIL_USERNAME")
            print(f"🔍 get_setting('MAIL_USERNAME') returned: {repr(payment_email_setting)}")
            if payment_email_setting:
                context['payment_email'] = payment_email_setting
                print(f"✅ Set payment_email from MAIL_USERNAME: {payment_email_setting}")
            else:
                print(f"❌ No payment_email found in settings! Value was: {repr(payment_email_setting)}")
    else:
        print(f"ℹ️ payment_email already in context: {context['payment_email']}")

    # Render Jinja2 variables in all text fields
    # (e.g., {{ activity_name }}, {{ question_count }})
    from jinja2 import Template
    for field in ['subject', 'title', 'intro_text', 'conclusion_text']:
        if field in context and context[field]:
            try:
                # Check if the field contains Jinja2 syntax (variables or control structures)
                if ('{{' in context[field] and '}}' in context[field]) or ('{%' in context[field] and '%}' in context[field]):
                    print(f"🔧 JINJA2 RENDERING: Found template syntax in {field}")
                    print(f"🔧 Before: {context[field][:100]}")
                    # Render as Jinja2 template with current context
                    template = Template(context[field])
                    context[field] = template.render(**context)
                    print(f"🔧 After: {context[field][:100]}")
            except Exception as e:
                # If rendering fails, keep original value
                print(f"Warning: Failed to render Jinja2 template in {field}: {e}")

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

    # Phase 3 — Hybrid Hosted Images
    # Add hero_image_url, owner_logo_url, and site_url for URL-based image delivery
    _BASE_URL = get_setting('SITE_URL', '').rstrip('/')
    context['site_url'] = _BASE_URL  # Used in templates for static assets (e.g. interac logo)
    if activity and 'hero_image_url' not in context:
        context['hero_image_url'] = f"{_BASE_URL}/activity/{activity.id}/hero-image/{template_type}"

    if activity and 'owner_logo_url' not in context:
        context['owner_logo_url'] = f"{_BASE_URL}/owner-logo?activity_id={activity.id}"

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

def get_financial_data_from_views(start_date=None, end_date=None, activity_filter=None):
    """
    Get financial data using SQL views for consistency with chatbot.

    Args:
        start_date: Start date (datetime or string YYYY-MM-DD, or None for all time)
        end_date: End date (datetime or string YYYY-MM-DD, or None for all time)
        activity_filter: Optional activity ID to filter by

    Returns:
        dict with summary, by_activity, transactions (same structure as old function)
    """
    from sqlalchemy import text
    from models import Activity, db
    from datetime import datetime

    # Handle None dates - default to all time
    if start_date is None:
        start_date = '2000-01-01'
    if end_date is None:
        end_date = '2099-12-31'

    # Convert dates to strings if needed
    if isinstance(start_date, datetime):
        start_date = start_date.strftime('%Y-%m-%d')
    if isinstance(end_date, datetime):
        end_date = end_date.strftime('%Y-%m-%d')

    # Step 1: Query transaction detail view for individual transactions
    trans_query = """
        SELECT
            month,
            project as account,
            transaction_type,
            transaction_date,
            customer,
            memo,
            amount,
            payment_status,
            entered_by
        FROM monthly_transactions_detail
        WHERE transaction_date >= :start_date AND transaction_date <= :end_date
    """

    params = {'start_date': start_date, 'end_date': end_date}

    if activity_filter:
        # Need to get activity name for filtering since view uses account name
        activity = Activity.query.get(activity_filter)
        if activity:
            trans_query += " AND project = :activity_name"
            params['activity_name'] = activity.name

    # Execute transaction query
    result = db.session.execute(text(trans_query), params)
    transactions = []

    # Step 2: Process and enrich transactions
    for row in result:
        # Handle transaction_date - could be string or datetime object
        transaction_date_str = row.transaction_date
        if isinstance(transaction_date_str, datetime):
            # Already a datetime object
            txn_datetime = transaction_date_str
            transaction_date_str = transaction_date_str.strftime('%Y-%m-%d')
        elif isinstance(transaction_date_str, str):
            # Parse string - handle both date-only and datetime formats
            if ' ' in transaction_date_str:
                # Has time component - take just the date part
                transaction_date_str = transaction_date_str.split(' ')[0]
            txn_datetime = datetime.strptime(transaction_date_str, '%Y-%m-%d')
        else:
            # Fallback
            transaction_date_str = str(transaction_date_str)
            txn_datetime = datetime.now()

        txn = {
            'month': row.month,
            'account': row.account,  # This is activity name from view
            'transaction_type': row.transaction_type,
            'transaction_date': transaction_date_str,
            'date': transaction_date_str,  # For sorting
            'datetime': txn_datetime,
            'customer': row.customer,
            'description': row.memo or '',
            'memo': row.memo or '',
            'amount': float(row.amount),
            'payment_status': row.payment_status,
            'entered_by': row.entered_by or 'System',
            'created_by': row.entered_by or 'System'
        }

        # Get activity info for UI metadata
        activity = Activity.query.filter_by(name=row.account).first()
        if activity:
            txn['activity_id'] = activity.id
            txn['activity_name'] = activity.name
            txn['activity_image'] = activity.image_filename
        else:
            txn['activity_id'] = None
            txn['activity_name'] = row.account
            txn['activity_image'] = None

        # Determine editability and source type
        # Check if this is a system-generated passport sale (check both transaction_type AND entered_by)
        is_passport_system = (
            txn['transaction_type'] == 'Passport Sale' or
            txn['entered_by'] in ['Passport System', 'System'] or
            'Passport' in str(txn['entered_by'])
        )

        if is_passport_system or txn['transaction_type'] == 'Passport Sale':
            txn['editable'] = False
            txn['source_type'] = 'passport'
            txn['type'] = 'Income'
            txn['category'] = 'Passport Sales'
        elif txn['transaction_type'] in ['Other Income', 'Income']:
            txn['editable'] = True
            txn['source_type'] = 'income'
            txn['type'] = 'Income'
            txn['category'] = row.customer or 'Other Income'  # customer field has category for income
        elif txn['transaction_type'] == 'Expense':
            txn['editable'] = True
            txn['source_type'] = 'expense'
            txn['type'] = 'Expense'
            txn['category'] = row.customer or 'Expense'  # customer field has category for expenses
        else:
            # Default for unknown transaction types
            txn['editable'] = True
            txn['source_type'] = 'other'
            txn['type'] = 'Income'  # Default to Income
            txn['category'] = txn['transaction_type']

        # Get ID and receipt from original tables for editable transactions
        txn['id'] = None
        txn['receipt_filename'] = None
        txn['payment_method'] = None

        if txn['editable'] and txn['activity_id']:
            from models import Income, Expense
            from sqlalchemy import func, and_

            # Convert date string to date object for comparison
            try:
                if isinstance(transaction_date_str, str):
                    # Handle both 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS.mmmmmm' formats
                    date_str = transaction_date_str.split()[0]  # Take just the date part
                    compare_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    compare_date = transaction_date_str

                if txn['source_type'] == 'income':
                    # Query Income table - use SQL date casting for robust comparison
                    income_record = Income.query.filter(
                        and_(
                            Income.activity_id == txn['activity_id'],
                            func.date(Income.date) == compare_date,
                            func.abs(Income.amount - txn['amount']) < 0.01  # Floating point tolerance
                        )
                    ).first()

                    if income_record:
                        txn['id'] = income_record.id
                        txn['receipt_filename'] = income_record.receipt_filename
                        txn['category'] = income_record.category
                        txn['payment_method'] = income_record.payment_method

                elif txn['source_type'] == 'expense':
                    # Query Expense table
                    expense_record = Expense.query.filter(
                        and_(
                            Expense.activity_id == txn['activity_id'],
                            func.date(Expense.date) == compare_date,
                            func.abs(Expense.amount - txn['amount']) < 0.01  # Floating point tolerance
                        )
                    ).first()

                    if expense_record:
                        txn['id'] = expense_record.id
                        txn['receipt_filename'] = expense_record.receipt_filename
                        txn['category'] = expense_record.category
                        txn['payment_method'] = expense_record.payment_method
            except Exception as e:
                # If date parsing fails, skip ID lookup
                pass

        transactions.append(txn)

    # Step 3: Calculate summary KPIs from financial summary view
    # Calculate month range for summary query
    start_month = start_date[:7]  # YYYY-MM
    end_month = end_date[:7]  # YYYY-MM

    summary_query = """
        SELECT
            COALESCE(SUM(cash_received), 0) as cash_received,
            COALESCE(SUM(cash_paid), 0) as cash_paid,
            COALESCE(SUM(net_cash_flow), 0) as net_cash_flow,
            COALESCE(SUM(accounts_receivable), 0) as accounts_receivable,
            COALESCE(SUM(accounts_payable), 0) as accounts_payable,
            COALESCE(SUM(total_revenue), 0) as total_revenue,
            COALESCE(SUM(total_expenses), 0) as total_expenses
        FROM monthly_financial_summary
        WHERE month >= :start_month AND month <= :end_month
    """

    sum_params = {'start_month': start_month, 'end_month': end_month}

    if activity_filter and activity:
        summary_query += " AND account = :activity_name"
        sum_params['activity_name'] = activity.name

    summary_result = db.session.execute(text(summary_query), sum_params)
    summary_row = summary_result.fetchone()

    summary = {
        'cash_received': float(summary_row.cash_received),
        'cash_paid': float(summary_row.cash_paid),
        'net_cash_flow': float(summary_row.net_cash_flow),
        'accounts_receivable': float(summary_row.accounts_receivable),
        'accounts_payable': float(summary_row.accounts_payable),
        'total_revenue': float(summary_row.total_revenue),
        'total_expenses': float(summary_row.total_expenses)
    }

    # Step 4: Group transactions by activity
    by_activity = []
    activities_dict = {}

    for txn in transactions:
        activity_id = txn.get('activity_id')
        if not activity_id:
            continue  # Skip if no activity found

        if activity_id not in activities_dict:
            activities_dict[activity_id] = {
                'activity_id': activity_id,
                'activity_name': txn['activity_name'],
                'activity_image': txn['activity_image'],
                'total_revenue': 0,
                'total_expenses': 0,
                'transactions': []
            }

        # Add transaction to activity
        activities_dict[activity_id]['transactions'].append(txn)

        # Calculate activity totals (only paid transactions)
        if txn['payment_status'] in ['Paid', 'received']:
            if txn['type'] == 'Income':
                activities_dict[activity_id]['total_revenue'] += txn['amount']
            elif txn['type'] == 'Expense':
                activities_dict[activity_id]['total_expenses'] += txn['amount']

    # Calculate net income per activity and convert to list
    for activity in activities_dict.values():
        activity['net_income'] = activity['total_revenue'] - activity['total_expenses']
        by_activity.append(activity)

    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: x['datetime'], reverse=True)

    # Return in expected format
    return {
        'summary': summary,
        'by_activity': by_activity,
        'transactions': transactions
    }


def get_activity_revenue_from_view():
    """
    Get total cash_received per activity from SQL view.

    Returns dict mapping activity_id to total revenue (passport_sales + other_income).
    This ensures consistency with the Financial Report page.
    """
    from sqlalchemy import text

    query = """
        SELECT activity_id, SUM(cash_received) as total_revenue
        FROM monthly_financial_summary
        GROUP BY activity_id
    """

    try:
        result = db.session.execute(text(query))
        return {row.activity_id: float(row.total_revenue or 0) for row in result}
    except Exception as e:
        return {}  # Fallback if view doesn't exist


def get_financial_data(start_date=None, end_date=None, activity_id=None, basis='cash'):
    """
    Get financial data for reporting with Cash Flow Accounting support.

    Args:
        start_date: datetime object for start of period (UTC, optional)
        end_date: datetime object for end of period (UTC, optional)
        activity_id: Optional activity ID to filter by specific activity
        basis: 'cash' (default) or 'accrual' - accounting basis

    Returns:
        dict with cash_received, cash_paid, net_cash_flow,
        accounts_receivable, accounts_payable, transactions
    """
    from models import Passport, Income, Expense, Activity, PassportType, User
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

    # Initialize totals
    cash_received = 0.0
    cash_paid = 0.0
    accounts_receivable = 0.0
    accounts_payable = 0.0
    all_transactions = []

    # PASSPORT SALES (Income)
    passport_query = db.session.query(Passport).join(Activity).join(PassportType)

    if basis == 'cash':
        # Cash Basis: Only paid passports, use payment_date for filtering
        passport_query = passport_query.filter(
            Passport.paid == True,
            Passport.paid_date >= start_date,
            Passport.paid_date <= end_date
        )
    else:
        # Accrual Basis: All passports, use created_dt for filtering
        passport_query = passport_query.filter(
            Passport.created_dt >= start_date,
            Passport.created_dt <= end_date
        )

    if activity_id:
        passport_query = passport_query.filter(Passport.activity_id == activity_id)

    passports = passport_query.all()

    for passport in passports:
        user = db.session.get(User, passport.user_id) if passport.user_id else None
        if passport.paid:
            cash_received += passport.sold_amt
        else:
            accounts_receivable += passport.sold_amt

        all_transactions.append({
            'id': None,
            'date': passport.paid_date.strftime('%Y-%m-%d') if passport.paid_date else passport.created_dt.strftime('%Y-%m-%d'),
            'datetime': passport.paid_date if passport.paid_date else passport.created_dt,
            'type': 'Income',
            'category': 'Passport Sales',
            'description': f"{passport.passport_type.name if passport.passport_type else 'Passport'} - {user.name if user else 'Unknown'}",
            'amount': passport.sold_amt,
            'payment_status': 'received' if passport.paid else 'pending',
            'payment_date': passport.paid_date.strftime('%Y-%m-%d') if passport.paid_date else '',
            'payment_method': '',  # Passport sales don't track payment method
            'due_date': '',  # Passport sales don't have due dates
            'receipt_filename': None,
            'activity_id': passport.activity_id,
            'activity_name': passport.activity.name,
            'activity_image': passport.activity.image_filename or passport.activity.logo_filename,
            'editable': False,  # Passport sales not editable from financial report
            'source_type': 'passport',
            'created_by': passport.marked_paid_by or 'System'
        })

    # MANUAL INCOME ENTRIES
    # Query ALL income transactions (regardless of payment status)
    # KPIs will be calculated based on payment_status below
    income_query = db.session.query(Income).join(Activity)

    # Filter by invoice date to get all transactions in the period
    income_query = income_query.filter(
        Income.date >= start_date,
        Income.date <= end_date
    )

    if activity_id:
        income_query = income_query.filter(Income.activity_id == activity_id)

    incomes = income_query.all()

    # Calculate KPIs based on payment status (cash basis accounting)
    for income in incomes:
        if income.payment_status == 'received':
            cash_received += income.amount
        elif income.payment_status == 'pending':
            accounts_receivable += income.amount

        all_transactions.append({
            'id': income.id,
            'date': income.payment_date.strftime('%Y-%m-%d') if income.payment_date else income.date.strftime('%Y-%m-%d'),
            'datetime': income.payment_date if income.payment_date else income.date,
            'type': 'Income',
            'category': income.category,
            'description': income.note or '',
            'amount': income.amount,
            'payment_status': income.payment_status,
            'payment_date': income.payment_date.strftime('%Y-%m-%d') if income.payment_date else '',
            'payment_method': income.payment_method or '',
            'due_date': '',  # Income doesn't have due_date
            'receipt_filename': income.receipt_filename,
            'activity_id': income.activity_id,
            'activity_name': income.activity.name,
            'activity_image': income.activity.image_filename or income.activity.logo_filename,
            'editable': True,
            'source_type': 'income',
            'created_by': income.created_by or 'Unknown'
        })

    # EXPENSES
    # Query expense transactions with proper date filtering:
    # - Paid expenses: filter by bill date (date field)
    # - Unpaid expenses: filter by effective date (payment_date > due_date > date)
    # This ensures unpaid expenses with future payment dates appear in the correct fiscal year
    from sqlalchemy import func, or_, and_

    # Build effective date expression for unpaid expenses
    effective_date = func.coalesce(Expense.payment_date, Expense.due_date, Expense.date)

    expense_query = db.session.query(Expense).join(Activity)

    # Filter: paid expenses by bill date OR unpaid expenses by effective date
    expense_query = expense_query.filter(
        or_(
            # Paid expenses: use bill date (current behavior)
            and_(
                Expense.payment_status == 'paid',
                Expense.date >= start_date,
                Expense.date <= end_date
            ),
            # Unpaid expenses: use effective date (payment_date > due_date > date)
            and_(
                Expense.payment_status == 'unpaid',
                effective_date >= start_date,
                effective_date <= end_date
            ),
            # Cancelled expenses: use bill date
            and_(
                Expense.payment_status == 'cancelled',
                Expense.date >= start_date,
                Expense.date <= end_date
            )
        )
    )

    if activity_id:
        expense_query = expense_query.filter(Expense.activity_id == activity_id)

    expenses = expense_query.all()

    # Calculate KPIs based on payment status (cash basis accounting)
    for expense in expenses:
        if expense.payment_status == 'paid':
            cash_paid += expense.amount
        elif expense.payment_status == 'unpaid':
            accounts_payable += expense.amount

        all_transactions.append({
            'id': expense.id,
            'date': expense.payment_date.strftime('%Y-%m-%d') if expense.payment_date else expense.date.strftime('%Y-%m-%d'),
            'datetime': expense.payment_date if expense.payment_date else expense.date,
            'type': 'Expense',
            'category': expense.category,
            'description': expense.description or '',
            'amount': expense.amount,
            'payment_status': expense.payment_status,
            'payment_date': expense.payment_date.strftime('%Y-%m-%d') if expense.payment_date else '',
            'payment_method': expense.payment_method or '',
            'due_date': expense.due_date.strftime('%Y-%m-%d') if expense.due_date else '',
            'receipt_filename': expense.receipt_filename,
            'activity_id': expense.activity_id,
            'activity_name': expense.activity.name,
            'activity_image': expense.activity.image_filename or expense.activity.logo_filename,
            'editable': True,
            'source_type': 'expense',
            'created_by': expense.created_by or 'Unknown'
        })

    # Sort transactions by date (newest first)
    all_transactions.sort(key=lambda x: x['datetime'], reverse=True)

    # Group by activity
    by_activity = []
    if activity_id:
        # Single activity view
        activity = db.session.get(Activity, activity_id)
        if activity:
            activity_transactions = [t for t in all_transactions if t['activity_id'] == activity.id]
            by_activity.append({
                'activity_id': activity.id,
                'activity_name': activity.name,
                'activity_image': activity.image_filename or activity.logo_filename,
                'total_revenue': sum(t['amount'] for t in activity_transactions if t['type'] == 'Income' and t['payment_status'] in ['received', 'paid']),
                'total_expenses': sum(t['amount'] for t in activity_transactions if t['type'] == 'Expense' and t['payment_status'] == 'paid'),
                'net_income': sum(t['amount'] for t in activity_transactions if t['type'] == 'Income' and t['payment_status'] in ['received', 'paid']) -
                              sum(t['amount'] for t in activity_transactions if t['type'] == 'Expense' and t['payment_status'] == 'paid'),
                'transactions': activity_transactions
            })
    else:
        # All activities
        activities = db.session.query(Activity).all()
        for activity in activities:
            activity_transactions = [t for t in all_transactions if t['activity_id'] == activity.id]
            if activity_transactions:
                by_activity.append({
                    'activity_id': activity.id,
                    'activity_name': activity.name,
                    'activity_image': activity.image_filename or activity.logo_filename,
                    'total_revenue': sum(t['amount'] for t in activity_transactions if t['type'] == 'Income' and t['payment_status'] in ['received', 'paid']),
                    'total_expenses': sum(t['amount'] for t in activity_transactions if t['type'] == 'Expense' and t['payment_status'] == 'paid'),
                    'net_income': sum(t['amount'] for t in activity_transactions if t['type'] == 'Income' and t['payment_status'] in ['received', 'paid']) -
                                  sum(t['amount'] for t in activity_transactions if t['type'] == 'Expense' and t['payment_status'] == 'paid'),
                    'transactions': activity_transactions
                })

    # Determine period label
    if start_date.year == 2000 and end_date >= datetime.now(timezone.utc):
        period_label = 'All Time'
    else:
        period_label = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"

    return {
        'summary': {
            'cash_received': cash_received,
            'cash_paid': cash_paid,
            'net_cash_flow': cash_received - cash_paid,
            'accounts_receivable': accounts_receivable,
            'accounts_payable': accounts_payable,
            'total_revenue': cash_received + accounts_receivable,  # Accrual total
            'total_expenses': cash_paid + accounts_payable,  # Accrual total
            'net_income': (cash_received + accounts_receivable) - (cash_paid + accounts_payable),
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

    # Write header with cash flow accounting fields
    writer.writerow([
        'Date',
        'Activity',
        'Type',
        'Category',
        'Description',
        'Amount',
        'Payment Status',
        'Payment Date',
        'Payment Method',
        'Due Date',
        'Receipt',
        'Created By'
    ])

    # Write all transactions (support both old 'all_transactions' and new 'transactions' keys)
    transactions = financial_data.get('all_transactions') or financial_data.get('transactions', [])

    for transaction in transactions:
        writer.writerow([
            transaction.get('date', transaction.get('transaction_date', 'N/A')),
            transaction.get('activity_name', 'N/A'),
            transaction.get('type', transaction.get('transaction_type', 'N/A')),
            transaction.get('category', 'N/A'),
            transaction.get('description', transaction.get('memo', 'N/A')),
            f"{transaction.get('amount', 0):.2f}",
            transaction.get('payment_status', 'N/A').title(),
            transaction.get('payment_date', 'N/A'),
            transaction.get('payment_method', 'N/A'),
            transaction.get('due_date', 'N/A'),
            transaction.get('receipt_filename', 'N/A'),
            transaction.get('created_by', transaction.get('entered_by', 'N/A'))
        ])

    return output.getvalue()


# ================================
# 👥 USER CONTACT REPORT FUNCTIONS
# ================================

def get_user_contact_report(search_query="", status_filter="", show_all=False):
    """
    Generate user contact list with engagement metrics.

    Args:
        search_query: Search term to filter users by name or email
        status_filter: 'active' to show only users with passports, '' for default
        show_all: Boolean to show all users

    Returns:
        dict: User contact data with summary and user list
    """
    from models import User, Passport, Activity
    from sqlalchemy import func, desc, or_
    from datetime import datetime, timezone

    # Build query aggregated by name + email (to avoid duplicates from multiple User records)
    query = db.session.query(
        User.name,
        User.email,
        func.max(User.phone_number).label('phone_number'),
        func.max(User.email_opt_out).label('email_opt_out'),
        func.count(Passport.id).label('passport_count'),
        func.coalesce(func.sum(Passport.sold_amt), 0).label('total_revenue'),
        func.max(Passport.created_dt).label('last_activity_date')
    ).outerjoin(Passport, User.id == Passport.user_id)

    # Group by name and email (aggregate duplicates)
    query = query.group_by(User.name, User.email)

    # Execute query to get all users
    all_user_data = query.all()

    # Apply filters in Python for flexibility
    users = []
    total_users = 0
    active_users = 0
    total_revenue = 0

    for user in all_user_data:
        # Apply status filter
        if status_filter == "active" and not show_all:
            # Only show users with passports
            if user.passport_count == 0:
                continue

        # Apply search filter
        if search_query:
            search_lower = search_query.lower()
            name_match = search_lower in (user.name or '').lower()
            email_match = search_lower in (user.email or '').lower()
            if not (name_match or email_match):
                continue

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
        ).distinct()

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

    # Sort by passport count descending
    users.sort(key=lambda x: x['passport_count'], reverse=True)

    return {
        'users': users,
        'summary': {
            'total_users': total_users,
            'active_users': active_users,
            'total_revenue': total_revenue,
            'avg_passports': round(sum(u['passport_count'] for u in users) / total_users, 1) if total_users > 0 else 0
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
    from datetime import datetime, timezone

    output = StringIO()
    writer = csv.writer(output)

    # Write metadata header
    writer.writerow([f"# User Contact List - Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"])
    writer.writerow([f"# Total Users: {user_data['summary']['total_users']}"])
    writer.writerow([f"# Active Users: {user_data['summary']['active_users']}"])
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


def export_user_contacts_raw_csv(search_query="", status_filter="", show_all=False):
    """
    Export RAW passport data to CSV format - one row per passport, no aggregation.

    Args:
        search_query: Optional search filter for user name/email
        status_filter: "active" to show only users with passports
        show_all: If True, ignore status_filter

    Returns:
        str: CSV formatted string with raw passport data
    """
    import csv
    from io import StringIO
    from datetime import datetime, timezone
    from models import User, Passport, Activity, PassportType

    output = StringIO()
    # Add UTF-8 BOM for Excel compatibility
    output.write('\ufeff')
    writer = csv.writer(output)

    # Query raw passport data with joins
    query = db.session.query(
        User.name.label('user_name'),
        User.email.label('user_email'),
        User.phone_number.label('user_phone'),
        User.email_opt_out,
        Activity.name.label('activity_name'),
        Passport.passport_type_name,
        Passport.sold_amt,
        Passport.created_dt,
        Passport.paid,
        Passport.paid_date,
        Passport.uses_remaining,
        Passport.pass_code,
        Passport.notes
    ).join(
        User, Passport.user_id == User.id
    ).join(
        Activity, Passport.activity_id == Activity.id
    )

    # Apply search filter
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )

    # Order by created date descending
    query = query.order_by(Passport.created_dt.desc())

    results = query.all()

    # Write column headers (no comment rows - they confuse spreadsheet software)
    writer.writerow([
        'User Name',
        'User Email',
        'User Phone',
        'Activity',
        'Passport Type',
        'Amount',
        'Created Date',
        'Paid',
        'Paid Date',
        'Uses Remaining',
        'Pass Code',
        'Notes',
        'Email Opt-Out'
    ])

    # Write data rows - one per passport
    for row in results:
        writer.writerow([
            row.user_name or '',
            row.user_email or '',
            row.user_phone or '',
            row.activity_name or '',
            row.passport_type_name or '',
            f"{row.sold_amt:.2f}" if row.sold_amt else '0.00',
            row.created_dt.strftime('%Y-%m-%d %H:%M') if row.created_dt else '',
            'Yes' if row.paid else 'No',
            row.paid_date.strftime('%Y-%m-%d') if row.paid_date else '',
            row.uses_remaining if row.uses_remaining is not None else '',
            row.pass_code or '',
            row.notes or '',
            'Yes' if row.email_opt_out else 'No'
        ])

    return output.getvalue()


# ================================
# 📱 PUSH NOTIFICATIONS
# ================================

def get_or_create_vapid_keys():
    """
    Get existing VAPID keys or generate new ones if not present.
    VAPID keys are stored in the Setting table for persistence.

    Returns:
        dict: {'private_key': str, 'public_key': str}
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    # Check if keys already exist
    private_key_setting = Setting.query.filter_by(key="VAPID_PRIVATE_KEY").first()
    public_key_setting = Setting.query.filter_by(key="VAPID_PUBLIC_KEY").first()

    if private_key_setting and public_key_setting:
        return {
            'private_key': private_key_setting.value,
            'public_key': public_key_setting.value
        }

    # Generate new ECDSA key pair using P-256 curve (required for VAPID)
    private_key_obj = ec.generate_private_key(ec.SECP256R1())

    # Get private key as raw bytes (32 bytes for P-256), then base64 encode for pywebpush
    private_key_bytes = private_key_obj.private_numbers().private_value.to_bytes(32, 'big')
    private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')

    # Get public key in URL-safe base64 format (for browser push subscription)
    public_key_bytes = private_key_obj.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')

    # Save to database
    if not private_key_setting:
        db.session.add(Setting(key="VAPID_PRIVATE_KEY", value=private_key_b64))
    else:
        private_key_setting.value = private_key_b64

    if not public_key_setting:
        db.session.add(Setting(key="VAPID_PUBLIC_KEY", value=public_key_b64))
    else:
        public_key_setting.value = public_key_b64

    db.session.commit()

    print(f"✅ Generated new VAPID keys for push notifications")

    return {
        'private_key': private_key_b64,
        'public_key': public_key_b64
    }


def send_push_notification_to_admins(title, body, url=None, tag=None):
    """
    Send push notification to all admins with active subscriptions.

    Args:
        title: Notification title
        body: Notification body text
        url: URL to open when notification is clicked
        tag: Optional tag to replace previous notifications with same tag

    Returns:
        int: Number of notifications successfully sent
    """
    from pywebpush import webpush, WebPushException
    from models import PushSubscription
    from datetime import datetime, timezone
    import json

    try:
        vapid_keys = get_or_create_vapid_keys()
    except Exception as e:
        print(f"❌ Failed to get VAPID keys: {e}")
        return 0

    # Get VAPID claims email from settings, or use default
    claims_email_setting = Setting.query.filter_by(key="VAPID_CLAIMS_EMAIL").first()
    vapid_claims_email = claims_email_setting.value if claims_email_setting else "mailto:admin@minipass.me"

    subscriptions = PushSubscription.query.all()

    if not subscriptions:
        return 0

    payload = json.dumps({
        'title': title,
        'body': body,
        'url': url or '/',
        'tag': tag,
        'icon': '/static/icons/icon-192x192.png',
        'badge': '/static/favicon.png'
    })

    failed_subscriptions = []
    success_count = 0

    for sub in subscriptions:
        subscription_info = {
            'endpoint': sub.endpoint,
            'keys': {
                'p256dh': sub.p256dh_key,
                'auth': sub.auth_key
            }
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=vapid_keys['private_key'],
                vapid_claims={'sub': vapid_claims_email}
            )
            # Update last_used timestamp
            sub.last_used_dt = datetime.now(timezone.utc)
            success_count += 1
        except WebPushException as e:
            print(f"⚠️ Push notification failed for subscription {sub.id}: {e}")
            # If subscription is expired or invalid (404, 410), mark for removal
            if e.response and e.response.status_code in [404, 410]:
                failed_subscriptions.append(sub.id)
        except Exception as e:
            print(f"⚠️ Unexpected push error for subscription {sub.id}: {e}")

    # Clean up invalid subscriptions
    if failed_subscriptions:
        PushSubscription.query.filter(
            PushSubscription.id.in_(failed_subscriptions)
        ).delete(synchronize_session=False)
        print(f"🗑️ Removed {len(failed_subscriptions)} expired push subscription(s)")

    db.session.commit()

    if success_count > 0:
        print(f"📱 Sent push notification to {success_count} device(s): {title}")

    return success_count


def send_push_notification_to_admin(admin_id, title, body, url=None, tag=None):
    """
    Send push notification to a specific admin's subscribed devices.

    Args:
        admin_id: ID of the admin to send notification to
        title: Notification title
        body: Notification body text
        url: URL to open when notification is clicked
        tag: Optional tag to replace previous notifications with same tag

    Returns:
        int: Number of notifications successfully sent
    """
    from pywebpush import webpush, WebPushException
    from models import PushSubscription
    from datetime import datetime, timezone
    import json

    try:
        vapid_keys = get_or_create_vapid_keys()
    except Exception as e:
        print(f"❌ Failed to get VAPID keys: {e}")
        raise Exception(f"Failed to get VAPID keys: {e}")

    # Get VAPID claims email from settings, or use default
    claims_email_setting = Setting.query.filter_by(key="VAPID_CLAIMS_EMAIL").first()
    vapid_claims_email = claims_email_setting.value if claims_email_setting else "mailto:admin@minipass.me"

    subscriptions = PushSubscription.query.filter_by(admin_id=admin_id).all()

    if not subscriptions:
        raise Exception("No push subscriptions found for this admin")

    payload = json.dumps({
        'title': title,
        'body': body,
        'url': url or '/',
        'tag': tag,
        'icon': '/static/icons/icon-192x192.png',
        'badge': '/static/favicon.png'
    })

    failed_subscriptions = []
    success_count = 0
    errors = []

    for sub in subscriptions:
        subscription_info = {
            'endpoint': sub.endpoint,
            'keys': {
                'p256dh': sub.p256dh_key,
                'auth': sub.auth_key
            }
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=vapid_keys['private_key'],
                vapid_claims={'sub': vapid_claims_email}
            )
            # Update last_used timestamp
            sub.last_used_dt = datetime.now(timezone.utc)
            success_count += 1
            print(f"✅ Push sent to subscription {sub.id}")
        except WebPushException as e:
            error_msg = str(e)
            print(f"⚠️ Push notification failed for subscription {sub.id}: {error_msg}")
            errors.append(error_msg)
            # If subscription is expired or invalid (404, 410), mark for removal
            if e.response and e.response.status_code in [404, 410]:
                failed_subscriptions.append(sub.id)
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ Unexpected push error for subscription {sub.id}: {error_msg}")
            errors.append(error_msg)

    # Clean up invalid subscriptions
    if failed_subscriptions:
        PushSubscription.query.filter(
            PushSubscription.id.in_(failed_subscriptions)
        ).delete(synchronize_session=False)
        print(f"🗑️ Removed {len(failed_subscriptions)} expired push subscription(s)")

    db.session.commit()

    if success_count == 0 and errors:
        raise Exception(f"All push notifications failed: {'; '.join(errors)}")

    return success_count


