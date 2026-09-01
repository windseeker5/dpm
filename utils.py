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

from models import Setting, db, Passport, Redemption, Admin, EbankPayment, ReminderLog, Activity




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


# Where the shipped default hero images live, one PNG per template type.
HERO_DIR = os.path.join('static', 'images', 'email', 'heroes')


@lru_cache(maxsize=20)
def get_template_default_hero(template_type):
    """
    Load the shipped default hero image for a template type.

    These used to live base64-encoded inside templates/email_templates/<type>_original/
    inline_images.json — two copies of every hero (_compiled and _original), 2.3 MB of JSON,
    maintained by a compiler whose real job was embedding images that are now served as
    hosted URLs. They are ordinary PNGs in static/ now; the bytes are unchanged.

    Note: Cached with @lru_cache (avoids repeated file reads).
    Use clear_hero_image_cache() after replacing a hero image.

    Args:
        template_type: Type of template (newPass, paymentReceived, etc.)

    Returns:
        bytes: Hero image data, or None if not found
    """
    path = os.path.join(HERO_DIR, f"{template_type}.png")

    if not os.path.exists(path):
        print(f"\u274c Default hero not found: {path}")
        return None

    try:
        with open(path, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"\u274c Error loading template hero: {e}")
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
    Hero image selection, priority order:
    1. Custom uploaded hero for this exact email type (highest priority — an explicit choice)
    2. The activity's own real photo (the whole point of the Aug 2026 photo-band redesign —
       see docs/EMAIL.md)
    3. The shipped generic mascot default — last resort, only when the activity has no photo
       at all
    4. A generated placeholder cover from the activity's name

    Before Aug 2026 this order had the generic mascot (3) ahead of the real photo (2), gated
    behind an unrelated "does this template have text customizations" check — meaning a real
    uploaded activity photo was *never* used unless someone separately uploaded a duplicate
    "custom hero" for that exact template type, since the mascot file always exists and so
    always won first. Every activity's emails showed the cartoon mascot regardless of whether
    the activity had a real photo, which is the opposite of what the redesign shipped to
    replace it with. Reordered so the real photo is the default, not a rarely-reached fallback.

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

    # Priority 2: The activity's own real photo
    if activity and activity.image_filename:
        activity_image_paths = [
            f"static/uploads/{activity.image_filename}",
            f"static/uploads/activity_images/{activity.image_filename}"
        ]
        for activity_image_path in activity_image_paths:
            if os.path.exists(activity_image_path):
                with open(activity_image_path, "rb") as f:
                    print(f"✅ Using activity's real photo as hero for {template_type}: {activity.image_filename}")
                    return f.read(), False, False  # is_template_default=False — this is a photo

    # Priority 3: The shipped generic mascot default — only when the activity has no photo
    template_hero_data = get_template_default_hero(template_type)
    if template_hero_data:
        print(f"📦 Activity has no photo — using generic template default hero for {template_type}")
        return template_hero_data, False, True  # is_template_default=True

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
        html_fields = ['admin_message']
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
    1. Environment variable (from docker-compose) — EXCEPT for DB-only keys
    2. Database setting table (cached in flask.g for the lifetime of the request)
    3. Default value
    """
    import os
    from flask import g

    # Keys that must ONLY come from the database, never from environment variables.
    # These are per-customer values that differ between deployed instances.
    # Allowing env vars to override them causes silent mismatches (e.g. wrong
    # Stripe account credentials) that break subscription management.
    _DB_ONLY_KEYS = {
        'STRIPE_SUBSCRIPTION_ID', 'STRIPE_CUSTOMER_ID',
        'STRIPE_PAYMENTS_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET',
        'STRIPE_PAYMENTS_ENABLED',
        'BILLING_FREQUENCY', 'MINIPASS_TIER', 'PAYMENT_AMOUNT',
        'SUBSCRIPTION_RENEWAL_DATE',
        'PENDING_DOWNGRADE_PLAN', 'PENDING_DOWNGRADE_FREQ',
        'PENDING_DOWNGRADE_DATE', 'PENDING_DOWNGRADE_SCHEDULE_ID',
    }
    _DB_ONLY_PREFIXES = ('STRIPE_PRICE_',)

    # First check environment variables (from docker-compose) — skip for DB-only keys
    is_db_only = key in _DB_ONLY_KEYS or any(key.startswith(p) for p in _DB_ONLY_PREFIXES)
    if not is_db_only:
        env_value = os.environ.get(key)
        if env_value is not None and env_value != "":
            return env_value

    with current_app.app_context():
        # Cache all settings in flask.g so Setting.query.all() runs at most once per request
        if not hasattr(g, '_settings_cache'):
            try:
                g._settings_cache = {s.key: s.value for s in Setting.query.all()}
            except Exception as e:
                logging.error(f"❌ get_setting() DB pool exhausted — settings cache empty: {e}")
                g._settings_cache = {}

        cached = g._settings_cache.get(key)
        if cached not in [None, ""]:
            return cached

        # Fall back to SettingsManager for any key not in the simple setting table
        try:
            from models.settings import SettingsManager
            return SettingsManager.get(key, default)
        except ImportError:
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

    # Session scheduling: per-slot capacity is the sole admission control, so this
    # activity-level number is meaningless here — and worse, it would invert. This function
    # subtracts SUM(uses_remaining), and scheduled activities decrement uses_remaining at
    # BOOKING time, so every booking would make the activity look like it had one MORE spot
    # free, silently reopening a sold-out activity. Return None and let the slots govern.
    if activity.uses_scheduling:
        return None

    # Sum all uses_remaining from active passports for this activity
    # This counts total sessions sold/reserved
    total_sold = db.session.query(func.coalesce(func.sum(Passport.uses_remaining), 0))\
        .filter(Passport.activity_id == activity_id)\
        .scalar()

    remaining = activity.max_sessions - total_sold
    return max(0, remaining)


# ============================================================================
# 📅 SESSION SCHEDULING (slots + bookings)
# ============================================================================
# Called "Sessions" in the UI, "slots" in code — see the naming note in models.py.
#
# ⚠️ TIMEZONE CONTRACT (the easiest thing to get wrong here):
#   ActivitySlot.starts_at / ends_at  -> NAIVE LOCAL wall-clock (matches Activity.start_date
#                                        and the <input type="datetime-local"> fields)
#   everything else (*_dt, held_until) -> UTC
# SQLite has no timezone type, so aware datetimes are persisted with tzinfo dropped and read
# back naive. Always compare UTC columns against _utc_naive_now(), never datetime.now().

SLOT_HOLD_HOURS_DEFAULT = 72        # Interac + admin approval can genuinely take days
SLOT_HOLD_HOURS_STRIPE = 2          # Checkout abandonment is near-instant

_FR_MONTHS = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}
_FR_DAYS = {
    0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi", 4: "vendredi", 5: "samedi", 6: "dimanche",
}


def _utc_naive_now():
    """Current UTC time as a naive datetime, matching how SQLite stores our UTC columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_slot_label(slot, include_weekday=True):
    """Human label for a slot, e.g. 'samedi 14 juillet à 11 h 00'.

    Built by hand because there are no locale helpers in this app and babel/locale is not
    configured — relying on system locale would produce English on some hosts.
    """
    if slot is None or slot.starts_at is None:
        return ""
    if slot.label:
        return slot.label
    dt = slot.starts_at
    parts = []
    if include_weekday:
        parts.append(_FR_DAYS.get(dt.weekday(), ""))
    parts.append(f"{dt.day} {_FR_MONTHS.get(dt.month, '')}")
    label = " ".join(p for p in parts if p).strip()
    return f"{label} à {dt.hour} h {dt.minute:02d}"


def get_slot_hold_hours():
    """How long an unpaid signup holds its seat (Interac path). Tunable without a deploy."""
    try:
        setting = Setting.query.filter_by(key="SLOT_HOLD_HOURS").first()
        if setting and setting.value:
            hours = int(str(setting.value).strip())
            if hours > 0:
                return hours
    except (ValueError, TypeError, AttributeError):
        pass
    return SLOT_HOLD_HOURS_DEFAULT


def get_available_slots(activity_id, include_full=True, include_past=False):
    """Active slots for an activity, soonest first.

    Full slots are included by default so the signup form can render them greyed out —
    hiding them generates "is it cancelled?" emails, and visible scarcity converts.
    """
    from models import ActivitySlot

    query = ActivitySlot.query.filter(
        ActivitySlot.activity_id == activity_id,
        ActivitySlot.status == "active",
    )
    if not include_past:
        # starts_at is naive LOCAL, so compare against naive local now.
        query = query.filter(ActivitySlot.starts_at >= datetime.now())

    slots = query.order_by(ActivitySlot.starts_at.asc()).all()
    if not include_full:
        slots = [s for s in slots if not s.is_full]
    return slots


def claim_slot_seat(slot_id):
    """Atomically reserve one seat. Returns True iff THIS caller got it.

    ⚠️ The single conditional UPDATE is the whole admission control. SQLite serialises
    writers on a database-level lock, so the read (seats_taken < capacity) and the write
    (+1) cannot interleave with another worker. gunicorn runs 2 workers x 4 threads, so any
    Python-level check would be a lost-update race.

    NEVER replace this with `slot.seats_taken += 1` through the ORM, and never re-SELECT
    afterwards to "verify" — rowcount is the entire answer.

    Must be called inside an open transaction; the caller commits.
    """
    from sqlalchemy import text as _sql_text

    result = db.session.execute(_sql_text("""
        UPDATE activity_slot
           SET seats_taken = seats_taken + 1
         WHERE id = :slot_id
           AND status = 'active'
           AND seats_taken < capacity
    """), {"slot_id": slot_id})
    return result.rowcount == 1


def _release_slot_seat(slot_id):
    """Give one seat back. Guarded so the counter can never go negative."""
    from sqlalchemy import text as _sql_text

    db.session.execute(_sql_text("""
        UPDATE activity_slot
           SET seats_taken = seats_taken - 1
         WHERE id = :slot_id AND seats_taken > 0
    """), {"slot_id": slot_id})


def release_slot_booking(booking_id, reason, refund_credit=True):
    """Cancel a booking, free its seat, and refund the credit if one was consumed.

    Safe to call concurrently and repeatedly: the booking's status transition is the mutex,
    so two simultaneous cancels free exactly one seat and refund exactly one credit.

    A booking already in 'expired' was counter-decremented by the sweeper, so moving it to
    'cancelled' must NOT decrement again.

    Does not commit; the caller owns the transaction.
    Returns True if this call performed the cancellation.
    """
    from sqlalchemy import text as _sql_text
    from models import SlotBooking

    booking = SlotBooking.query.get(booking_id)
    if booking is None or booking.status == "cancelled":
        return False

    slot_id = booking.slot_id
    passport_id = booking.passport_id
    had_credit = bool(booking.credit_consumed)
    now = _utc_naive_now()

    params = {"bid": booking_id, "now": now, "reason": (reason or "")[:50]}

    # Live booking: win the mutex, then free the seat.
    rc_live = db.session.execute(_sql_text("""
        UPDATE slot_booking
           SET status='cancelled', cancelled_dt=:now, cancelled_reason=:reason,
               credit_consumed=0
         WHERE id=:bid AND status IN ('held','confirmed')
    """), params).rowcount

    if rc_live == 1:
        _release_slot_seat(slot_id)
    else:
        # Already expired (seat previously freed by the sweeper) — terminal-ise it only.
        rc_expired = db.session.execute(_sql_text("""
            UPDATE slot_booking
               SET status='cancelled', cancelled_dt=:now, cancelled_reason=:reason,
                   credit_consumed=0
             WHERE id=:bid AND status='expired'
        """), params).rowcount
        if rc_expired != 1:
            return False    # someone else got there first — touch nothing

    # Refund exactly once, and only if a credit was actually taken.
    if refund_credit and had_credit and passport_id:
        db.session.execute(_sql_text("""
            UPDATE passport SET uses_remaining = uses_remaining + 1 WHERE id = :pid
        """), {"pid": passport_id})
        _expire_orm(passport_id)

    db.session.expire(booking)
    return True


def _expire_orm(passport_id):
    """Drop a Passport from the identity map so later reads see raw-SQL changes."""
    from models import Passport as _Passport

    obj = db.session.identity_map.get((_Passport, (passport_id,)))
    if obj is not None:
        db.session.expire(obj)


def attach_slot_booking_to_passport(signup, passport, actor="system"):
    """Bind a held seat to a newly-created passport and consume one credit.

    This is the signup -> passport handoff. The customer chose their session at signup time,
    but the Passport may not exist for days (Interac e-transfer + admin approval), so the
    seat is held by a booking row that references only the signup until now.

    Called from BOTH passport-creation entry points:
      - app.approve_and_create_pass          (admin approval)
      - utils.auto_create_passport_from_signup (covers Stripe webhook AND the Interac bot)

    Idempotent, and NEVER raises: a slot problem must not stop a paying customer getting
    their passport. Does not commit; the caller owns the transaction.

    Returns: 'confirmed' | 'reclaimed' | 'slot_full' | 'no_booking' | 'already'
    """
    from sqlalchemy import text as _sql_text
    from models import SlotBooking

    try:
        if signup is None or passport is None:
            return "no_booking"

        booking = SlotBooking.query.filter_by(signup_id=signup.id).first()
        if booking is None:
            return "no_booking"          # non-scheduled activity, or a pre-feature signup
        if booking.status == "confirmed":
            return "already"             # webhook replay / admin double-click
        if booking.status == "cancelled":
            return "slot_full"           # deliberately cancelled — never resurrect

        outcome = "confirmed"

        # An expired hold may still be re-claimable if nobody took the seat meanwhile.
        if booking.status == "expired":
            if not claim_slot_seat(booking.slot_id):
                db.session.execute(_sql_text("""
                    UPDATE slot_booking
                       SET status='cancelled', cancelled_dt=:now,
                           cancelled_reason='expired_slot_full'
                     WHERE id=:bid AND status='expired'
                """), {"bid": booking.id, "now": _utc_naive_now()})
                db.session.expire(booking)
                return "slot_full"       # passport is still created; admin gets flagged
            outcome = "reclaimed"

        # Conditional confirm is the mutex — only one worker may bind this booking.
        rc = db.session.execute(_sql_text("""
            UPDATE slot_booking
               SET status='confirmed', passport_id=:pid, confirmed_dt=:now, held_until=NULL
             WHERE id=:bid AND status IN ('held','expired')
        """), {"bid": booking.id, "pid": passport.id, "now": _utc_naive_now()}).rowcount

        if rc != 1:
            return "already"

        # Consume the credit, but never below zero. A 0-credit passport type still gets a
        # confirmed booking — admin intent beats arithmetic — it just records no credit.
        rc_credit = db.session.execute(_sql_text("""
            UPDATE passport SET uses_remaining = uses_remaining - 1
             WHERE id = :pid AND uses_remaining > 0
        """), {"pid": passport.id}).rowcount

        if rc_credit == 1:
            db.session.execute(_sql_text("""
                UPDATE slot_booking SET credit_consumed=1 WHERE id=:bid
            """), {"bid": booking.id})
        else:
            logging.warning(
                "Slot booking %s confirmed for passport %s but no credit was available "
                "to consume (uses_remaining=0).", booking.id, passport.id
            )

        # Raw UPDATEs bypass the ORM — force re-reads to see the new values.
        db.session.expire(passport)
        db.session.expire(booking)
        return outcome

    except Exception as e:
        # Never let a scheduling problem cost a customer their paid passport.
        logging.error("attach_slot_booking_to_passport failed for signup %s: %s",
                      getattr(signup, "id", "?"), e, exc_info=True)
        return "no_booking"


def expire_stale_slot_holds(app=None):
    """Release seats whose hold has lapsed. Runs on the existing APScheduler.

    'expired' is deliberately distinct from 'cancelled': a late e-transfer can still
    re-claim an expired seat (see attach_slot_booking_to_passport), whereas cancelled is
    terminal. Also cancels the orphaned signup so the admin's pending badge stays honest.

    Returns the number of holds expired.
    """
    from sqlalchemy import text as _sql_text
    from models import SlotBooking, Signup

    def _run():
        now = _utc_naive_now()
        stale = SlotBooking.query.filter(
            SlotBooking.status == "held",
            SlotBooking.held_until.isnot(None),
            SlotBooking.held_until < now,
        ).all()

        expired_count = 0
        for booking in stale:
            rc = db.session.execute(_sql_text("""
                UPDATE slot_booking SET status='expired' WHERE id=:bid AND status='held'
            """), {"bid": booking.id}).rowcount
            if rc != 1:
                continue                      # another worker beat us to it
            _release_slot_seat(booking.slot_id)
            expired_count += 1

            if booking.signup_id:
                signup = Signup.query.get(booking.signup_id)
                if signup and signup.status in ("pending", "stripe_processing"):
                    signup.status = "cancelled"

        if expired_count:
            db.session.commit()
            logging.info("Expired %s stale slot hold(s).", expired_count)
        return expired_count

    try:
        if app is not None:
            with app.app_context():
                return _run()
        return _run()
    except Exception as e:
        logging.error("expire_stale_slot_holds failed: %s", e, exc_info=True)
        try:
            db.session.rollback()
        except Exception:
            pass
        return 0


def find_booking_to_fulfil(passport):
    """The booking this check-in is fulfilling, or None if the person is a walk-in.

    Returns the passport's unattended booking whose session falls TODAY, nearest to now.
    Used by both redeem routes to decide whether the scan costs a credit:

        booking found  -> they reserved this session and already paid the credit at
                          booking time. Stamp attendance, take nothing.
        None           -> walk-in (or non-scheduled activity). Deduct one credit, exactly
                          as Minipass has always behaved.

    ⚠️ slot.starts_at is NAIVE LOCAL wall-clock (see models.py). Compare it with
    datetime.now(), never datetime.now(timezone.utc) — mixing them shifts every session
    by the UTC offset and would silently match the wrong day.

    Note bookings with passport_id IS NULL (handoff failed) are invisible here; the admin
    was already warned at passport-creation time.
    """
    from models import SlotBooking, ActivitySlot

    try:
        if passport is None or not getattr(passport, "id", None):
            return None
        activity = getattr(passport, "activity", None)
        if not activity or not getattr(activity, "uses_scheduling", False):
            return None

        now_local = datetime.now()
        day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        candidates = SlotBooking.query.join(
            ActivitySlot, ActivitySlot.id == SlotBooking.slot_id
        ).filter(
            SlotBooking.passport_id == passport.id,
            SlotBooking.status.in_(("held", "confirmed")),
            SlotBooking.attended_dt.is_(None),
            ActivitySlot.status == "active",
            ActivitySlot.starts_at >= day_start,
            ActivitySlot.starts_at < day_end,
        ).all()

        if not candidates:
            return None

        # Nearest session to right now — handles an activity running 11:00 and 14:00 on
        # the same day, where the morning scan should fulfil the morning booking.
        return min(candidates, key=lambda b: abs((b.slot.starts_at - now_local).total_seconds()))

    except Exception as e:
        # A lookup problem must never block a check-in. Falling through to None means the
        # scan is treated as a walk-in (a credit is taken), which is the safe direction:
        # it under-serves rather than giving away free attendance.
        logging.error("find_booking_to_fulfil failed for passport %s: %s",
                      getattr(passport, "id", "?"), e, exc_info=True)
        return None


def has_booking_today(passport):
    """True if this passport has an unattended booking today — used to decide whether the
    admin 'Check In' button should be offered even when the credit balance is 0."""
    return find_booking_to_fulfil(passport) is not None


def count_active_bookings(passport):
    """How many upcoming sessions this passport currently holds (for customer display)."""
    from models import SlotBooking

    try:
        if passport is None or not getattr(passport, "id", None):
            return 0
        bookings = SlotBooking.query.filter(
            SlotBooking.passport_id == passport.id,
            SlotBooking.status.in_(("held", "confirmed")),
        ).all()
        now_local = datetime.now()
        return sum(1 for b in bookings if b.slot and b.slot.starts_at >= now_local)
    except Exception as e:
        logging.warning("count_active_bookings failed: %s", e)
        return 0


def _get_pass_url(passport):
    """Absolute URL to this passport's public page, for the email CTA.

    This is the ONLY way a customer reaches their pass page — they have no account and
    never visit the platform otherwise. Without this link, booking additional sessions
    from /pass/<code> is unreachable in practice.

    Uses the SITE_URL setting (same source as every other email URL). Returns "" if
    SITE_URL isn't configured, so the template simply omits the button.
    """
    try:
        pass_code = getattr(passport, "pass_code", None)
        if not pass_code:
            return ""
        base = (get_setting('SITE_URL', '') or '').rstrip('/')
        if not base:
            return ""
        return f"{base}/pass/{pass_code}"
    except Exception as e:
        logging.warning("Could not build pass URL for email: %s", e)
        return ""


def _get_booked_slot_labels(passport):
    """French labels for a passport's upcoming booked sessions, for the email owner card.

    Returns [] for non-scheduled activities so the email renders exactly as before.
    Never raises — an email must not fail because of a scheduling lookup.
    """
    from models import SlotBooking

    try:
        activity = getattr(passport, "activity", None)
        if not activity or not getattr(activity, "uses_scheduling", False):
            return []
        passport_id = getattr(passport, "id", None)
        if not passport_id:
            return []

        bookings = SlotBooking.query.filter(
            SlotBooking.passport_id == passport_id,
            SlotBooking.status.in_(("held", "confirmed")),
        ).all()
        # Exclude sessions already attended, not just past ones. A session earlier today that
        # the customer has been checked into is still "upcoming" by start time, and it was
        # showing as their Prochaine séance in the email while the passport page — which does
        # reject attended — named the next real one. The two must agree.
        upcoming = [b for b in bookings
                    if b.slot and b.slot.starts_at >= datetime.now()
                    and not b.attended_dt]
        upcoming.sort(key=lambda b: b.slot.starts_at)
        return [format_slot_label(b.slot) for b in upcoming]
    except Exception as e:
        logging.warning("Could not resolve booked slots for email: %s", e)
        return []


def _build_history_rows(history):
    """Flatten get_pass_history_data() into rows for the email history table.

    Each row is {label, date, by}. The order is the passport's actual life: created, paid,
    then each use in sequence, then expiry — which is what makes this table worth having in
    the email at all ("issued then, paid then, used here on this date, scanned by them").

    Mirrors the Historique table on pass.html so the email and the passport page can never
    tell different stories. Never raises: an email must not fail over its history block.
    """
    # Same shortening as app.py's trim_email filter, restated here because importing app
    # into utils would be circular. Shows "kdresdell" rather than the full address.
    def _who(value):
        return value.split("@")[0] if value else ""

    def _when(value):
        """"2026-08-25 09:19" -> "25 août, 09:19".

        The stored format is sortable but long, and three of them stacked in a narrow column
        read as a log dump. Uses the same French month names as format_slot_label so the dates
        in the history match the dates in the session list.
        """
        if not value:
            return ""
        try:
            dt = datetime.strptime(value[:16], "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return value
        return f"{dt.day} {_FR_MONTHS.get(dt.month, '')}, {dt.strftime('%H:%M')}"

    rows = []
    try:
        if not history:
            return rows

        if history.get("created"):
            rows.append({"label": "Création",
                         "date": _when(history["created"]),
                         "by": _who(history.get("created_by"))})

        if history.get("paid"):
            rows.append({"label": "Paiement",
                         "date": _when(history["paid"]),
                         "by": _who(history.get("paid_by"))})

        for i, r in enumerate(history.get("redemptions") or [], start=1):
            rows.append({"label": f"Participation {i}",
                         "date": _when(r.get("date", "")),
                         "by": _who(r.get("by"))})

        if history.get("expired"):
            rows.append({"label": "Expiré", "date": _when(history["expired"]), "by": ""})
    except Exception as e:
        logging.warning("Could not build email history rows: %s", e)
        return []
    return rows


def reconcile_slot_seat_counts(activity_id=None, fix=False):
    """Compare ActivitySlot.seats_taken against the live booking ledger.

    seats_taken is the admission gate; bookings are the ledger. Any drift is a bug, not an
    expected state. Read-only unless fix=True.

    Returns a list of {slot_id, activity_id, seats_taken, actual} for drifting slots.
    """
    from sqlalchemy import text as _sql_text

    where_activity = "WHERE s.activity_id = :aid" if activity_id else ""
    rows = db.session.execute(_sql_text(f"""
        SELECT s.id, s.activity_id, s.seats_taken,
               COALESCE(COUNT(b.id), 0) AS actual
          FROM activity_slot s
          LEFT JOIN slot_booking b
                 ON b.slot_id = s.id AND b.status IN ('held','confirmed')
          {where_activity}
         GROUP BY s.id, s.activity_id, s.seats_taken
        HAVING s.seats_taken != COALESCE(COUNT(b.id), 0)
    """), ({"aid": activity_id} if activity_id else {})).fetchall()

    drift = [{"slot_id": r[0], "activity_id": r[1], "seats_taken": r[2], "actual": r[3]}
             for r in rows]

    if fix and drift:
        for d in drift:
            db.session.execute(_sql_text("""
                UPDATE activity_slot SET seats_taken = :actual WHERE id = :sid
            """), {"actual": d["actual"], "sid": d["slot_id"]})
        db.session.commit()
        logging.warning("Reconciled %s slot(s) with drifting seat counts: %s",
                        len(drift), drift)

    return drift


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
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(size * 0.5))
    except (IOError, OSError):
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', int(size * 0.5))
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


def save_optimized_image(file_stream, dest_folder, prefix="upload", max_size=(1200, 800)):
    """Save uploaded image: resize to max dimensions, convert to JPEG quality=85.

    Returns the saved filename. For PDF/SVG files, callers should skip this function.
    """
    from PIL import Image as _Image

    img = _Image.open(file_stream)

    # Flatten transparency to white background
    if img.mode in ('RGBA', 'P'):
        bg = _Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    img.thumbnail(max_size, _Image.Resampling.LANCZOS)

    filename = f"{prefix}_{uuid.uuid4().hex[:10]}.jpg"
    os.makedirs(dest_folder, exist_ok=True)
    img.save(os.path.join(dest_folder, filename), 'JPEG', quality=85, optimize=True)
    return filename


def generate_qr_code(pass_code):
    qr = qrcode.make(pass_code)
    img_bytes = io.BytesIO()
    qr.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return base64.b64encode(img_bytes.read()).decode()



@lru_cache(maxsize=512)
def generate_qr_code_image(pass_code: str, box_size: int = 10) -> bytes:
    """Return PNG bytes for the given pass_code QR. Result is cached — same code always returns same bytes."""
    qr = qrcode.make(pass_code, box_size=box_size)
    img_bytes = io.BytesIO()
    qr.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


def generate_signup_card_image(signup_url: str, organization_name: str,
                               activity_name: str, passport_type_name: str) -> bytes:
    """Build a clean 4:5 PNG signup card containing a reliably scannable QR code."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1080, 1350
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    font_paths = {
        "regular": [
            "/usr/share/fonts/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
        "bold": [
            "/usr/share/fonts/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ],
    }

    def load_font(size, bold=False):
        for path in font_paths["bold" if bold else "regular"]:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

    def text_width(text, font):
        box = draw.textbbox((0, 0), text, font=font)
        return box[2] - box[0]

    def wrap_text(text, font, max_width, max_lines):
        words = (text or "").split()
        if not words:
            return [""]
        lines = []
        current = words.pop(0)
        while words:
            candidate = f"{current} {words[0]}"
            if text_width(candidate, font) <= max_width:
                current = candidate
                words.pop(0)
            else:
                lines.append(current)
                current = words.pop(0)
                if len(lines) == max_lines - 1:
                    break
        if words:
            remainder = " ".join([current] + words)
            while remainder and text_width(remainder + "…", font) > max_width:
                remainder = remainder[:-1].rstrip()
            current = remainder + "…"
        lines.append(current)
        return lines[:max_lines]

    def draw_centered_lines(lines, font, y, fill, spacing):
        for line in lines:
            box = draw.textbbox((0, 0), line, font=font)
            line_width = box[2] - box[0]
            line_height = box[3] - box[1]
            draw.text(((width - line_width) / 2, y), line, font=font, fill=fill)
            y += line_height + spacing
        return y

    org_font = load_font(42, bold=True)
    activity_font = load_font(52, bold=True)
    type_font = load_font(34)
    prompt_font = load_font(38, bold=True)

    org_lines = wrap_text(organization_name or "minipass", org_font, 900, 1)
    y = draw_centered_lines(org_lines, org_font, 72, "#343a46", 8)
    y += 34
    y = draw_centered_lines(wrap_text(activity_name, activity_font, 900, 2),
                            activity_font, y, "#1d273b", 10)
    y += 20
    y = draw_centered_lines(wrap_text(passport_type_name, type_font, 860, 2),
                            type_font, y, "#626976", 8)

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    qr.add_data(signup_url)
    qr.make(fit=True)
    module_count = qr.modules_count + 8
    box_size = max(8, min(18, 680 // module_count))
    qr.box_size = box_size
    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_y = max(370, int(y + 32))
    image.paste(qr_image, ((width - qr_image.width) // 2, qr_y))

    prompt_y = qr_y + qr_image.height + 38
    draw_centered_lines(["Scan to register"], prompt_font, prompt_y, "#1d273b", 8)

    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG", optimize=True)
    return img_bytes.getvalue()


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
            uses_remaining=(passport_type.sessions_included if passport_type else 1) * signup.requested_sessions,
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

        # Session scheduling: bind the held seat to the new passport and consume one
        # credit. This single call covers BOTH the Stripe webhook and the Interac
        # email-parser bot, since both funnel through this function.
        slot_result = attach_slot_booking_to_passport(signup, passport, actor=marked_paid_by)
        if slot_result == "slot_full":
            print(f"   [auto_create_passport] WARNING: session for signup {signup.id} "
                  f"is now full — passport created but needs manual rebooking")

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
            
            # Check for IMAP-specific credentials (used in local dev)
            gmail_user = get_setting("IMAP_USERNAME") or gmail_user
            gmail_password = get_setting("IMAP_PASSWORD") or gmail_password

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






def get_active_passports_query(activity_id=None):
    """
    Single source of truth for 'active passport' definition.
    An active passport: has uses remaining AND belongs to a non-archived activity.
    """
    query = Passport.query.join(Activity).filter(
        Activity.status != 'archived',
        Passport.uses_remaining > 0
    )
    if activity_id:
        query = query.filter(Passport.activity_id == activity_id)
    return query


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
        
        # KPI 2: Active Users (passports with uses_remaining > 0, non-archived activity)
        current_active_users = get_active_passports_query(activity_id=activity_id).count()
        
        if period != 'all':
            # Approximate: compare passes created in current vs previous period as a proxy
            current_created = get_base_passport_query().filter(
                Passport.created_dt >= current_start,
                Passport.created_dt <= current_end
            ).count()
            prev_created = get_base_passport_query().filter(
                Passport.created_dt >= prev_start,
                Passport.created_dt <= prev_end
            ).count()
            prev_active_users = prev_created
            if prev_created > 0:
                active_users_change = ((current_created - prev_created) / prev_created * 100)
            elif current_created > 0:
                active_users_change = 100.0
            else:
                active_users_change = 0
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
        
        active_users_trend = build_count_trend(Passport, None, trend_days)
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
        
        # Check for IMAP-specific credentials (used in local dev)
        user = get_setting("IMAP_USERNAME") or user
        pwd = get_setting("IMAP_PASSWORD") or pwd

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
                    # First: compare IMAP UIDs - definitive differentiator
                    # Different UIDs = different emails. One has UID and other is NULL = also different.
                    # Both NULL = can't tell, fall back to time-based check.
                    if uid and (not existing_payment.email_uid or str(uid) != str(existing_payment.email_uid)):
                        # Before treating as new payment: check if received date is identical.
                        # Interac sometimes sends duplicate notification emails for the same payment
                        # (same Date header, different IMAP UID). Don't process these as new payments.
                        is_duplicate_notification = False
                        if email_received_date and existing_payment.email_received_date:
                            nd = email_received_date if email_received_date.tzinfo else email_received_date.replace(tzinfo=timezone.utc)
                            ed = existing_payment.email_received_date
                            if ed.tzinfo is None:
                                ed = ed.replace(tzinfo=timezone.utc)
                            if abs((nd - ed).total_seconds()) < 60:
                                is_duplicate_notification = True

                        if is_duplicate_notification:
                            print(f"⚠️ DUPLICATE INTERAC NOTIFICATION: same received date, different UID ({uid} vs {existing_payment.email_uid}) - archiving and skipping")
                            if uid:
                                try:
                                    mail.uid("COPY", uid, processed_folder)
                                    mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                                except Exception as dup_e:
                                    print(f"   Could not archive duplicate: {dup_e}")
                            results["skipped"] += 1
                            continue

                        print(f"🆕 DIFFERENT EMAIL UID ({uid} vs {existing_payment.email_uid}): processing as new payment")
                        # Fall through to process as new payment
                    else:
                        # Fallback: use time-based comparison when UIDs unavailable
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
                    # Before retrying: check if this is a duplicate Interac notification (same received
                    # date, different UID). If so, archive this email and keep the existing record
                    # pointing to the original UID — prevents orphaned emails in inbox.
                    if uid and existing_payment.email_uid and str(uid) != str(existing_payment.email_uid):
                        is_duplicate_notification = False
                        if email_received_date and existing_payment.email_received_date:
                            nd = email_received_date if email_received_date.tzinfo else email_received_date.replace(tzinfo=timezone.utc)
                            ed = existing_payment.email_received_date
                            if ed.tzinfo is None:
                                ed = ed.replace(tzinfo=timezone.utc)
                            if abs((nd - ed).total_seconds()) < 60:
                                is_duplicate_notification = True

                        if is_duplicate_notification:
                            print(f"⚠️ DUPLICATE INTERAC NOTIFICATION (NO_MATCH): same received date, different UID ({uid} vs {existing_payment.email_uid}) - archiving duplicate and keeping original")
                            try:
                                mail.uid("COPY", uid, processed_folder)
                                mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                            except Exception as dup_e:
                                print(f"   Could not archive duplicate: {dup_e}")
                            results["skipped"] += 1
                            continue

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
                    Activity.workflow_type == "payment_first",
                    Signup.payment_method == "interac",
                    Signup.status == "pending"
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
                        if uid:
                            existing_payment.email_uid = uid
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
                            email_received_date=email_received_date,
                            email_uid=uid
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

                    if not unpaid_passports:
                        # Nothing to compare against — say so plainly instead of the
                        # generic "all names below threshold" wording, which is
                        # meaningless when there were zero candidates.
                        note_parts.append(f"No unpaid passport(s) exist for ${amt}.")
                    elif top_candidates:
                        # Show the closest name matches and their scores
                        candidate_strs = [f"{cname} ({score:.0f}%)" for cname, score in top_candidates]
                        note_parts.append(f"Found {len(unpaid_passports)} unpaid passport(s) for ${amt}, but all names below {threshold}% threshold. Closest: {', '.join(candidate_strs)}.")
                    else:
                        # Unpaid passports exist, but none scored above the diagnostic floor
                        note_parts.append(f"Found {len(unpaid_passports)} unpaid passport(s) for ${amt}, but all names below {threshold}% threshold (no candidates above {DIAGNOSTIC_MIN}%).")
                        example_names = [p.user.name for p in unpaid_passports[:3] if p.user]
                        if example_names:
                            note_parts.append(f"Available names: {', '.join(example_names[:3])}")

                    # Check for pending payment-first Interac signups at this amount and
                    # report the true reason auto-match didn't use them — a real name
                    # score, not a blanket "ambiguous" label.
                    from models import Signup as SignupModel, Activity as ActivityModel
                    pending_interac = db.session.query(SignupModel).join(ActivityModel).filter(
                        SignupModel.passport_id == None,
                        SignupModel.requested_amount == payment_amount,
                        ActivityModel.workflow_type == "payment_first",
                        SignupModel.payment_method == "interac",
                        SignupModel.status == "pending"
                    ).all()
                    if pending_interac:
                        signup_scores = []
                        for s in pending_interac:
                            if not s.user:
                                continue
                            s_score = fuzz.ratio(normalized_payment_name, normalize_name(s.user.name))
                            signup_scores.append((s.user.name, s_score))
                        signup_scores.sort(key=lambda x: x[1], reverse=True)

                        if not signup_scores:
                            pass
                        elif len(signup_scores) > 1 and (signup_scores[0][1] - signup_scores[1][1]) < 5:
                            # Genuine tie between multiple candidates — this is actually ambiguous
                            tie_strs = [f"{cname} ({score:.0f}%)" for cname, score in signup_scores if score >= signup_scores[0][1] - 5]
                            note_parts.append(f"Note: {len(tie_strs)} pending Interac signup(s) tied for this amount, ambiguous: {', '.join(tie_strs)}. Manual review required.")
                        else:
                            cname, score = signup_scores[0]
                            note_parts.append(f"Note: closest pending Interac signup is '{cname}' ({score:.0f}%) — below the {threshold}% threshold. Review and link manually if correct.")

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

    # Check for IMAP-specific credentials (used in local dev)
    user = get_setting("IMAP_USERNAME") or user
    pwd = get_setting("IMAP_PASSWORD") or pwd

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
                import re
                m = re.search(r'marked as PAID \((\w+)\)', action_text, re.IGNORECASE)
                if m:
                    method_labels = {"cash": "Cash", "pos": "POS/TPV", "cheque": "Cheque",
                                     "stripe": "Stripe", "interac": "Interac"}
                    method = method_labels.get(m.group(1).lower(), m.group(1).title())
                    log_type = f"Marked Paid ({method})"
                else:
                    log_type = "Marked Paid"  # backward-compatible for old entries
            elif "approved" in action_text and "signup" in action_text:
                log_type = "Signup Approved"
            elif "rejected" in action_text and "signup" in action_text:
                log_type = "Signup Rejected"
            elif "cancelled" in action_text and "signup" in action_text:
                log_type = "Signup Cancelled"  # ✅ NEW detection for cancelled
            elif "announcement sent" in action_text:
                log_type = "Announcement Sent"
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
            elif "stripe payment received" in action_text:
                log_type = "Stripe Payment Received"
            elif "stripe payout received" in action_text:
                log_type = "Stripe Payout Received"
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

        # 🟠 Email Sent / Email Failed / Email Dismissed
        for e in EmailLog.query.all():
            pass_code_display = e.pass_code if e.pass_code else "App-Sent"
            if e.result == "FAILED":
                error_hint = f" — Error: {e.error_message[:60]}" if e.error_message else ""
                logs.append({
                    "timestamp": e.timestamp,
                    "type": "Email Failed",
                    "user": e.to_email,
                    "details": f"To {e.to_email} — \"{e.subject}\" (Code: {pass_code_display}){error_hint}",
                    "email_log_id": e.id
                })
            elif e.result == "DISMISSED":
                logs.append({
                    "timestamp": e.timestamp,
                    "type": "Email Dismissed",
                    "user": e.to_email,
                    "details": f"To {e.to_email} — \"{e.subject}\" (Code: {pass_code_display})",
                    "email_log_id": None
                })
            else:
                logs.append({
                    "timestamp": e.timestamp,
                    "type": "Email Sent",
                    "user": e.to_email,
                    "details": f"To {e.to_email} — \"{e.subject}\" (Code: {pass_code_display})",
                    "email_log_id": e.id
                })

        # 🔵 Payments
        for p in EbankPayment.query.all():
            if p.result == "MATCHED":
                log_type = "Interac Payment Matched"
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

# Templates whose layout renders no QR code, so no CID part should be attached for them.
# Keep in step with show_qr=False in the corresponding templates/email/<name>.html.
NO_QR_TEMPLATES = {'latePayment'}

# QR module box size for the email pass block: 33 modules (version 2 + border) * 5px = 165px,
# matching the qr_block() display size exactly so no client has to rescale the PNG (rescaling a
# non-divisor size forces browser smoothing and makes the code look muddy — Outlook also ignores
# the image-rendering:pixelated CSS that would otherwise mask it).
EMAIL_QR_BOX_SIZE = 5

# The seven transactional email types, named as they appear in Activity.email_templates.
EMAIL_TEMPLATE_TYPES = {
    'newPass', 'paymentReceived', 'latePayment', 'redeemPass',
    'signup', 'signup_payment_first', 'survey_invitation',
}


def template_key(template_name: str) -> str:
    """Reduce any spelling of a template name to its bare key.

    Call sites name templates inconsistently — "newPass" from the preview,
    "newPass_compiled/index.html" from older code, "email/newPass.html" from a resolved path.
    The _compiled/_original suffixes no longer correspond to any directory, but they still
    appear in stored settings and EmailLog rows, so they have to keep normalising.

    Returns the key unchanged if it isn't one of the known types; callers decide what that
    means (safe_template builds a path from it, send_email_async treats it as "not ours").
    """
    name = (template_name or "").lstrip("/")
    name = name.replace("email_templates/", "").replace("email/", "")
    name = name.split("/")[0]
    name = name.replace(".html", "").replace("_compiled", "").replace("_original", "")
    # Legacy alias from before the survey template was renamed.
    if name == "email_survey_invitation":
        name = "survey_invitation"
    return name


def safe_template(template_name: str) -> str:
    """Resolve any spelling of a template name to its file under templates/email/."""

    # Idempotent: some callers resolve the path themselves and hand the result to send_email,
    # which resolves it again. Without this a second pass would re-prefix an already-good path.
    template_name = template_name.lstrip("/")
    if os.path.exists(os.path.join("templates", template_name)):
        return template_name

    return f"email/{template_key(template_name)}.html"


def send_email(subject, to_email, template_name=None, context=None, inline_images=None, html_body=None, timestamp_override=None, email_config=None, use_hosted_images=False, user=None, activity=None, operational=False):
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
        context['organization_name'] = get_setting('ORG_NAME', 'minipass')

    # Set payment email from settings if not in context
    if 'payment_email' not in context:
        payment_email_setting = get_setting("MAIL_USERNAME")
        if payment_email_setting:
            context['payment_email'] = payment_email_setting

    # Use ORG_ADDRESS setting for address
    context['organization_address'] = get_setting('ORG_ADDRESS', '')

    # Always set these URLs and support email
    from urllib.parse import quote
    context['unsubscribe_url'] = f"{base_url}/unsubscribe?email={quote(to_email)}"
    context['privacy_url'] = f"{base_url}/privacy"
    context['base_url'] = base_url

    # Add support_email using MAIL_DEFAULT_SENDER setting
    context['support_email'] = get_setting("MAIL_DEFAULT_SENDER") or ""
    
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
    msg["Reply-To"] = from_email

    if not operational:
        if context.get('unsubscribe_url'):
            msg["List-Unsubscribe"] = f"<{context['unsubscribe_url']}>"
            msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

    # Set email priority based on template type (transactional vs bulk)
    if operational:
        msg["Precedence"] = "normal"
        msg["X-Priority"] = "1"
        msg["Importance"] = "high"
    else:
        is_transactional = template_name and ('survey' in template_name or 'Pass' in template_name or 'payment' in template_name or 'signup' in template_name or 'announcement' in template_name)
        if is_transactional:
            msg["Precedence"] = "normal"  # Transactional email
            msg["X-Priority"] = "3"  # Normal priority (1=high, 3=normal, 5=low)
            msg["Importance"] = "normal"
        else:
            msg["Precedence"] = "bulk"  # Bulk/newsletter emails

    msg["X-Mailer"] = "Minipass/1.0"
    if not operational:
        msg["Auto-Submitted"] = "auto-generated"

    # Generate unique Message-ID
    import uuid
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    msg["Message-ID"] = f"<{timestamp}.{uuid.uuid4().hex}@minipass.me>"
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
        # 🛠️ DEV MODE: use .env MAIL_SERVER/MAIL_USERNAME/MAIL_PASSWORD (Gmail)
        # Dev mode always wins — emails never reach real users regardless of email_config
        from flask import current_app
        import os
        if current_app.debug:
            original_to = to_email
            to_email = os.environ.get("MAIL_USERNAME", to_email)
            smtp_host = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
            smtp_port = int(os.environ.get("MAIL_PORT", 587))
            smtp_user = os.environ.get("MAIL_USERNAME")
            smtp_pass = os.environ.get("MAIL_PASSWORD")
            use_tls = True
            use_ssl = False
            print(f"🛠️ DEV MODE: redirecting email from {original_to} → {to_email} via {smtp_host}:{smtp_port}")
        elif email_config:
            smtp_host = email_config['MAIL_SERVER']
            smtp_port = email_config['MAIL_PORT']
            smtp_user = email_config['MAIL_USERNAME']
            smtp_pass = email_config['MAIL_PASSWORD'] if email_config['MAIL_PASSWORD'] else None
            use_tls = email_config.get('MAIL_USE_TLS', True)
            use_ssl = email_config.get('MAIL_USE_SSL', False)
            sender_name = email_config.get('SENDER_NAME', 'Minipass')

            # Replace From and Reply-To with org-specific sender (del first — MIME appends, not overwrites)
            from_email = email_config['MAIL_DEFAULT_SENDER']
            del msg['From']
            msg['From'] = formataddr((sender_name, from_email))
            del msg['Reply-To']
            msg['Reply-To'] = from_email
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
    # Extract operational flag before thread starts (closure capture)
    operational = kwargs.get("operational", False)
    # Same reasoning as activity_id: a live context['pass_data'] ORM object belongs to the
    # *caller's* session, which can be torn down before this thread gets to it (a request's
    # session closing once the response is sent, while the send is still running in the
    # background). Reload a fresh, thread-session-bound Passport from this instead of touching
    # the original object — see the reload block in send_in_thread().
    _reload_pass_code = (kwargs.get("context") or {}).get("pass_code")

    def send_in_thread():
        with app.app_context():
            try:
                from utils import send_email
                from models import EmailLog, Activity, Passport
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

                # Reload pass_data in thread context too, for the same reason as activity above.
                # The template rendering below reads pass_data.user / .activity / .uses_remaining
                # extensively; a detached original would only fail once the calling thread's
                # session happened to already be gone by the time rendering runs, which made this
                # intermittent rather than a reliable, obvious break.
                if _reload_pass_code and context.get("pass_data") is not None:
                    fresh_pass_data = Passport.query.filter_by(pass_code=_reload_pass_code).first()
                    if fresh_pass_data:
                        context["pass_data"] = fresh_pass_data
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
                    # One normaliser, shared with safe_template(), instead of a
                    # 27-entry table of every spelling a caller might use.
                    _key = template_key(template_name)
                    template_type = _key if _key in EMAIL_TEMPLATE_TYPES else None
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

                # Custom hero images for the activity, when a caller is still using CID
                # images. The compiled-template inline_images.json loading that used to sit
                # here is gone with templates/email_templates/: hero and logo are hosted URLs
                # now (docs/EMAIL.md) and only the QR is ever a CID part.
                if template_name and not html_body and not use_hosted_images and activity_in_thread:
                    from utils import get_activity_hero_image

                    _key = template_key(template_name)
                    if _key in EMAIL_TEMPLATE_TYPES:
                        hero_data, is_custom, is_template_default = get_activity_hero_image(
                            activity_in_thread, _key)
                        if hero_data and not is_template_default:
                            hero_cid = HERO_CID_MAP.get(_key)
                            if hero_cid:
                                inline_images[hero_cid] = hero_data
                                hero_type = "custom" if is_custom else "activity fallback"
                                print(f"\u2705 {hero_type} hero image loaded in send_email_async: "
                                      f"template={_key}, cid={hero_cid}, size={len(hero_data)} bytes")

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
                send_result = send_email(
                    subject=subject,
                    to_email=to_email,
                    template_name=template_name,
                    context=context,
                    inline_images=inline_images,
                    html_body=html_body,
                    timestamp_override=timestamp_override,
                    user=user,
                    activity=activity_in_thread,
                    use_hosted_images=use_hosted_images,
                    operational=operational,
                )

                if send_result is False:
                    raise RuntimeError("SMTP delivery failed — send_email() returned False")

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
                    # notify_pass_event passes passport as pass_data object
                    elif "pass_data" in context:
                        pd = context["pass_data"]
                        pass_code = getattr(pd, "pass_code", None)
                        user_name = getattr(getattr(pd, "user", None), "name", None)
                
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

                # Try to extract pass_code and context safely for error log
                error_pass_code = None
                error_user_name = None
                error_activity_name = None
                error_context = kwargs.get("context", {})
                if error_context:
                    if "hockey_pass" in error_context:
                        error_pass_code = error_context.get("hockey_pass", {}).get("pass_code")
                        error_user_name = error_context.get("hockey_pass", {}).get("user_name")
                    elif "pass_code" in error_context:
                        error_pass_code = error_context.get("pass_code")
                        error_user_name = error_context.get("user_name")
                    elif "pass_data" in error_context:
                        pd = error_context.get("pass_data")
                        error_pass_code = getattr(pd, "pass_code", None)
                        error_user_name = getattr(getattr(pd, "user", None), "name", None)
                    error_activity_name = error_context.get("activity_name")

                db.session.add(EmailLog(
                    to_email=kwargs.get("to_email"),
                    subject=subject,
                    pass_code=error_pass_code,
                    template_name=kwargs.get("template_name") or "",
                    context_json=json.dumps({
                        "user_name": error_user_name,
                        "activity_name": error_activity_name,
                        "template_type": kwargs.get("template_name"),
                        "special_message": error_context.get("special_message", "") if error_context else "",
                        "error": str(e),
                    }),
                    result="FAILED",
                    error_message=str(e),
                    timestamp=kwargs.get("timestamp_override") or datetime.now(timezone.utc)
                ))
                db.session.commit()

    thread = threading.Thread(target=send_in_thread)
    thread.start()


def send_bulk_sequential(app, email_jobs, subject, activity=None, operational=False, delay=0.3):
    """
    Send multiple emails in a single background thread, sequentially.

    Reads SMTP config once, then sends one-by-one — no DB pool pressure,
    no simultaneous SMTP connections. Designed to replace N-thread bulk sends.

    Args:
        email_jobs: list of dicts with keys: to_email (str), html_body (str)
        subject: email subject (same for all)
        activity: Activity object (optional, for logging)
        operational: if True, bypasses unsubscribe checks
        delay: seconds between sends (default 0.3)
    """
    import time

    activity_id = activity.id if activity and hasattr(activity, 'id') else None

    def _run():
        with app.app_context():
            from utils import send_email, get_setting
            from models import EmailLog
            import json
            from datetime import datetime, timezone

            smtp_config = {
                'MAIL_SERVER':         get_setting('MAIL_SERVER'),
                'MAIL_PORT':           int(get_setting('MAIL_PORT', '587') or 587),
                'MAIL_USERNAME':       get_setting('MAIL_USERNAME'),
                'MAIL_PASSWORD':       get_setting('MAIL_PASSWORD'),
                'MAIL_USE_TLS':        True,
                'MAIL_USE_SSL':        False,
                'MAIL_DEFAULT_SENDER': get_setting('MAIL_DEFAULT_SENDER') or get_setting('MAIL_USERNAME'),
                'SENDER_NAME':         get_setting('SENDER_NAME') or get_setting('ORG_NAME') or 'Minipass',
            }

            if not smtp_config['MAIL_SERVER']:
                logging.error("❌ send_bulk_sequential: MAIL_SERVER is empty — aborting bulk send")
                return

            sent = 0
            failed = 0

            for job in email_jobs:
                to_email = job.get('to_email')
                html_body = job.get('html_body')

                try:
                    result = send_email(
                        subject=subject,
                        to_email=to_email,
                        html_body=html_body,
                        email_config=smtp_config,
                        operational=operational,
                    )

                    log_entry = EmailLog(
                        timestamp=datetime.now(timezone.utc),
                        to_email=to_email,
                        subject=subject,
                        template_name='',
                        pass_code=None,
                        result='SENT' if result else 'FAILED',
                        context_json=json.dumps({'activity_id': activity_id}),
                        error_message=None if result else 'send_email() returned False',
                    )
                    db.session.add(log_entry)
                    db.session.commit()

                    if result:
                        sent += 1
                    else:
                        failed += 1
                        logging.error(f"❌ Bulk send failed for {to_email}")

                except Exception as e:
                    failed += 1
                    logging.exception(f"❌ Bulk send exception for {to_email}: {e}")
                    db.session.rollback()
                    try:
                        log_entry = EmailLog(
                            timestamp=datetime.now(timezone.utc),
                            to_email=to_email,
                            subject=subject,
                            template_name='',
                            result='FAILED',
                            context_json=json.dumps({'error': str(e)}),
                            error_message=str(e),
                        )
                        db.session.add(log_entry)
                        db.session.commit()
                    except Exception:
                        pass

                if delay > 0:
                    time.sleep(delay)

            logging.info(f"✅ Bulk send complete — {sent} sent, {failed} failed (subject: {subject})")

            if failed > 0:
                admin_email = get_setting('ADMIN_EMAIL') or get_setting('MAIL_USERNAME')
                if admin_email:
                    try:
                        body = (
                            f"<p>⚠️ Bulk announcement completed with <strong>{failed} failure(s)</strong>.</p>"
                            f"<p><strong>Subject:</strong> {subject}<br>"
                            f"<strong>Sent:</strong> {sent}<br>"
                            f"<strong>Failed:</strong> {failed}</p>"
                            f"<p>Check the Email Log in your dashboard for details on which recipients failed.</p>"
                        )
                        send_email(
                            subject=f"⚠️ Announcement partially failed — {failed} email(s) not delivered",
                            to_email=admin_email,
                            html_body=body,
                            operational=True,
                        )
                        logging.info(f"📧 Failure notification sent to {admin_email}")
                    except Exception as notify_err:
                        logging.error(f"❌ Could not send failure notification: {notify_err}")

    thread = threading.Thread(target=_run)
    thread.start()


def _fr_money(amount):
    """Format an amount the way the email templates do: 50,00 $.

    Quebec French puts the sign after the number with a non-breaking space, and uses a comma
    for the decimal. Kept in step with the `money()` macro in templates/email/components.html
    so a single email never shows both "$50.00" and "50,00 $".
    """
    return f"{amount or 0:.2f}".replace(".", ",") + " $"


def notify_signup_event(app, *, signup, activity, timestamp=None):
    from utils import send_email_async, get_email_context, get_setting
    from flask import url_for
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
        base_context["requested_amount"] = _fr_money(signup.requested_amount)
        base_context["payment_email"] = payment_email

    # Get email context using activity-specific templates
    email_context = get_email_context(activity, template_type, base_context)
    
    # Extract template values
    subject = email_context.get('subject', "Confirmation d'inscription")
    title = email_context.get('title', "Votre Inscription est Confirmée")
    # admin_message_raw is already fully rendered — get_email_context() renders it through
    # utils_email_text's sandboxed renderer, against base_context (which already carries
    # user_name/activity_name and, for payment-first, needs_signup_code/signup_code/
    # requested_amount/payment_email). Re-rendering it here through Flask's plain, unsandboxed
    # render_template_string() was a second-order SSTI: signup.user.name comes straight from
    # the public signup form with no filtering, so a name like "{{ ''.__class__.__mro__... }}"
    # would survive the first (safe) render as literal output text, then get executed as real
    # template *source* by this second pass. Do not reintroduce a second render here.
    admin_message = email_context.get('admin_message', '')
    # Which signup template, by workflow type. safe_template() turns this into the file.
    theme = 'signup_payment_first' if is_payment_first else 'signup'

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
        "admin_message": admin_message,
        "logo_url": "/static/minipass_logo.png",
        # CRITICAL: Flag to prevent send_email_async from re-applying get_email_context()
        "_skip_email_context": True
    }
    
    # Add organization variables for footer (from Settings table)
    context['organization_name'] = get_setting('ORG_NAME', 'minipass')
    context['organization_address'] = get_setting('ORG_ADDRESS', '')

    # Phase 3: copy hosted image URLs from email_context (get_email_context already computed them)
    context['hero_image_url'] = email_context.get('hero_image_url', '')
    context['owner_logo_url'] = email_context.get('owner_logo_url')
    context['site_url'] = email_context.get('site_url', '')
    # Without this, photo_band() defaults to treating the hero as a real photo (Jinja's
    # `| default(True)`) even when it's actually the generic mascot icon — same bug the
    # pass-style templates already had fixed via notify_pass_event's base_context.
    context['hero_is_photo'] = email_context.get('hero_is_photo', True)

    # Add payment-first variables if applicable (for signup_payment_first template)
    if is_payment_first:
        context['payment_email'] = base_context['payment_email']
        context['needs_signup_code'] = base_context['needs_signup_code']
        context['signup_code'] = base_context['signup_code']
        context['requested_amount'] = base_context['requested_amount']

    # One send. This used to branch on whether a compiled template existed on disk, and with
    # templates/email_templates/ gone that check would always have failed into a fallback that
    # forgot use_hosted_images=True — which would have re-attached hero and logo as CID parts,
    # the exact thing that got the domain blocked by Gmail in Feb 2026.
    send_email_async(
        app=app,
        user=signup.user,
        activity=activity,
        subject=subject,
        to_email=signup.user.email,
        template_name=theme,
        context=context,
        inline_images={},
        timestamp_override=timestamp,
        use_hosted_images=True
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

    # One path for every activity.
    #
    # There used to be two branches here, chosen by whether the activity had customizations.
    # They existed only to pick between different template files, and both now resolve to
    # email/<type>.html through safe_template(), so the choice no longer means anything.
    #
    # The split was also breaking sends. The customized branch rebuilt pass_data as a plain
    # dict with different key names (user_name / games_remaining / paid_ind), which the
    # pass_block macro cannot read, so every email for an activity with customizations raised
    # UndefinedError inside the send worker thread and was silently never delivered. Since
    # create_activity seeds email_templates on every new activity, that was nearly all of
    # them. Customization is applied by get_email_context() either way.

    # The template decides whether a QR exists at all; the owner's toggle can then switch it
    # off. Never attach a CID part the layout doesn't render - attachment count is what
    # triggered the Feb 2026 Gmail block.
    show_qr_code = template_type not in NO_QR_TEMPLATES
    if show_qr_code and has_custom_template:
        show_qr_code = activity.email_templates[template_type].get('show_qr_code', True)

    # Owner branding: the activity's own logo, then the organization's, then nothing (the
    # layout falls back to the activity name).
    _BASE_URL = get_setting('SITE_URL', '').rstrip('/')
    _activity_logo_path = os.path.join("static/uploads", f"{activity.id}_owner_logo.png") if activity else None
    if _activity_logo_path and os.path.exists(_activity_logo_path):
        _owner_logo_url = f"{_BASE_URL}/static/uploads/{activity.id}_owner_logo.png"
    else:
        _org_logo_filename = get_setting('LOGO_FILENAME', 'logo.png')
        _org_logo_path = os.path.join("static/uploads", _org_logo_filename)
        _owner_logo_url = f"{_BASE_URL}/static/uploads/{_org_logo_filename}" if os.path.exists(_org_logo_path) else None

    base_context = {
        "pass_data": pass_data,
        "activity_name": activity.name if activity else "",
        "show_qr_code": show_qr_code,
        "owner_logo_url": _owner_logo_url,
        # hero_is_photo is computed by get_email_context() below, once, for every caller.
        # The customer has no account, so the passport page is their only durable way back in.
        "pass_url": _get_pass_url(pass_data),
        "uses_scheduling": bool(activity and getattr(activity, "uses_scheduling", False)),
        "booked_slots": _get_booked_slot_labels(pass_data),
        "history_rows": _build_history_rows(
            get_pass_history_data(pass_data.pass_code, fallback_admin_email=admin_email)
        ),
        # send_email()'s background thread runs in its own app/session context. `pass_data` is
        # a live ORM object bound to *this* (the caller's) session, which can be torn down
        # before that thread gets around to it — e.g. a request's session closing once the
        # response is sent, while the email is still being sent in the background. The thread
        # only needs these two scalars for its EmailLog write; extracting them here, in the
        # still-attached calling thread, means it never has to lazy-load through `pass_data`
        # and risk a DetachedInstanceError (which was silently losing the EmailLog row, though
        # not the send itself, for real pass emails).
        "pass_code": pass_data.pass_code,
        "user_name": pass_data.user.name if pass_data.user else None,
    }

    # Applies the activity's customizations and renders the stored intro/conclusion text.
    context = get_email_context(activity, template_type, base_context)
    # Already applied here - stop the send worker from doing it a second time.
    context["_skip_email_context"] = True

    inline_images = {}
    if show_qr_code:
        inline_images["qr_code"] = generate_qr_code_image(pass_data.pass_code, box_size=EMAIL_QR_BOX_SIZE)

    send_email_async(
        app=app,
        user=pass_data.user,
        activity=activity,
        subject=context.get('subject', 'Notification'),
        to_email=pass_data.user.email if pass_data.user else None,
        template_name=template_type,
        context=context,
        timestamp_override=timestamp,
        inline_images=inline_images,
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


def consolidate_admin_message(fields):
    """Collapse the legacy intro_text/custom_message/conclusion_text trio into the single
    admin_message field, in the exact concatenation order the email layout already renders
    them in. Lets activities whose stored `email_templates` JSON predates the single-field
    consolidation keep rendering/editing correctly without a forced migration.
    See migrations/upgrade_production_database.py's task46 for the one-time DB-wide sweep.
    """
    if not fields:
        return ''
    admin_message = fields.get('admin_message')
    if admin_message:
        return admin_message
    parts = [fields.get('intro_text') or '', fields.get('custom_message') or '', fields.get('conclusion_text') or '']
    return ''.join(parts)


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
        'admin_message': 'Thank you for using our service. We appreciate your business!',
        'hero_image': None,
        'cta_text': None,
        'cta_url': None,
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
    legacy_message_keys = ('intro_text', 'custom_message', 'conclusion_text')
    if activity and activity.email_templates:
        template_customizations = activity.email_templates.get(template_type, {})
        for key, value in template_customizations.items():
            # NEVER allow customizations to override email blocks. The legacy trio is folded
            # into admin_message below rather than applied directly.
            if key not in ['owner_html', 'history_html'] and key not in legacy_message_keys:
                if value is not None and value != '':
                    context[key] = value
        # Legacy-shaped stored data (pre single-field consolidation) still needs to produce
        # a message — consolidate_admin_message() also just returns admin_message itself
        # when the data is already in the new shape.
        admin_message_override = consolidate_admin_message(template_customizations)
        if admin_message_override:
            context['admin_message'] = admin_message_override

    # Restore protected blocks to ensure they're never overridden
    context.update(protected_blocks)

    # Add organization_name and payment_email BEFORE Jinja2 rendering
    if 'organization_name' not in context:
        # Get from Settings table (organization table removed)
        context['organization_name'] = get_setting('ORG_NAME', 'minipass')
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

    # Render Jinja2 variables in all text fields (e.g. {{ activity_name }}).
    #
    # This text is editable per activity, so it is rendered through the sandboxed helper in
    # utils_email_text rather than a bare jinja2.Template: an unsandboxed render whose
    # context holds live SQLAlchemy models lets customized text walk __class__/__mro__ into
    # application internals. build_email_text_context() also guarantees the documented
    # variables (payment_email, organization_name, user_name, ...) are always defined, so a
    # missing name can never silently turn an {% if %} clause off.
    from utils_email_text import build_email_text_context, render_email_text

    text_context = build_email_text_context(
        activity=activity,
        pass_data=context.get('pass_data'),
        organization_name=context.get('organization_name'),
        payment_email=context.get('payment_email'),
        pass_url=context.get('pass_url'),
        sessions=context.get('booked_slots'),
        # Everything already assembled here stays available and wins, so existing
        # customizations that reference the live objects keep rendering unchanged.
        extra=context,
    )

    for field in ['subject', 'title', 'admin_message']:
        if field in context and context[field]:
            context[field] = render_email_text(context[field], text_context)

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

    # Whether the hero is a real photo (custom upload or the activity's own image) versus the
    # shipped default/mascot icon — the photo band renders those two very differently. See
    # photo_band()'s docstring in templates/email/components.html for why the default icon
    # needs its own treatment instead of being cropped and scrimmed like a photo. Computed once
    # here for every caller; a caller that already knows better (e.g. an admin previewing a
    # hero file uploaded in this same request) can still pre-set it in base_context.
    if activity and 'hero_is_photo' not in context:
        _, _hero_is_custom, _hero_is_template_default = get_activity_hero_image(activity, template_type)
        context['hero_is_photo'] = _hero_is_custom or not _hero_is_template_default

    if activity and 'owner_logo_url' not in context:
        context['owner_logo_url'] = f"{_BASE_URL}/owner-logo?activity_id={activity.id}"

    return context


def get_template_hero_dimensions(template_type):
    """
    Get the expected dimensions for hero images based on template type.
    Returns (width, height) tuple. All templates use the standard 400x400 square canvas.
    """
    # All templates use a 400x400 square RGBA canvas for consistent display
    # at width="152" height="auto" (2.6x retina oversampling, ~152x152px rendered)
    all_templates = {
        'newPass', 'signup', 'signup_payment_first', 'paymentReceived',
        'latePayment', 'redeemPass', 'survey_invitation', 'welcome', 'renewal'
    }
    if template_type in all_templates:
        return (400, 400)
    return None

def resize_hero_image(image_data, template_type, max_file_size_mb=2):
    """
    Resize uploaded hero image to a standard 400x400 RGBA square canvas.

    Strategy:
    - PNG with alpha channel: scale-to-fit within 400x400, centered, transparent padding
    - JPEG or opaque PNG: center-crop to square, then resize to 400x400 (fills frame)

    Always outputs RGBA PNG (transparent background, no white box in dark mode).

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

        target_size = 400  # Standard 400x400 square canvas

        # Open and validate the image
        try:
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            return None, f"Invalid image file: {str(e)}"

        original_width, original_height = image.size
        print(f"🖼️ Resizing hero image: {original_width}x{original_height} → {target_size}x{target_size} RGBA")

        # Determine if the image has a meaningful alpha channel
        has_alpha = image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info)

        # Create the 400x400 RGBA output canvas (transparent)
        canvas = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))

        if has_alpha:
            # PNG with alpha: scale-to-fit, preserve full artwork, transparent padding
            if image.mode == 'P':
                image = image.convert('RGBA')
            elif image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Scale to fit within 400x400 maintaining aspect ratio
            image.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
            fitted_width, fitted_height = image.size

            # Center on canvas
            offset_x = (target_size - fitted_width) // 2
            offset_y = (target_size - fitted_height) // 2
            canvas.paste(image, (offset_x, offset_y), mask=image)
            print(f"🖼️ Transparent PNG: scale-to-fit → {fitted_width}x{fitted_height}, centered on {target_size}x{target_size} canvas")
        else:
            # JPEG or opaque PNG: center-crop to square, then resize to fill frame
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Center-crop to square
            min_side = min(original_width, original_height)
            left = (original_width - min_side) // 2
            top = (original_height - min_side) // 2
            image = image.crop((left, top, left + min_side, top + min_side))
            print(f"🖼️ Opaque image: center-cropped to {min_side}x{min_side}")

            # Resize to target_size
            image = image.resize((target_size, target_size), Image.Resampling.LANCZOS)
            image = image.convert('RGBA')
            canvas.paste(image, (0, 0))

        # Save to bytes as PNG
        output_buffer = io.BytesIO()
        canvas.save(output_buffer, format='PNG', optimize=True)
        resized_bytes = output_buffer.getvalue()

        print(f"🖼️ Hero image resized successfully: {len(image_data)} → {len(resized_bytes)} bytes (RGBA)")

        return resized_bytes, f"Image resized to {target_size}x{target_size} RGBA PNG"

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


def send_discord_announcement(subject, message_html, activity_name, webhook_url):
    """Post an announcement to a Discord channel via webhook."""
    import re
    import requests

    # HTML → Discord markdown (basic conversion)
    text = message_html
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'<li>(.*?)</li>', r'• \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)   # strip remaining tags
    text = text.strip()

    payload = {
        "embeds": [{
            "title": subject,
            "description": text,
            "color": 0x206bc4,  # Tabler blue
            "footer": {"text": f"📍 {activity_name}"}
        }]
    }
    try:
        r = requests.post(webhook_url, json=payload, timeout=5)
        return r.status_code == 204
    except Exception as e:
        print(f"[Discord] Webhook error: {e}")
        return False
