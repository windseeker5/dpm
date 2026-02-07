# 📦 Core Python Modules
import os
import io
import re
import uuid
import json
import base64
import hashlib
import bcrypt
import stripe
import qrcode
import secrets
import string
import subprocess
import logging
import traceback
import shutil
import time
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 📁 API Blueprints
from api.backup import backup_api
from api.geocode import geocode_api


# 🌐 Flask Core
from flask import (
    Flask, render_template, render_template_string, request, redirect,
    url_for, session, flash, get_flashed_messages, jsonify, current_app, make_response, Response,
    send_from_directory
)


# 🛠 Flask Extensions
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect



# 🧱 SQLAlchemy Extras
from sqlalchemy import extract, func, case, desc, text

# 📎 File Handling
from werkzeug.utils import secure_filename

# 🧠 Models
from models import db, Admin, Redemption, Setting, EbankPayment, ReminderLog, EmailLog, Income, Expense
from models import Activity, User, Signup, Passport, PassportType, AdminActionLog
from models import SurveyTemplate, Survey, SurveyResponse
from models import QueryLog


# ⚙️ Config
from config import Config

# 🔒 Security Decorators
from decorators import rate_limit, admin_required, log_api_call, cache_response

# 🎯 KPI Card Component

# 🔁 Background Jobs
from apscheduler.schedulers.background import BackgroundScheduler

# 🧰 App Utilities
from utils import (
    send_email_async,
    get_setting,
    generate_qr_code_image,
    get_pass_history_data,
    get_all_activity_logs,
    match_gmail_payments_to_passes,
    utc_to_local,
    send_unpaid_reminders,
    get_kpi_data,
    notify_pass_event,
    notify_signup_event,
    generate_pass_code,
    generate_survey_token,
    generate_response_token,
    HERO_CID_MAP  # Shared constant for email template hero image CIDs
)

# 🧠 Data Tools
from collections import defaultdict

# ✅ Old chatbot imports removed - using new chatbot_v2 blueprint instead

# ==========================================
# HARDCODED DEFAULTS FOR REMOVED UI FIELDS
# ==========================================
# These fields were removed from the UI on 2025-01-24 but need backward compatibility
REMOVED_FIELD_DEFAULTS = {
    'gmail_label_folder_processed': 'PaymentProcessed',
    'default_pass_amount': 50,
    'default_session_qt': 4,
    'email_info_text': '',
    'email_footer_text': '',
    'activity_tags': []
}




db_path = os.path.join("instance", "minipass.db")
print(f"Using database → {db_path}")



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


app.config.from_object(Config)

# Set after Config loading to ensure these take precedence
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'activity_images')

# ✅ Initialize database
db.init_app(app)

# 🔒 Enable foreign key constraints in SQLite
@app.before_request
def enable_foreign_keys():
    """Enable foreign key constraints for SQLite on every request"""
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        db.session.execute(text('PRAGMA foreign_keys = ON'))

# 📁 Register API blueprints
app.register_blueprint(backup_api)
app.register_blueprint(geocode_api)




migrate = Migrate(app, db)


#if not os.path.exists(db_path):
#    print(f"{db_path} is missing!")
#    exit(1)


print(f"📂 Connected DB path: {app.config['SQLALCHEMY_DATABASE_URI']}")


UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Set up logging
logger = logging.getLogger(__name__)

csrf = CSRFProtect(app)
# CRITICAL: Load SECRET_KEY from environment variable for security
# Fallback generates new key on each restart (sessions will be invalidated)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())

app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour

# 🤖 Register Chatbot Blueprint - Using correct template with Gemini
try:
    from chatbot_v2.routes_simple import chatbot_bp
    app.register_blueprint(chatbot_bp)
    print("Gemini chatbot (correct template) registered successfully")
    
    # Register Settings API Blueprint
    from api.settings import settings_api
    app.register_blueprint(settings_api)
    print("Settings API registered successfully")
    
    
    # List routes to verify
    for rule in app.url_map.iter_rules():
        if 'chatbot' in rule.rule:
            print(f"  🗗 {rule.rule} -> {rule.endpoint}")
    
    # Exempt chatbot API from CSRF for testing
    csrf.exempt(chatbot_bp)
    print("Chatbot API exempted from CSRF")

    # Exempt geocode API from CSRF (for AJAX calls)
    csrf.exempt(geocode_api)
    print("Geocode API exempted from CSRF")
except Exception as e:
    print(f"Simple Chatbot registration failed: {e}")
    import traceback
    traceback.print_exc()

@app.template_filter("hashlib_md5")
def hashlib_md5(s):
    return hashlib.md5(s.encode()).hexdigest()





# ✅ Load settings only if the database is ready
with app.app_context():
    app.config["MAIL_SERVER"] = Config.get_setting(app, "MAIL_SERVER", "smtp.gmail.com")
    #app.config["MAIL_PORT"] = int(Config.get_setting(app, "MAIL_PORT", 587))
    app.config["MAIL_PORT"] = int(Config.get_setting(app, "MAIL_PORT", "587") or 587)
    app.config["MAIL_USE_TLS"] = Config.get_setting(app, "MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = Config.get_setting(app, "MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = Config.get_setting(app, "MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = Config.get_setting(app, "MAIL_DEFAULT_SENDER", "")





# ================================
# 💰 SUBSCRIPTION TIER MANAGEMENT
# ================================

def get_subscription_tier():
    """Get current subscription tier from database Setting table.
    Returns: 1 (Starter), 2 (Professional), or 3 (Enterprise)
    Beta testers (no tier set) get Enterprise (3) features.
    """
    from utils import get_setting
    tier = get_setting('MINIPASS_TIER', '')

    # Beta testers have empty/no tier - give them Enterprise features
    if not tier or tier.strip() == '':
        return 3  # Enterprise tier for beta testers

    try:
        return int(tier)
    except (ValueError, TypeError):
        return 3  # Default to Enterprise for invalid values

def get_activity_limit():
    """Get maximum active activities allowed for current subscription tier."""
    tier_limits = {
        1: 1,    # Starter: $10/month
        2: 15,   # Professional: $25/month
        3: 100   # Enterprise: $60/month
    }
    return tier_limits.get(get_subscription_tier(), 1)

def get_tier_info():
    """Get complete tier information for current subscription."""
    tier = get_subscription_tier()
    tier_data = {
        1: {"name": "Starter", "price": "$10/month", "activities": 1},
        2: {"name": "Professional", "price": "$25/month", "activities": 15},
        3: {"name": "Enterprise", "price": "$60/month", "activities": 100}
    }
    return tier_data.get(tier, tier_data[1])

def count_active_activities():
    """Count currently active (non-archived) activities."""
    return Activity.query.filter_by(status='active').count()

def check_activity_limit(exclude_activity_id=None):
    """Check if user can create/activate more activities.

    Args:
        exclude_activity_id: Optional activity ID to exclude from count (for edit scenarios)

    Returns: (bool, error_message or None)
    """
    # Count active activities, excluding the one being edited if specified
    if exclude_activity_id:
        current = Activity.query.filter(
            Activity.status == 'active',
            Activity.id != exclude_activity_id
        ).count()
    else:
        current = count_active_activities()

    limit = get_activity_limit()
    tier = get_subscription_tier()

    if current >= limit:
        tier_info = get_tier_info()

        # Build error message
        msg = f"You've reached your {tier_info['name']} plan limit of {limit} active "
        msg += f"{'activity' if limit == 1 else 'activities'}. "

        # Suggest upgrade if not on highest tier
        if tier < 3:
            next_tier_data = {
                2: {"name": "Professional", "price": "$25/month", "activities": 15},
                3: {"name": "Enterprise", "price": "$60/month", "activities": 100}
            }
            next_tier = next_tier_data[tier + 1]
            msg += f"Upgrade to {next_tier['name']} ({next_tier['price']}) "
            msg += f"for {next_tier['activities']} active activities! "
            msg += 'Contact support to upgrade your plan.'

        return False, msg

    return True, None

def get_activity_usage_display():
    """Get formatted activity usage for display in UI.
    Returns: dict with usage info
    """
    current = count_active_activities()
    limit = get_activity_limit()
    return {
        'current': current,
        'limit': limit,
        'tier_info': get_tier_info(),
        'percentage': int((current / limit) * 100) if limit > 0 else 0
    }

def is_over_activity_limit():
    """Check if user has MORE active activities than their tier allows.
    Returns: (bool, excess_count, message)
    """
    current = count_active_activities()
    limit = get_activity_limit()

    if current > limit:
        excess = current - limit
        tier_info = get_tier_info()
        msg = f"You have {current} active {'activities' if current > 1 else 'activity'} but your {tier_info['name']} plan allows {limit}. "
        msg += f"Please archive {excess} {'activities' if excess > 1 else 'activity'} to continue or upgrade your plan."
        return True, excess, msg

    return False, 0, None

def get_subscription_metadata():
    """Read subscription info from database Setting table.

    Returns:
        dict: Subscription metadata including:
            - subscription_id: Stripe subscription ID (if exists)
            - customer_id: Stripe customer ID (if exists)
            - billing_frequency: 'monthly' or 'annual'
            - renewal_date: Formatted date string (YYYY-MM-DD)
            - payment_amount: Amount in dollars (converted from cents)
            - is_paid_subscriber: Boolean indicating if has subscription
            - is_beta_tester: Boolean indicating if this is a beta tester
            - tier: Tier number (for beta testers)
            - tier_name, tier_display: Tier information (for beta testers)
    """
    from utils import get_setting

    # Check if this is a beta tester (no Stripe subscription)
    stripe_sub_id = get_setting('STRIPE_SUBSCRIPTION_ID', '')
    tier_value = get_setting('MINIPASS_TIER', '')

    if not stripe_sub_id or not tier_value:
        # Beta tester - show appreciation message
        return {
            'is_beta_tester': True,
            'tier': 3,  # Give Enterprise features
            'tier_name': 'Beta Tester',
            'tier_display': 'Beta Tester - Thank You!',
            'tier_price': 'Complimentary',
            'tier_activities': 100,  # Unlimited
            'activity_count': get_activity_count(),
            'activity_usage_display': 'Unlimited',
            'next_billing_date': None,
            'formatted_next_billing': 'N/A',
            'payment_amount': None,
            'formatted_payment_amount': 'N/A',
            'subscription_id': '',
            'customer_id': '',
            'billing_frequency': '',
            'is_paid_subscriber': False,
            'renewal_date': None
        }

    # Regular paid subscriber - read from database
    # Format renewal date (remove time portion)
    renewal_date_raw = get_setting('SUBSCRIPTION_RENEWAL_DATE')
    renewal_date_formatted = None
    if renewal_date_raw:
        try:
            # Parse ISO datetime and extract just the date
            from datetime import datetime
            dt = datetime.fromisoformat(renewal_date_raw.replace('Z', '+00:00'))
            renewal_date_formatted = dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            renewal_date_formatted = renewal_date_raw  # Fallback to raw if parsing fails

    # Convert payment amount from cents to dollars
    payment_amount_raw = get_setting('PAYMENT_AMOUNT')
    payment_amount_formatted = None
    if payment_amount_raw:
        try:
            amount_cents = int(payment_amount_raw)
            payment_amount_formatted = f"{amount_cents / 100:.2f}"
        except (ValueError, TypeError):
            payment_amount_formatted = payment_amount_raw  # Fallback to raw if conversion fails

    return {
        'is_beta_tester': False,
        'subscription_id': stripe_sub_id,
        'customer_id': get_setting('STRIPE_CUSTOMER_ID'),
        'billing_frequency': get_setting('BILLING_FREQUENCY', 'monthly'),
        'renewal_date': renewal_date_formatted,
        'payment_amount': payment_amount_formatted,
        'is_paid_subscriber': bool(stripe_sub_id)
    }

def cancel_subscription(subscription_id):
    """Cancel Stripe subscription at period end.

    Args:
        subscription_id: Stripe subscription ID

    Returns:
        tuple: (success: bool, message: str)
    """
    logger.info(f"[CANCEL_SUB] Starting cancellation for: {subscription_id}")

    try:
        # Get Stripe API key from environment
        api_key = os.getenv('STRIPE_SECRET_KEY')
        logger.info(f"[CANCEL_SUB] API key loaded: {bool(api_key)}")

        if not api_key:
            logger.error("[CANCEL_SUB] STRIPE_SECRET_KEY not found")
            return False, "Stripe API key not configured"

        # Set Stripe API key
        stripe.api_key = api_key
        logger.info(f"[CANCEL_SUB] Calling Stripe API")

        # Cancel subscription at period end
        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )

        logger.info(f"[CANCEL_SUB] SUCCESS - Status: {updated_subscription.status}, cancel_at_period_end: {updated_subscription.cancel_at_period_end}")
        return True, "Auto-renewal cancelled. You'll have access until your current billing period ends."

    except stripe.error.InvalidRequestError as e:
        logger.error(f"[CANCEL_SUB] Invalid request: {e}")
        return False, f"Error: {str(e)}"
    except stripe.error.AuthenticationError as e:
        logger.error(f"[CANCEL_SUB] Auth failed: {e}")
        return False, "Stripe authentication failed"
    except stripe.error.StripeError as e:
        logger.error(f"[CANCEL_SUB] Stripe error: {e}")
        return False, f"Stripe error: {str(e)}"
    except Exception as e:
        logger.error(f"[CANCEL_SUB] Unexpected error: {type(e).__name__}: {e}", exc_info=True)
        return False, f"Error: {str(e)}"


def get_subscription_details():
    """Fetch live subscription details from Stripe API.

    Returns:
        dict: Subscription details including cancel_at_period_end status
    """
    from utils import get_setting
    subscription_id = get_setting('STRIPE_SUBSCRIPTION_ID')

    if not subscription_id:
        return None

    try:
        api_key = os.getenv('STRIPE_SECRET_KEY')
        if not api_key:
            logger.error("[GET_SUB_DETAILS] No Stripe API key")
            return None

        stripe.api_key = api_key
        sub = stripe.Subscription.retrieve(subscription_id)

        return {
            'id': sub.id,
            'status': sub.status,
            'cancel_at_period_end': getattr(sub, 'cancel_at_period_end', False)
        }
    except Exception as e:
        logger.error(f"[GET_SUB_DETAILS] Error: {e}")
        return None


##
##  All the Scheduler JOB 🟢
##

# Global scheduler instance
scheduler = None

def init_scheduler(app):
    """Initialize the scheduler - called once per application instance"""
    global scheduler
    
    if scheduler is not None:
        return  # Already initialized
    
    import fcntl
    import os
    
    # Use file locking to ensure only one scheduler runs across all Gunicorn workers
    lock_file_path = "/tmp/minipass_scheduler.lock"
    
    try:
        # Try to acquire exclusive lock
        lock_file = open(lock_file_path, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # If we get here, we have the lock and should start the scheduler
        from utils import get_setting, send_unpaid_reminders, match_gmail_payments_to_passes
        from sqlalchemy.exc import OperationalError
        
        scheduler = BackgroundScheduler()
        
        with app.app_context():
            try:
                # Payment bot setup - ALWAYS register job, check setting at runtime
                def run_payment_bot():
                    """Payment bot job that checks setting at runtime (no restart needed to enable/disable)"""
                    with app.app_context():
                        # Check setting at runtime - this allows dynamic enable/disable without restart
                        if get_setting("ENABLE_EMAIL_PAYMENT_BOT", "False") != "True":
                            print("⚪ Payment bot scheduled run: DISABLED (skipping)")
                            return

                        print("🟢 Payment bot scheduled run: ENABLED (checking emails...)")
                        try:
                            match_gmail_payments_to_passes()
                            # Auto-cleanup duplicates after processing
                            from utils import cleanup_duplicate_payment_logs_auto
                            cleanup_duplicate_payment_logs_auto()
                        except Exception as e:
                            print(f"Payment bot error: {e}")

                # Always register the job - it will check the setting each time it runs
                scheduler.add_job(run_payment_bot, trigger="interval", minutes=30, id="email_payment_bot")
                current_setting = get_setting("ENABLE_EMAIL_PAYMENT_BOT", "False")
                print(f"📅 Email Payment Bot scheduler registered (currently {'ENABLED' if current_setting == 'True' else 'DISABLED'}, checks setting each run)")

                # Unpaid reminders setup
                scheduler.add_job(func=lambda: send_unpaid_reminders(app), trigger="interval", days=1, id="unpaid_reminders")
                
                # Start the scheduler
                scheduler.start()
                print("Scheduler initialized and started successfully (master worker).")
                
            except OperationalError as e:
                print("DB not ready yet (probably during initial setup), skipping scheduler setup.")
            except Exception as e:
                print(f"Error initializing scheduler: {e}")
    
    except (IOError, OSError):
        # Another worker already has the lock
        print("📋 Scheduler already running in another worker process (skipping duplicate).")
        return

# Initialize scheduler when app starts (Gunicorn-compatible)
def initialize_background_tasks():
    init_scheduler(app)





def get_git_branch():
    """Get current git branch name"""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        branch = result.stdout.strip()
        return branch if branch else 'main'
    except Exception:
        return 'main'

@app.context_processor
def inject_globals_and_csrf():
    from flask_wtf.csrf import generate_csrf
    from flask import has_request_context

    # Calculate pending signups count for sidebar badge
    pending_signups_count = 0
    active_passport_count = 0
    unmatched_payment_count = 0
    current_admin = None

    try:
        if has_request_context() and "admin" in session:  # Only calculate if admin is logged in
            pending_signups_count = Signup.query.filter_by(status='pending').count()
            # Calculate active passports (uses_remaining > 0 OR unpaid) - matches Active filter logic
            active_passport_count = Passport.query.filter(
                db.or_(
                    Passport.uses_remaining > 0,
                    Passport.paid == False
                )
            ).count()
            # Calculate unmatched payments (deduplicated count of NO_MATCH)
            unmatched_payment_count = db.session.query(EbankPayment.id).filter(
                EbankPayment.result == 'NO_MATCH',
                EbankPayment.id.in_(
                    db.session.query(db.func.max(EbankPayment.id))
                    .group_by(EbankPayment.bank_info_name, EbankPayment.bank_info_amt, EbankPayment.from_email)
                )
            ).count()
            # Get current admin info for personalization
            current_admin = Admin.query.filter_by(email=session.get("admin")).first()
    except Exception:
        # If there's any database error, default to 0
        pending_signups_count = 0
        active_passport_count = 0
        unmatched_payment_count = 0
        current_admin = None

    # Get subscription tier info for templates
    subscription_info = None
    if has_request_context() and "admin" in session:
        try:
            subscription_info = get_activity_usage_display()
        except Exception:
            subscription_info = None

    # Get payment email (prefer DISPLAY_PAYMENT_EMAIL, fall back to MAIL_USERNAME)
    display_email = get_setting("DISPLAY_PAYMENT_EMAIL")
    payment_email = display_email if display_email else get_setting("MAIL_USERNAME", "")

    from utils import get_placeholder_css, get_placeholder_letter, get_placeholder_color

    return {
        'now': datetime.now(timezone.utc),
        'ORG_NAME': get_setting("ORG_NAME", "Ligue hockey Gagnon Image"),
        'git_branch': get_git_branch(),
        'csrf_token': generate_csrf,  # returns the raw CSRF token
        'pending_signups_count': pending_signups_count,
        'active_passport_count': active_passport_count,
        'unmatched_payment_count': unmatched_payment_count,
        'current_admin': current_admin,  # Add current admin for template personalization
        'subscription': subscription_info,  # Subscription tier info
        'payment_email': payment_email,  # For displaying payment instructions (uses display email if set)
        'placeholder_css': get_placeholder_css,
        'placeholder_letter': get_placeholder_letter,
        'placeholder_color': get_placeholder_color,
    }


@app.template_filter('encode_md5')
def encode_md5(s):
    if not s:
        return ''
    return hashlib.md5(s.strip().lower().encode('utf-8')).hexdigest()



@app.template_filter("datetimeformat")
def datetimeformat(value, format="%Y-%m-%d %H:%M"):
    return value.strftime(format) if value else ""



@app.before_request
def check_first_run():
    if request.endpoint != 'setup' and not Admin.query.first():
        return redirect(url_for('setup'))



@app.template_filter("trim_email")
def trim_email(email):
    if not email:
        return "-"
    return email.split("@")[0]





##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##
##    TESTING ROUTES
##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##

  


@app.route("/retry-failed-emails")
def retry_failed_emails():
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import EmailLog, Passport
    from utils import send_email_async
    from datetime import datetime

    failed_logs = EmailLog.query.filter_by(result="FAILED").all()
    retried = 0

    # 🔁 Replace with your email for testing
    override_email = "kdresdell@gmail.com"
    #testing_mode = True
    testing_mode = False

    for log in failed_logs:
        passport_obj = Passport.query.filter_by(pass_code=log.pass_code).first()
        if not passport_obj:
            continue  # Skip if no matching passport

        try:
            context = json.loads(log.context_json)
        except:
            continue

        send_email_async(
            current_app._get_current_object(),
            user_email=override_email if testing_mode else log.to_email,
            subject=f"[TEST] {log.subject}" if testing_mode else log.subject,
            user_name=context.get("user_name", "User"),
            pass_code=log.pass_code,
            created_date=context.get("created_date", datetime.now().strftime("%Y-%m-%d")),
            remaining_games=context.get("remaining_games", 0),
            special_message=context.get("special_message", None),
            admin_email=session.get("admin")
        )

        retried += 1

    flash(f"Retried {retried} failed email(s) — sent to {override_email}.", "info")
    return redirect(url_for("dashboard"))






##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##
##    EXTERNAL API TESTING ONLY
##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##



# 🔵 Unsplash Search API

# Unsplash API configuration
# Note: This is a demo/test key that may be expired. Replace with a valid Unsplash API key.
UNSPLASH_ACCESS_KEY = os.environ.get('UNSPLASH_ACCESS_KEY')

@app.route('/unsplash-search')
def unsplash_search():
    """Search for images on Unsplash"""
    import requests
    import uuid
    
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return jsonify([]), 400
    
    try:
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "page": page,
            "per_page": 9,  # 3x3 grid
            "orientation": "landscape"
        }
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for photo in data.get('results', []):
                results.append({
                    'id': photo['id'],
                    'thumb': photo['urls']['small'],
                    'full': photo['urls']['full'],
                    'description': photo.get('description', photo.get('alt_description', 'Image'))
                })
            
            return jsonify(results)
        elif response.status_code == 401:
            print(f"Unsplash API authentication error: {response.text}")
            return jsonify({
                'error': 'Unsplash API key is invalid or expired. Please contact administrator to configure a valid API key.',
                'code': 'AUTH_ERROR',
                'details': 'The Unsplash API key needs to be updated in the application configuration.'
            }), 401
        else:
            print(f"Unsplash API error: {response.status_code} - {response.text}")
            return jsonify({
                'error': f'Unsplash API returned error {response.status_code}',
                'code': 'API_ERROR'
            }), response.status_code
            
    except Exception as e:
        print(f"Unsplash search error: {e}")
        return jsonify({
            'error': 'Image search service is temporarily unavailable',
            'code': 'SERVICE_ERROR',
            'details': 'Please try again later or contact administrator if the problem persists.'
        }), 500

@app.route('/download-unsplash-image')
def download_unsplash_image():
    """Download an image from Unsplash and save it locally"""
    import requests
    import uuid
    import os
    from PIL import Image
    
    image_url = request.args.get('url')
    
    if not image_url:
        return jsonify({'success': False, 'error': 'No image URL provided'}), 400
    
    try:
        # Download the image
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            # Generate unique filename
            filename = f"unsplash_{uuid.uuid4().hex[:8]}.jpg"
            
            # Ensure upload directory exists
            upload_dir = os.path.join(app.static_folder, 'uploads', 'activity_images')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            
            # Save and optimize the image
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Optimize image size
            try:
                with Image.open(file_path) as img:
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # Resize if too large
                    max_size = (1200, 800)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Save with optimization
                    img.save(file_path, 'JPEG', quality=85, optimize=True)
            except Exception as img_error:
                print(f"Image optimization error: {img_error}")
                # Continue with original file if optimization fails
            
            return jsonify({
                'success': True,
                'filename': filename,
                'path': f'/static/uploads/activity_images/{filename}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to download image'}), 500
            
    except Exception as e:
        print(f"Image download error: {e}")
        return jsonify({'success': False, 'error': 'Download failed'}), 500


##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##
##    Regular ROUTES
##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##



@app.route("/")
def home():
    return dashboard()


@app.route("/health")
def health_check():
    """Health check endpoint with version tracking for cache detection"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': 'unknown',
        'git_commit': 'unknown',
        'database': 'unknown'
    }
    
    # Get git version
    try:
        git_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], 
            stderr=subprocess.DEVNULL
        ).decode('ascii').strip()[:8]
        health_status['version'] = git_hash
        health_status['git_commit'] = git_hash
    except:
        pass
    
    # Check database connection
    try:
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        health_status['database'] = 'connected'
    except Exception as e:
        health_status['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory('assets', filename)


@app.route("/style-guide")
def style_guide():
    if "admin" not in session:
        return redirect(url_for("login"))
    return render_template("style_guide.html")

@app.route("/components")
def components():
    if "admin" not in session:
        return redirect(url_for("login"))
    return render_template("components.html")







@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    # CHECK IF USER IS OVER THEIR TIER LIMIT
    is_over, excess, message = is_over_activity_limit()
    if is_over:
        return redirect(url_for("tier_limit_exceeded"))

    from utils import get_kpi_data, get_all_activity_logs
    from models import Activity, Signup, Passport, db
    from sqlalchemy.sql import func
    from datetime import datetime
    from kpi_renderer import render_revenue_card, render_active_users_card, render_passports_created_card, render_passports_unpaid_card, render_passports_redeemed_card
    import re

    # Detect mobile user agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = bool(re.search(r'mobile|android|iphone|ipad', user_agent)) or request.args.get('mobile') == '1'
    
    # Use new simplified KPI data function
    kpi_data = get_kpi_data()

    # Always generate fiscal year data for mobile view (CSS d-md-none handles visibility)
    mobile_kpi_data = get_kpi_data(activity_id=None, period='fy')
    activities = db.session.query(Activity).filter_by(status='active').all()
    activity_cards = []

    for a in activities:
        # Signups
        all_signups = Signup.query.filter_by(activity_id=a.id).all()
        pending_signups = [s for s in all_signups if s.status == 'pending']

        # Passports
        all_passports = Passport.query.filter_by(activity_id=a.id).all()
        paid_passports = [p for p in all_passports if p.paid]
        unpaid_passports = [p for p in all_passports if not p.paid]
        active_passports = [p for p in all_passports if p.uses_remaining > 0]

        # Revenue
        paid_amount = round(sum(p.sold_amt for p in paid_passports), 2)
        unpaid_amount = round(sum(p.sold_amt for p in unpaid_passports), 2)

        # Optional: Days left
        if a.end_date:
            days_left = max((a.end_date - datetime.now()).days, 0)
        else:
            days_left = "N/A"

        # Get passport type information for this activity
        passport_types = PassportType.query.filter_by(activity_id=a.id).all()
        total_sessions = sum(pt.sessions_included or 0 for pt in passport_types) if passport_types else 0

        activity_cards.append({
            "id": a.id,
            "name": a.name,
            "passport_types_count": len(passport_types),
            "total_sessions": total_sessions,
            "signups": len(all_signups),
            "pending_signups": len(pending_signups),
            "passports": len(all_passports),
            "active_passports": len(active_passports),
            "unpaid_passports": len(unpaid_passports),
            "paid_passports": len(paid_passports),
            "paid_amount": paid_amount,
            "unpaid_amount": unpaid_amount,
            "goal_revenue": a.goal_revenue or 0.0,
            "image_filename": a.image_filename,
            "days_left": days_left
        })

    # ✅ Calculate global passport statistics
    all_passports = Passport.query.all()
    passport_stats = {
        'total_passports': len(all_passports),
        'paid_passports': len([p for p in all_passports if p.paid]),
        'unpaid_passports': len([p for p in all_passports if not p.paid]),
        'active_passports': len([p for p in all_passports if p.uses_remaining > 0]),
        'total_revenue': sum(p.sold_amt for p in all_passports if p.paid),
        'pending_revenue': sum(p.sold_amt for p in all_passports if not p.paid),
    }

    # ✅ Calculate global signup statistics
    all_signups = Signup.query.all()
    
    # Calculate cutoff date for recent signups (7 days ago)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    signup_stats = {
        'total_signups': len(all_signups),
        'paid_signups': len([s for s in all_signups if s.paid]),
        'unpaid_signups': len([s for s in all_signups if not s.paid]),
        'pending_signups': len([s for s in all_signups if s.status == 'pending']),
        'approved_signups': len([s for s in all_signups if s.status == 'approved']),
        'recent_signups': len([s for s in all_signups if s.signed_up_at and s.signed_up_at.replace(tzinfo=timezone.utc) >= seven_days_ago]),
    }

    # ✅ Use working helper function - Get all logs for pagination
    all_logs = get_all_activity_logs()

    # ✅ Extract active passport count for the dashboard badge
    active_passport_count = passport_stats['active_passports']

    # Render KPI cards using new templates
    revenue_card = render_revenue_card()
    active_users_card = render_active_users_card()
    passports_created_card = render_passports_created_card()
    passports_unpaid_card = render_passports_unpaid_card()

    return render_template(
        "dashboard.html",
        activities=activity_cards,
        kpi_data=kpi_data,
        mobile_kpi_data=mobile_kpi_data,
        is_mobile=is_mobile,
        passport_stats=passport_stats,
        signup_stats=signup_stats,
        active_passport_count=active_passport_count,
        logs=all_logs,
        revenue_card=revenue_card,
        active_users_card=active_users_card,
        passports_created_card=passports_created_card,
        passports_unpaid_card=passports_unpaid_card
    )




@app.route("/admin/signup/mark-paid/<int:signup_id>", methods=["POST"])
def mark_signup_paid(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("Signup not found.", "error")
        return redirect(url_for("list_signups"))

    signup.paid = True
    signup.paid_at = datetime.now(timezone.utc)
    db.session.commit()
    
    # Emit SSE notification for signup payment
    # SSE notifications removed for leaner performance

    flash(f"Marked {signup.user.name}'s signup as paid.", "success")
    return redirect(url_for("list_signups"))





@app.route("/signups")
def list_signups():
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Signup, User, Activity
    
    # Get filter parameters
    q = request.args.get('q', '').strip()
    activity_id = request.args.get('activity_id')
    payment_status = request.args.get('payment_status')
    signup_status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    show_all_param = request.args.get('show_all')

    # Default to pending status when no filters are set (like passport defaults to active)
    if not signup_status and not payment_status and show_all_param != "true":
        signup_status = "pending"
    
    # Build query with eager loading for performance
    query = Signup.query.options(
        db.joinedload(Signup.user),
        db.joinedload(Signup.activity)
    ).order_by(Signup.signed_up_at.desc())
    
    # Apply text search filter
    if q:
        # Escape special characters for LIKE queries to prevent issues
        escaped_q = q.replace('%', '\\%').replace('_', '\\_')
        search_filter = db.or_(
            User.name.ilike(f'%{escaped_q}%', escape='\\'),
            User.email.ilike(f'%{escaped_q}%', escape='\\'),
            Signup.subject.ilike(f'%{escaped_q}%', escape='\\'),
            Signup.description.ilike(f'%{escaped_q}%', escape='\\'),
            Signup.form_data.ilike(f'%{escaped_q}%', escape='\\'),
            Activity.name.ilike(f'%{escaped_q}%', escape='\\')
        )
        query = query.join(User).join(Activity).filter(search_filter)
    else:
        query = query.join(User).join(Activity)
    
    # Apply activity filter
    if activity_id:
        try:
            activity_id = int(activity_id)
            query = query.filter(Signup.activity_id == activity_id)
        except ValueError:
            pass
    
    # Apply payment status filter
    if payment_status == 'paid':
        query = query.filter(Signup.paid == True)
    elif payment_status == 'unpaid':
        query = query.filter(Signup.paid == False)
    
    # Apply signup status filter
    if signup_status:
        query = query.filter(Signup.status == signup_status)
    
    # Apply date range filters
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Signup.signed_up_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(Signup.signed_up_at <= end)
        except ValueError:
            pass
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Items per page - optimized for better UX with less scrolling
    
    # Execute query with pagination
    signups_pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    signups = signups_pagination.items
    
    # Calculate statistics
    all_signups = Signup.query.count()
    paid_signups = Signup.query.filter(Signup.paid == True).count()
    unpaid_signups = Signup.query.filter(Signup.paid == False).count()
    pending_signups = Signup.query.filter(Signup.status == 'pending').count()
    approved_signups = Signup.query.filter(Signup.status == 'approved').count()
    recent_signups = Signup.query.filter(
        Signup.signed_up_at >= datetime.now(timezone.utc) - timedelta(days=7)
    ).count()
    
    statistics = {
        'total': all_signups,
        'paid': paid_signups,
        'unpaid': unpaid_signups,
        'pending': pending_signups,
        'approved': approved_signups,
        'recent': recent_signups
    }

    # Determine empty state type
    is_first_time_empty = all_signups == 0
    is_zero_results = len(signups) == 0 and not is_first_time_empty

    # Get all activities for filter dropdown
    activities = Activity.query.order_by(Activity.name).all()
    
    # Get unique statuses for filter dropdown
    statuses = db.session.query(Signup.status.distinct()).filter(Signup.status.isnot(None)).all()
    statuses = [status[0] for status in statuses]
    
    # Get all passport types for display
    passport_types = PassportType.query.all()
    
    return render_template('signups.html',
                         signups=signups,
                         pagination=signups_pagination,
                         activities=activities,
                         statuses=statuses,
                         passport_types=passport_types,
                         statistics=statistics,
                         is_first_time_empty=is_first_time_empty,
                         is_zero_results=is_zero_results,
                         current_filters={
                             'q': q,
                             'activity_id': activity_id,
                             'status': signup_status,
                             'start_date': start_date,
                             'end_date': end_date,
                             'show_all': show_all_param == "true"
                         })


@app.route("/signups/bulk-action", methods=["POST"])
def bulk_signup_action():
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Signup, User, Activity
    
    action = request.form.get('action')
    selected_ids = request.form.getlist('selected_signups')
    
    if not selected_ids:
        flash("No signups selected.", "error")
        return redirect(url_for("list_signups"))
    
    try:
        selected_ids = [int(id) for id in selected_ids]
        signups = Signup.query.filter(Signup.id.in_(selected_ids)).all()
        
        if not signups:
            flash("No valid signups found.", "error")
            return redirect(url_for("list_signups"))
        
        admin_email = session.get("admin", "unknown")
        
        if action == 'mark_paid':
            count = 0
            paid_signups = []  # Track signups for notifications
            for signup in signups:
                if not signup.paid:
                    signup.paid = True
                    signup.paid_at = datetime.now(timezone.utc)
                    paid_signups.append(signup)
                    count += 1
            
            db.session.commit()
            
            # SSE notifications removed for leaner performance
            
            # Log admin action
            db.session.add(AdminActionLog(
                admin_email=admin_email,
                action=f"Marked {count} signups as paid (bulk action)"
            ))
            db.session.commit()
            
            flash(f"{count} signups marked as paid.", "success")
            
        elif action == 'send_reminders':
            count = 0
            for signup in signups:
                if not signup.paid:
                    try:
                        # Send payment reminder email
                        notify_signup_event(
                            app=current_app._get_current_object(),
                            event_type="payment_reminder",
                            signup_data=signup,
                            admin_email=admin_email,
                            timestamp=datetime.now(timezone.utc)
                        )
                        count += 1
                    except Exception as e:
                        print(f"Failed to send reminder for signup {signup.id}: {e}")
            
            # Log admin action
            db.session.add(AdminActionLog(
                admin_email=admin_email,
                action=f"Sent payment reminders to {count} unpaid signups (bulk action)"
            ))
            db.session.commit()
            
            flash(f"Payment reminders sent to {count} signups.", "success")
            
        elif action == 'approve':
            count = 0
            for signup in signups:
                if signup.status == 'pending':
                    signup.status = 'approved'
                    count += 1
            
            db.session.commit()
            
            # Log admin action
            db.session.add(AdminActionLog(
                admin_email=admin_email,
                action=f"Approved {count} signups (bulk action)"
            ))
            db.session.commit()
            
            flash(f"{count} signups approved.", "success")
            
        elif action == 'delete':
            count = len(signups)
            signup_info = [f"{s.user.name} - {s.activity.name}" for s in signups]

            for signup in signups:
                db.session.delete(signup)

            db.session.commit()

            # Log admin action as "Signup Rejected" for activity log filter
            details = ', '.join(signup_info[:5])
            if len(signup_info) > 5:
                details += '...'

            db.session.add(AdminActionLog(
                admin_email=admin_email,
                action=f"Rejected signup for {details} by {admin_email}"
            ))
            db.session.commit()

            flash(f"{count} signups deleted.", "success")
            
        else:
            flash("Invalid action.", "error")

    except Exception as e:
        db.session.rollback()
        flash(f"Error processing bulk action: {str(e)}", "error")

    # Check if request came from activity dashboard
    activity_id = request.form.get("activity_id")
    if activity_id:
        return redirect(url_for("activity_dashboard", activity_id=activity_id))

    return redirect(url_for("list_signups"))


@app.route("/signups/export")
def export_signups():
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Signup, User, Activity
    import csv
    from io import StringIO
    
    # Apply the same filters as the main list
    q = request.args.get('q', '').strip()
    activity_id = request.args.get('activity_id')
    payment_status = request.args.get('payment_status')
    signup_status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build the same query as list_signups
    query = Signup.query.options(
        db.joinedload(Signup.user),
        db.joinedload(Signup.activity)
    ).order_by(Signup.signed_up_at.desc())
    
    # Apply filters (same logic as list_signups)
    if q:
        # Escape special characters for LIKE queries to prevent issues
        escaped_q = q.replace('%', '\\%').replace('_', '\\_')
        search_filter = db.or_(
            User.name.ilike(f'%{escaped_q}%', escape='\\'),
            User.email.ilike(f'%{escaped_q}%', escape='\\'),
            Signup.subject.ilike(f'%{escaped_q}%', escape='\\'),
            Signup.description.ilike(f'%{escaped_q}%', escape='\\'),
            Signup.form_data.ilike(f'%{escaped_q}%', escape='\\'),
            Activity.name.ilike(f'%{escaped_q}%', escape='\\')
        )
        query = query.join(User).join(Activity).filter(search_filter)
    else:
        query = query.join(User).join(Activity)
    
    if activity_id:
        try:
            activity_id = int(activity_id)
            query = query.filter(Signup.activity_id == activity_id)
        except ValueError:
            pass
    
    if payment_status == 'paid':
        query = query.filter(Signup.paid == True)
    elif payment_status == 'unpaid':
        query = query.filter(Signup.paid == False)
    
    if signup_status:
        query = query.filter(Signup.status == signup_status)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Signup.signed_up_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(Signup.signed_up_at <= end)
        except ValueError:
            pass
    
    signups = query.all()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        'ID',
        'User Name',
        'User Email',
        'Activity',
        'Subject',
        'Description',
        'Status',
        'Paid',
        'Signup Date',
        'Payment Date',
        'Form Data'
    ])
    
    # Write data rows
    for signup in signups:
        writer.writerow([
            signup.id,
            signup.user.name if signup.user else '',
            signup.user.email if signup.user else '',
            signup.activity.name if signup.activity else '',
            signup.subject or '',
            signup.description or '',
            signup.status or '',
            'Yes' if signup.paid else 'No',
            signup.signed_up_at.strftime('%Y-%m-%d %H:%M') if signup.signed_up_at else '',
            signup.paid_at.strftime('%Y-%m-%d %H:%M') if signup.paid_at else '',
            signup.form_data or ''
        ])
    
    # Log admin action
    admin_email = session.get("admin", "unknown")
    db.session.add(AdminActionLog(
        admin_email=admin_email,
        action=f"Exported {len(signups)} signups to CSV"
    ))
    db.session.commit()
    
    # Create response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'signups_export_{timestamp}.csv'
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response



@app.route("/admin/signup/create-pass/<int:signup_id>")
def create_pass_from_signup(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("Signup not found.", "error")
        return redirect(url_for("list_signups"))

    from models import Passport

    # Check if a passport already exists
    existing_passport = Passport.query.filter_by(user_id=signup.user_id, activity_id=signup.activity_id).first()
    if existing_passport:
        flash("A passport for this user and activity already exists.", "warning")
        return redirect(url_for("list_signups"))

    # Get passport type from signup or fallback to first one for this activity
    passport_type = None
    if signup.passport_type_id:
        passport_type = db.session.get(PassportType, signup.passport_type_id)
    else:
        passport_type = PassportType.query.filter_by(activity_id=signup.activity_id).first()
    
    # Create new passport
    new_passport = Passport(
        pass_code=f"MP{datetime.now().timestamp():.0f}",
        user_id=signup.user_id,
        activity_id=signup.activity_id,
        passport_type_id=passport_type.id if passport_type else None,
        passport_type_name=passport_type.name if passport_type else None,  # Preserve type name
        sold_amt=passport_type.price_per_user if passport_type else 0.0,
        uses_remaining=passport_type.sessions_included if passport_type else 1,
        created_dt=datetime.now(timezone.utc),
        paid=signup.paid,
        notes=f"Created from signup {signup.id}"
    )
    db.session.add(new_passport)
    db.session.commit()

    flash("Passport created from signup!", "success")
    return redirect(url_for("list_signups"))



@app.route("/admin/signup/edit/<int:signup_id>", methods=["GET", "POST"])
def edit_signup(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("Signup not found.", "error")
        return redirect(url_for("list_signups"))

    if request.method == "POST":
        signup.subject = request.form.get("subject", "").strip()
        signup.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("Signup updated.", "success")
        return redirect(url_for("list_signups"))

    return render_template("edit_signup.html", signup=signup)



@app.route("/signup/status/<int:signup_id>", methods=["POST"])
def update_signup_status(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("Signup not found.", "error")
        return redirect(url_for("list_signups"))

    status = request.form.get("status")

    if status in ["rejected", "cancelled"]:
        signup.status = status
        db.session.commit()

        from utils import log_admin_action

        user_name = signup.user.name if signup.user else "-"
        activity_name = signup.activity.name if signup.activity else "-"

        log_admin_action(
            f"Signup ID {signup.id}, {user_name}, for Activity '{activity_name}' was marked as {status}"
        )

        flash(f"Signup marked as {status}.", "success")
    else:
        flash("Invalid status.", "error")

    return redirect(url_for("list_signups"))




@app.route("/signup/approve-create-pass/<int:signup_id>")
def approve_and_create_pass(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("Signup not found.", "error")
        return redirect(url_for("list_signups"))

    from models import Passport, AdminActionLog, Admin
    from utils import notify_pass_event, generate_pass_code
    from datetime import datetime, timezone, timedelta
    import time

    now_utc = datetime.now(timezone.utc)

    # ✅ Step 1: Approve the signup
    signup.status = "approved"
    db.session.commit()

    # ✅ Step 2: Get current Admin info
    current_admin = Admin.query.filter_by(email=session.get("admin")).first()

    # ✅ Step 3: Get passport type and Create Passport
    # Use passport type from signup if available, otherwise get first one for activity
    passport_type = None
    if signup.passport_type_id:
        passport_type = db.session.get(PassportType, signup.passport_type_id)
    else:
        passport_type = PassportType.query.filter_by(activity_id=signup.activity_id).first()
    
    passport = Passport(
        pass_code=generate_pass_code(),
        user_id=signup.user_id,
        activity_id=signup.activity_id,
        passport_type_id=passport_type.id if passport_type else None,
        passport_type_name=passport_type.name if passport_type else None,  # Preserve type name
        sold_amt=passport_type.price_per_user if passport_type else 0.0,
        uses_remaining=passport_type.sessions_included if passport_type else 1,
        created_by=current_admin.id if current_admin else None,
        created_dt=now_utc,
        paid=signup.paid,
        notes=f"Created automatically from signup {signup.id}"
    )
    db.session.add(passport)
    db.session.commit()
    db.session.expire_all()

    # ✅ Step 4: Log admin actions (signup approved + passport created)
    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=f"Signup approved for {signup.user.name} for Activity '{signup.activity.name}' by {session.get('admin', 'unknown')}"
    ))
    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=f"Passport created from signup for {signup.user.name} (Code: {passport.pass_code}) by {session.get('admin', 'unknown')}"
    ))
    db.session.commit()

    # ✅ Step 5: Sleep to ensure clean timestamps
    time.sleep(0.5)

    # ✅ Step 6: Refresh now_utc
    now_utc = datetime.now(timezone.utc)

    # ✅ Step 7: Send confirmation email
    notify_pass_event(
        app=current_app._get_current_object(),
        event_type="pass_created",
        pass_data=passport,
        activity=passport.activity,
        admin_email=session.get("admin"),
        timestamp=now_utc
    )

    flash("Signup approved and passport created! Email sent to user.", "success")
    return redirect(url_for("activity_dashboard", activity_id=signup.activity_id))




@app.route("/create-activity", methods=["GET", "POST"])
def create_activity():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # CHECK TIER LIMIT BEFORE CREATING NEW ACTIVITY
        can_create, error_msg = check_activity_limit()
        if not can_create:
            from markupsafe import Markup
            tier_info = get_tier_info()
            tier = get_subscription_tier()

            # Build flash message with archive option and upgrade link
            flash_msg = f"You've reached your {tier_info['name']} plan limit of {tier_info['activities']} active "
            flash_msg += f"{'activity' if tier_info['activities'] == 1 else 'activities'}. "
            flash_msg += '<a href="/activities" class="alert-link">Archive a current activity</a> to create a new one'

            # Add upgrade option if not on highest tier
            if tier < 3:
                flash_msg += ' or <a href="/current-plan" class="alert-link">Upgrade to '
                next_tier_data = {
                    2: {"name": "Professional", "price": "$25/month"},
                    3: {"name": "Enterprise", "price": "$60/month"}
                }
                next_tier = next_tier_data[tier + 1]
                flash_msg += f'{next_tier["name"]}</a>'

            flash(Markup(flash_msg), 'tier_limit')
            return redirect(url_for("list_activities"))

        from models import Activity, PassportType, AdminActionLog, db
        import os
        import uuid

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")

        start_date = datetime.strptime(start_date_raw, "%Y-%m-%dT%H:%M") if start_date_raw else None
        end_date = datetime.strptime(end_date_raw, "%Y-%m-%dT%H:%M") if end_date_raw else None

        name = request.form.get("name", "").strip()
        activity_type = request.form.get("type", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "active")

        # 📍 Handle location fields (optional)
        location_address_raw = request.form.get("location_address_raw", "").strip()
        location_address_formatted = request.form.get("location_address_formatted", "").strip()
        location_coordinates = request.form.get("location_coordinates", "").strip()

        # 💰 Handle goal revenue (optional)
        goal_revenue_str = request.form.get("goal_revenue", "").strip()
        goal_revenue = float(goal_revenue_str) if goal_revenue_str else 0.0

        # 🖼️ Handle image selection
        uploaded_file = request.files.get('upload_image')
        selected_image_filename = request.form.get("selected_image_filename", "").strip()

        image_filename = None

        if uploaded_file and uploaded_file.filename != '':
            ext = os.path.splitext(uploaded_file.filename)[1].lower()
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if ext in allowed_extensions:
                filename = f"upload_{uuid.uuid4().hex[:10]}{ext}"
                upload_folder = os.path.join("static", "uploads", "activity_images")
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                uploaded_file.save(filepath)
                image_filename = filename
        elif selected_image_filename:
            image_filename = selected_image_filename

        # Get default email templates from central configuration
        from utils_email_defaults import get_default_email_templates
        default_email_templates = get_default_email_templates()

        # Get admin ID from email (session stores email, but FK expects admin.id)
        admin_email = session.get("admin")
        admin = Admin.query.filter_by(email=admin_email).first()
        admin_id = admin.id if admin else None

        # Workflow and quantity limit fields
        workflow_type = request.form.get("workflow_type", "approval_first")
        allow_quantity_selection = "allow_quantity_selection" in request.form
        is_quantity_limited = "is_quantity_limited" in request.form
        max_sessions_str = request.form.get("max_sessions", "").strip()
        max_sessions = int(max_sessions_str) if max_sessions_str else None
        show_remaining_quantity = "show_remaining_quantity" in request.form

        new_activity = Activity(
            name=name,
            type=activity_type,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            created_by=admin_id,
            image_filename=image_filename,
            email_templates=default_email_templates,
            location_address_raw=location_address_raw if location_address_raw else None,
            location_address_formatted=location_address_formatted if location_address_formatted else None,
            location_coordinates=location_coordinates if location_address_formatted else None,
            goal_revenue=goal_revenue,
            offer_passport_renewal=("offer_passport_renewal" in request.form),
            workflow_type=workflow_type,
            allow_quantity_selection=allow_quantity_selection,
            is_quantity_limited=is_quantity_limited,
            max_sessions=max_sessions,
            show_remaining_quantity=show_remaining_quantity
        )

        db.session.add(new_activity)
        db.session.flush()  # Get the activity ID
        
        # Copy default images for the new activity
        try:
            # Define source paths for default images
            default_hero_path = os.path.join("static", "uploads", "defaults", "default_hero.png")

            # Define target paths with activity ID
            activity_hero_path = os.path.join("static", "uploads", f"{new_activity.id}_hero.png")

            # Copy default hero image if it exists
            if os.path.exists(default_hero_path):
                shutil.copy(default_hero_path, activity_hero_path)

            # Update email templates to reference the copied images
            # Note: owner logo is NOT snapshot-copied; emails resolve it from org settings at send time
            updated_templates = new_activity.email_templates.copy()
            for template_type in updated_templates:
                if isinstance(updated_templates[template_type], dict):
                    updated_templates[template_type]['hero_image'] = f"{new_activity.id}_hero.png"
            
            # Update the activity with the modified templates
            new_activity.email_templates = updated_templates
            
        except Exception as e:
            print(f"Warning: Could not copy default images for activity {new_activity.id}: {e}")
            # Continue with activity creation even if image copying fails

        # Handle passport types
        passport_types_data = {}
        for key, value in request.form.items():
            if key.startswith('passport_types['):
                # Parse passport_types[id][field] format
                parts = key.split('[')
                if len(parts) == 3:
                    passport_id = parts[1].rstrip(']')
                    field = parts[2].rstrip(']')
                    
                    if passport_id not in passport_types_data:
                        passport_types_data[passport_id] = {}
                    passport_types_data[passport_id][field] = value

        # Create passport types
        for passport_id, passport_data in passport_types_data.items():
            if passport_data.get('name'):  # Only create if name is provided
                passport_type = PassportType(
                    activity_id=new_activity.id,
                    name=passport_data.get('name', '').strip(),
                    type='permanent',
                    price_per_user=float(passport_data.get('price_per_user', 0.0)),
                    sessions_included=int(passport_data.get('sessions_included', 1)),
                    target_revenue=0.0,
                    payment_instructions='',
                    use_custom_payment_instructions=False,
                    status='active'
                )
                db.session.add(passport_type)

        db.session.commit()

        # Log the action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Activity Created: {new_activity.name} with {len(passport_types_data)} passport types"
        ))
        db.session.commit()

        flash(f"Activity created successfully with {len(passport_types_data)} passport types!", "success")
        return redirect(url_for("dashboard"))

    # ✅ GET request - check tier limit BEFORE showing form
    can_create, error_msg = check_activity_limit()
    if not can_create:
        from markupsafe import Markup
        tier_info = get_tier_info()
        tier = get_subscription_tier()

        flash_msg = f"You've reached your {tier_info['name']} plan limit of {tier_info['activities']} active "
        flash_msg += f"{'activity' if tier_info['activities'] == 1 else 'activities'}. "
        flash_msg += '<a href="/activities" class="alert-link">Archive a current activity</a> to create a new one'

        if tier < 3:
            flash_msg += ' or <a href="/current-plan" class="alert-link">Upgrade to '
            next_tier_data = {
                2: {"name": "Professional", "price": "$25/month"},
                3: {"name": "Enterprise", "price": "$60/month"}
            }
            next_tier = next_tier_data[tier + 1]
            flash_msg += f'{next_tier["name"]}</a>'

        flash(Markup(flash_msg), 'tier_limit')
        return redirect(url_for("list_activities"))

    # If within limit, show the form
    # For new activities, all accordion sections are collapsed by default
    import os
    from utils import get_setting
    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    display_email = get_setting("DISPLAY_PAYMENT_EMAIL", "")
    payment_email = display_email if display_email else get_setting("MAIL_USERNAME", "")

    return render_template("activity_form.html",
                          activity=None,
                          has_workflow_data=False,
                          has_capacity_data=False,
                          has_schedule_data=False,
                          has_advanced_data=False,
                          google_maps_api_key=google_maps_api_key,
                          payment_email=payment_email)


@app.route("/edit-activity/<int:activity_id>", methods=["GET", "POST"])
def edit_activity(activity_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    activity = db.session.get(Activity, activity_id)

    if not activity:
        flash("Activity not found.", "error")
        return redirect(url_for("dashboard"))

    # Check for deletion success/error messages from query parameters
    deleted_name = request.args.get('deleted')
    error_msg = request.args.get('error')
    if deleted_name:
        flash(f"Passport type '{deleted_name}' has been deleted successfully!", "success")
    elif error_msg:
        flash(f"Error deleting passport type: {error_msg}", "error")

    if request.method == "POST":
        import os
        import uuid

        # Capture old status before updating
        old_status = activity.status
        new_status = request.form.get("status", "active")

        # CHECK TIER LIMIT when changing status to 'active'
        if old_status != 'active' and new_status == 'active':
            can_activate, error_msg = check_activity_limit(exclude_activity_id=activity.id)
            if not can_activate:
                flash(error_msg, 'warning')
                return redirect(url_for("edit_activity", activity_id=activity.id))

        activity.name = request.form.get("name", "").strip()
        activity.type = request.form.get("type", "").strip()
        activity.description = request.form.get("description", "").strip()
        activity.status = new_status

        # 📍 Update location fields (optional)
        activity.location_address_raw = request.form.get("location_address_raw", "").strip() or None
        activity.location_address_formatted = request.form.get("location_address_formatted", "").strip() or None
        activity.location_coordinates = request.form.get("location_coordinates", "").strip() or None

        # 💰 Update goal revenue (optional)
        goal_revenue_str = request.form.get("goal_revenue", "").strip()
        activity.goal_revenue = float(goal_revenue_str) if goal_revenue_str else 0.0

        # Update passport renewal setting
        activity.offer_passport_renewal = ("offer_passport_renewal" in request.form)

        # Update workflow and quantity limit fields
        activity.workflow_type = request.form.get("workflow_type", "approval_first")
        activity.allow_quantity_selection = "allow_quantity_selection" in request.form
        activity.is_quantity_limited = "is_quantity_limited" in request.form
        max_sessions_str = request.form.get("max_sessions", "").strip()
        activity.max_sessions = int(max_sessions_str) if max_sessions_str else None
        activity.show_remaining_quantity = "show_remaining_quantity" in request.form

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")

        activity.start_date = datetime.strptime(start_date_raw, "%Y-%m-%dT%H:%M") if start_date_raw else None
        activity.end_date = datetime.strptime(end_date_raw, "%Y-%m-%dT%H:%M") if end_date_raw else None

        uploaded_file = request.files.get('upload_image')
        selected_image_filename = request.form.get("selected_image_filename", "").strip()

        if uploaded_file and uploaded_file.filename != '':
            ext = os.path.splitext(uploaded_file.filename)[1].lower()
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if ext in allowed_extensions:
                filename = f"upload_{uuid.uuid4().hex[:10]}{ext}"
                upload_folder = os.path.join("static", "uploads", "activity_images")
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                uploaded_file.save(filepath)
                activity.image_filename = filename
        elif selected_image_filename:
            activity.image_filename = selected_image_filename

        # Handle passport types - preserve existing ones and update/create as needed
        existing_passport_types = PassportType.query.filter_by(activity_id=activity.id, status='active').all()
        existing_pt_dict = {pt.id: pt for pt in existing_passport_types}

        # Parse new passport types from form
        passport_types_data = {}
        for key, value in request.form.items():
            if key.startswith('passport_types['):
                parts = key.split('[')
                if len(parts) == 3:
                    passport_id = parts[1].rstrip(']')
                    field = parts[2].rstrip(']')
                    
                    if passport_id not in passport_types_data:
                        passport_types_data[passport_id] = {}
                    passport_types_data[passport_id][field] = value

        # Update existing passport types or create new ones
        passport_types_created = 0
        passport_types_updated = 0
        updated_passport_type_ids = set()
        
        for passport_id, passport_data in passport_types_data.items():
            if passport_data.get('name'):  # Only process if name is provided
                try:
                    existing_id = int(passport_id) if passport_id.isdigit() else None
                except (ValueError, TypeError):
                    existing_id = None
                
                if existing_id and existing_id in existing_pt_dict:
                    # Update existing passport type
                    passport_type = existing_pt_dict[existing_id]
                    passport_type.name = passport_data.get('name', '').strip()
                    passport_type.price_per_user = float(passport_data.get('price_per_user', 0.0))
                    passport_type.sessions_included = int(passport_data.get('sessions_included', 1))

                    # Preserve passport type names in existing passports when updating
                    passports_to_update = Passport.query.filter_by(passport_type_id=existing_id).all()
                    for passport in passports_to_update:
                        if not passport.passport_type_name:  # Only update if not already preserved
                            passport.passport_type_name = passport_type.name

                    updated_passport_type_ids.add(existing_id)
                    passport_types_updated += 1
                else:
                    # Create new passport type
                    passport_type = PassportType(
                        activity_id=activity.id,
                        name=passport_data.get('name', '').strip(),
                        type='permanent',
                        price_per_user=float(passport_data.get('price_per_user', 0.0)),
                        sessions_included=int(passport_data.get('sessions_included', 1)),
                        target_revenue=0.0,
                        payment_instructions='',
                        use_custom_payment_instructions=False,
                        status='active'
                    )
                    db.session.add(passport_type)
                    passport_types_created += 1
        
        # Archive passport types that were removed from the form (not deleted, just archived)
        passport_types_archived = 0
        for pt_id, pt in existing_pt_dict.items():
            if pt_id not in updated_passport_type_ids:
                # This passport type was removed from the form - archive it instead of deleting
                pt.status = 'archived'
                pt.archived_at = datetime.now(timezone.utc)
                pt.archived_by = session.get("admin", "system")
                
                # Preserve passport type names in existing passports
                passports_to_preserve = Passport.query.filter_by(passport_type_id=pt_id).all()
                for passport in passports_to_preserve:
                    if not passport.passport_type_name:  # Only update if not already preserved
                        passport.passport_type_name = pt.name
                
                passport_types_archived += 1

        db.session.commit()

        from models import AdminActionLog
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Activity Updated: {activity.name} - Created: {passport_types_created}, Updated: {passport_types_updated}, Archived: {passport_types_archived} passport types"
        ))
        db.session.commit()

        flash(f"Activity updated successfully! Created: {passport_types_created}, Updated: {passport_types_updated}, Archived: {passport_types_archived} passport types.", "success")
        return redirect(url_for("dashboard"))

    # 🧮 Add financial summary data (shown at bottom of form) - use database views for consistency
    from utils import get_financial_data_from_views, get_fiscal_year_range, get_fiscal_year_display, get_setting

    period = request.args.get('period', 'fy')
    start_date, end_date, period_display = None, None, "All Time"

    if period == 'fy':
        fy_start, fy_end = get_fiscal_year_range()
        start_date = fy_start.strftime('%Y-%m-%d')
        end_date = fy_end.strftime('%Y-%m-%d')
        period_display = get_fiscal_year_display()

    financial_data = get_financial_data_from_views(
        start_date=start_date,
        end_date=end_date,
        activity_filter=activity.id
    )

    summary = {
        "passport_income": financial_data['summary']['cash_received'],
        "other_income": 0,  # View combines all income into cash_received
        "total_expenses": financial_data['summary']['cash_paid'],
        "net_income": financial_data['summary']['net_cash_flow']
    }

    # Get passport types for this activity (only active ones)
    passport_types_objects = PassportType.query.filter_by(activity_id=activity.id, status='active').all()

    # Convert to dictionaries for JSON serialization
    passport_types = []
    for pt in passport_types_objects:
        passport_types.append({
            'id': pt.id,
            'name': pt.name,
            'price_per_user': pt.price_per_user,
            'sessions_included': pt.sessions_included
        })
    
    # Smart accordion expansion: detect which sections have data
    has_workflow_data = (
        activity.workflow_type == 'payment_first' or
        activity.offer_passport_renewal
    )
    has_capacity_data = (
        activity.is_quantity_limited or
        activity.allow_quantity_selection or
        activity.max_sessions
    )
    has_schedule_data = (
        activity.start_date or
        activity.end_date or
        activity.location_address_formatted
    )
    has_advanced_data = (
        activity.goal_revenue and activity.goal_revenue > 0
    )

    # Get Google Maps API key for Places Autocomplete
    import os
    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')

    # Get payment email for display
    display_email = get_setting("DISPLAY_PAYMENT_EMAIL", "")
    payment_email = display_email if display_email else get_setting("MAIL_USERNAME", "")

    return render_template("activity_form.html",
                          activity=activity,
                          passport_types=passport_types,
                          summary=summary,
                          current_period=period,
                          period_display=period_display,
                          has_workflow_data=has_workflow_data,
                          has_capacity_data=has_capacity_data,
                          has_schedule_data=has_schedule_data,
                          has_advanced_data=has_advanced_data,
                          google_maps_api_key=google_maps_api_key,
                          payment_email=payment_email)




@app.route("/signup/<int:activity_id>", methods=["GET", "POST"])
def signup(activity_id):
    activity = db.session.get(Activity, activity_id)
    if not activity:
        flash("Activity not found.", "error")
        return redirect(url_for("dashboard"))

    # Get passport type if specified
    passport_type_id = request.args.get('passport_type_id')
    selected_passport_type = None
    if passport_type_id:
        selected_passport_type = db.session.get(PassportType, passport_type_id)

    # Get all passport types for this activity
    passport_types = PassportType.query.filter_by(activity_id=activity.id, status='active').all()

    # ✅ Corrected settings loading
    settings = {s.key: s.value for s in Setting.query.all()}

    # Check capacity for quantity-limited activities
    from utils import get_remaining_capacity
    remaining_capacity = get_remaining_capacity(activity_id)
    is_sold_out = remaining_capacity is not None and remaining_capacity <= 0

    if request.method == "POST":
        # Check capacity again on POST to prevent race conditions
        remaining_capacity = get_remaining_capacity(activity_id)
        requested_sessions = int(request.form.get("requested_sessions", 1))

        if remaining_capacity is not None:
            if remaining_capacity <= 0:
                flash("Sorry, this activity is sold out.", "error")
                return redirect(url_for("signup", activity_id=activity_id))
            if requested_sessions > remaining_capacity:
                flash(f"Only {remaining_capacity} spots remaining. Please reduce your quantity.", "error")
                return redirect(url_for("signup", activity_id=activity_id))

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        selected_passport_type_id = request.form.get("passport_type_id")

        user = User(name=name, email=email, phone_number=phone)
        db.session.add(user)
        db.session.flush()

        # Get the selected passport type
        passport_type = None
        if selected_passport_type_id:
            passport_type = db.session.get(PassportType, selected_passport_type_id)

        # Calculate total amount for payment-first workflow
        unit_price = passport_type.price_per_user if passport_type else 0.0
        requested_amount = unit_price * requested_sessions

        signup_record = Signup(
            user_id=user.id,
            activity_id=activity.id,
            passport_type_id=selected_passport_type_id if selected_passport_type_id else None,
            subject=f"Signup for {activity.name}" + (f" - {passport_type.name}" if passport_type else ""),
            description=request.form.get("notes", "").strip(),
            form_data="",
            requested_sessions=requested_sessions,
            requested_amount=requested_amount
        )
        db.session.add(signup_record)
        db.session.flush()  # Get the ID before commit
        signup_record.signup_code = f"MP-INS-{signup_record.id:07d}"
        db.session.commit()

        from utils import notify_signup_event
        notify_signup_event(app, signup=signup_record, activity=activity)

        # SSE notifications removed for leaner performance

        flash("Signup submitted!", "success")
        return redirect(url_for("signup_thank_you", signup_id=signup_record.id))

    return render_template("signup_form.html", activity=activity, settings=settings,
                         passport_types=passport_types, selected_passport_type=selected_passport_type,
                         remaining_capacity=remaining_capacity, is_sold_out=is_sold_out)


@app.route("/signup/thank-you/<int:signup_id>")
def signup_thank_you(signup_id):
    """Thank you page after successful signup"""
    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("Signup not found.", "error")
        return redirect(url_for("dashboard"))
    
    activity = signup.activity
    settings = {s.key: s.value for s in Setting.query.all()}
    
    return render_template("signup_thank_you.html", 
                          signup=signup, 
                          activity=activity, 
                          settings=settings)



@app.route("/payment-bot-settings", methods=["GET", "POST"])
def payment_bot_settings():
    """Dedicated page for Email Parser Payment Bot settings"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    # Handle test button
    if request.form.get("action") == "test_bot":
        try:
            from utils import match_gmail_payments_to_passes, log_admin_action
            print("🔧 Payment bot manual test triggered!")
            
            log_admin_action(f"Manual payment bot test by {session.get('admin', 'Unknown')}")
            result = match_gmail_payments_to_passes()
            
            if result and isinstance(result, dict):
                matched = result.get('matched', 0)
                no_match = result.get('no_match', 0)
                skipped = result.get('skipped', 0)
                emails_found = result.get('emails_found', 0)

                if matched > 0:
                    flash(f"Test completed! {matched} payment(s) matched to passports!", "success")
                elif no_match > 0:
                    flash(f"Test completed! {no_match} payment(s) need manual review (no matching passport)", "warning")
                elif emails_found > 0 and skipped > 0:
                    flash(f"Test completed! {skipped} payment(s) already processed - no new payments.", "info")
                else:
                    flash("Test completed! No new payments found in inbox.", "info")
            else:
                flash("Test completed! No new payments found.", "info")
                
        except Exception as e:
            print(f"Payment bot test error: {e}")
            flash(f"Test failed: {str(e)}", "error")
        
        return redirect(url_for("payment_bot_settings"))
    
    if request.method == "POST":
        # Save Email Payment Bot settings
        bot_settings = {
            "ENABLE_EMAIL_PAYMENT_BOT": "enable_email_payment_bot" in request.form,
            "BANK_EMAIL_FROM": request.form.get("bank_email_from", "").strip(),
            "BANK_EMAIL_SUBJECT": request.form.get("bank_email_subject", "").strip(),
            "BANK_EMAIL_NAME_CONFIDANCE": request.form.get("bank_email_name_confidance", "85").strip(),
            # OBSOLETE: gmail_label_folder_processed removed from UI on 2025-01-24
            # "GMAIL_LABEL_FOLDER_PROCESSED": request.form.get("gmail_label_folder_processed", "InteractProcessed").strip()
            "GMAIL_LABEL_FOLDER_PROCESSED": REMOVED_FIELD_DEFAULTS['gmail_label_folder_processed']
        }
        
        for key, value in bot_settings.items():
            existing = Setting.query.filter_by(key=key).first()
            if existing:
                existing.value = str(value)
            else:
                db.session.add(Setting(key=key, value=str(value)))
        
        db.session.commit()

        # Log the action
        from utils import log_admin_action
        log_admin_action(f"Email Payment Bot Settings Updated by {session.get('admin', 'Unknown')}")

        # Check if we're enabling the bot - if so, trigger immediate first run (async)
        is_enabling = "enable_email_payment_bot" in request.form

        if is_enabling:
            # Trigger immediate payment bot run in background thread (non-blocking)
            import threading
            from utils import match_gmail_payments_to_passes

            def run_payment_bot_async():
                """Run payment bot in background thread"""
                with app.app_context():
                    try:
                        print("🚀 Payment bot ENABLED - running first check in background...")
                        match_gmail_payments_to_passes()
                        print("Payment bot background check completed!")
                    except Exception as e:
                        print(f"Payment bot background run failed: {e}")

            thread = threading.Thread(target=run_payment_bot_async, daemon=True)
            thread.start()
            print("🔄 Payment bot first check started in background thread")

            flash("Payment Bot enabled! First email check is running now. Subsequent checks every 30 minutes.", "success")
        else:
            flash("Payment Bot disabled. Email checking stopped.", "success")

        return redirect(url_for("payment_bot_settings"))
    
    # GET request - load settings
    settings = {}
    for setting in Setting.query.all():
        settings[setting.key] = setting.value
    
    return render_template("payment_bot_settings.html", settings=settings)


@app.route("/api/payment-bot/test-email", methods=["POST"])
@rate_limit(max_requests=2, window=3600)  # 2 requests per hour
def api_payment_bot_test_email():
    """Send a test payment email (rate-limited and secure)"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    from markupsafe import escape
    from utils import send_email, get_setting
    
    # Get and sanitize inputs (NO custom From address for security)
    sender_name = escape(request.form.get("sender_name", "").strip())[:100]
    amount = request.form.get("amount", "").strip()
    
    # Validate inputs
    if not sender_name:
        return jsonify({"error": "Sender name is required"}), 400
    
    try:
        amount_float = float(amount)
        if amount_float <= 0 or amount_float > 10000:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount (must be between 0 and 10000)"}), 400
    
    # Get payment email address from settings (use MAIL_USERNAME as the payment email)
    payment_email = get_setting("MAIL_USERNAME", None)
    if not payment_email:
        return jsonify({"error": "Payment email not configured. Please set Mail Username in Email Settings."}), 500
    
    # Build test email content
    subject = f"INTERAC e-Transfer: {sender_name} sent you ${amount_float:.2f} (CAD)"
    html_body = f"""
    <html>
    <body>
        <h2>Test Payment Notification</h2>
        <p><strong>Sender:</strong> {sender_name}</p>
        <p><strong>Amount:</strong> ${amount_float:.2f} CAD</p>
        <p><strong>Reference:</strong> TEST-{int(time.time())}</p>
        <hr>
        <p><em>This is a test email sent from Minipass Payment Bot settings.</em></p>
    </body>
    </html>
    """
    
    try:
        # Send email ONLY to configured payment address
        send_email(
            subject=subject,
            to_email=payment_email,
            html_body=html_body
        )
        
        # Log the action
        from utils import log_admin_action
        log_admin_action(f"Test payment email sent by {session.get('admin', 'Unknown')} - Amount: ${amount_float:.2f}")
        
        return jsonify({"success": True, "message": f"Test email sent to {payment_email}"}), 200
    except Exception as e:
        print(f"Error sending test email: {e}")
        return jsonify({"error": "Failed to send test email"}), 500


@app.route("/api/payment-bot/check-emails", methods=["POST"])
@csrf.exempt
def api_payment_bot_check_emails():
    """Manually trigger email payment bot to check for new payments"""
    print(f"🔍 Payment bot API called. Session keys: {list(session.keys())}")
    print(f"🔍 Session admin value: {session.get('admin', 'None')}")
    
    # Bypass authentication for testing - REMOVE THIS AFTER DEBUGGING
    if True:  # Temporary bypass
        print("🔧 BYPASSING AUTH FOR DEBUG")
    elif "admin" not in session:
        print("Unauthorized - no admin in session")
        return jsonify({"error": "Unauthorized"}), 401
    
    from utils import match_gmail_payments_to_passes, get_setting, log_admin_action, cleanup_duplicate_payment_logs_auto

    # Check if payment bot is enabled
    if get_setting("ENABLE_EMAIL_PAYMENT_BOT", "False") != "True":
        return jsonify({"error": "Payment bot is not enabled in settings"}), 400

    try:
        # Log the action first
        log_admin_action(f"Manual payment bot check triggered by {session.get('admin', 'Unknown')}")

        # Run the email checking function
        result = match_gmail_payments_to_passes()

        # Auto-cleanup duplicates after processing (same as scheduled job)
        cleanup_duplicate_payment_logs_auto()
        
        # Return success with any matched payments info
        if result and isinstance(result, dict):
            return jsonify({
                "success": True, 
                "message": f"Email check completed. {result.get('matched', 0)} payments matched.",
                "details": result
            }), 200
        else:
            return jsonify({
                "success": True,
                "message": "Email check completed. No new payments found."
            }), 200
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error running payment bot check: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Provide more specific error messages
        if "AUTHENTICATIONFAILED" in error_msg or "Invalid credentials" in error_msg:
            return jsonify({
                "error": "Email authentication failed. Please check your email settings (username/password)."
            }), 500
        elif "connection" in error_msg.lower():
            return jsonify({
                "error": "Could not connect to email server. Please check your server settings."
            }), 500
        else:
            return jsonify({
                "error": f"Failed to check emails: {error_msg}"
            }), 500


@app.route("/api/move-payment-email", methods=["POST"])
@csrf.exempt
def api_move_payment_email():
    """Manually move a payment email to the manually_processed folder"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    bank_info_name = data.get("bank_info_name")
    bank_info_amt = data.get("bank_info_amt")
    from_email = data.get("from_email")
    custom_note = data.get("custom_note")  # Optional custom note from user

    if not all([bank_info_name, bank_info_amt, from_email]):
        return jsonify({"error": "Missing required fields: bank_info_name, bank_info_amt, from_email"}), 400

    try:
        from utils import move_payment_email_by_criteria, log_admin_action

        print(f"🔧 API DEBUG: Calling move_payment_email_by_criteria with:")
        print(f"   Name: {bank_info_name}")
        print(f"   Amount: {bank_info_amt}")
        print(f"   Email: {from_email}")
        print(f"   Custom Note: {custom_note if custom_note else 'None'}")

        success, message = move_payment_email_by_criteria(bank_info_name, bank_info_amt, from_email, custom_note)

        print(f"🔧 API DEBUG: Function returned - Success: {success}, Message: {message}")

        if success:
            log_admin_action(f"Manually moved payment email: {bank_info_name} - ${bank_info_amt}")
            return jsonify({"success": True, "message": message}), 200
        else:
            print(f"API DEBUG: Returning error 400 with message: {message}")
            return jsonify({"success": False, "error": message}), 400

    except Exception as e:
        import traceback
        print(f"Error moving payment email: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to move email: {str(e)}"}), 500


@app.route("/api/cleanup-duplicate-logs", methods=["POST"])
@csrf.exempt
def api_cleanup_duplicate_logs():
    """Clean up duplicate NO_MATCH payment logs, keeping only the latest for each unique payment"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from models import EbankPayment, db
        from utils import log_admin_action

        # First, get count of duplicates to be deleted
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

        if duplicate_count == 0:
            return jsonify({
                "success": True,
                "message": "No duplicate logs found",
                "deleted_count": 0
            }), 200

        # Delete the duplicates
        duplicates_query.delete(synchronize_session=False)
        db.session.commit()

        log_admin_action(f"Cleaned up {duplicate_count} duplicate payment logs")

        return jsonify({
            "success": True,
            "message": f"Successfully deleted {duplicate_count} duplicate log entries",
            "deleted_count": duplicate_count
        }), 200

    except Exception as e:
        import traceback
        print(f"Error cleaning duplicate logs: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({"error": f"Failed to clean logs: {str(e)}"}), 500


@app.route("/api/get-passport-types/<int:activity_id>", methods=["GET"])
def api_get_passport_types(activity_id):
    """Get active passport types for an activity (used by create passport from payment modal)"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from models import PassportType

        passport_types = PassportType.query.filter_by(
            activity_id=activity_id,
            status='active'
        ).order_by(PassportType.name).all()

        result = [{
            "id": pt.id,
            "name": pt.name,
            "price": pt.price_per_user or 0,
            "sessions": pt.sessions_included or 1
        } for pt in passport_types]

        return jsonify(result), 200

    except Exception as e:
        print(f"Error fetching passport types: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/create-passport-from-payment", methods=["POST"])
@csrf.exempt
def api_create_passport_from_payment():
    """Create a passport directly from an unmatched payment, bypassing signup flow"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from models import User, Passport, PassportType, Activity, EbankPayment, AdminActionLog
        from utils import generate_pass_code, notify_pass_event, log_admin_action
        import time

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Required fields
        payment_id = data.get("payment_id")
        activity_id = data.get("activity_id")
        passport_type_id = data.get("passport_type_id")
        user_name = data.get("name", "").strip()
        user_email = data.get("email", "").strip()

        # Optional fields
        user_phone = data.get("phone", "").strip() or None
        amount = data.get("amount")
        sessions = data.get("sessions")

        # Validate required fields
        if not payment_id:
            return jsonify({"error": "Payment ID is required"}), 400
        if not activity_id:
            return jsonify({"error": "Activity is required"}), 400
        if not passport_type_id:
            return jsonify({"error": "Passport type is required"}), 400
        if not user_name:
            return jsonify({"error": "Name is required"}), 400
        if not user_email:
            return jsonify({"error": "Email is required - all passport communications are sent via email"}), 400

        # Verify payment exists and is NO_MATCH
        payment = db.session.get(EbankPayment, payment_id)
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        if payment.result != "NO_MATCH":
            return jsonify({"error": "Payment is not in NO_MATCH status"}), 400

        # Verify activity exists and is active
        activity = db.session.get(Activity, activity_id)
        if not activity:
            return jsonify({"error": "Activity not found"}), 404
        if activity.status != "active":
            return jsonify({"error": "Activity is not active"}), 400

        # Verify passport type exists and belongs to activity
        passport_type = db.session.get(PassportType, passport_type_id)
        if not passport_type:
            return jsonify({"error": "Passport type not found"}), 404
        if passport_type.activity_id != activity_id:
            return jsonify({"error": "Passport type does not belong to selected activity"}), 400
        if passport_type.status != "active":
            return jsonify({"error": "Passport type is not active"}), 400

        # Get current admin
        current_admin = Admin.query.filter_by(email=session.get("admin")).first()

        # Create User (always create new, even if same email reused - follows existing pattern)
        user = User(name=user_name, email=user_email, phone_number=user_phone)
        db.session.add(user)
        db.session.flush()  # Assign user.id

        # Use provided amount or default to passport type price
        sold_amt = float(amount) if amount is not None else (passport_type.price_per_user or 0)

        # Use provided sessions or default to passport type sessions
        uses_remaining = int(sessions) if sessions is not None else (passport_type.sessions_included or 1)

        # Create Passport (paid=True since we're creating from a payment)
        passport = Passport(
            pass_code=generate_pass_code(),
            user_id=user.id,
            activity_id=activity_id,
            passport_type_id=passport_type_id,
            passport_type_name=passport_type.name,
            sold_amt=sold_amt,
            uses_remaining=uses_remaining,
            created_by=current_admin.id if current_admin else None,
            created_dt=datetime.now(timezone.utc),
            paid=True,
            paid_date=datetime.now(timezone.utc),
            marked_paid_by=session.get("admin", "unknown"),
            notes=f"Created from payment #{payment_id} ({payment.bank_info_name} - ${payment.bank_info_amt})"
        )
        db.session.add(passport)
        db.session.flush()  # Assign passport.id

        # Update EbankPayment to link to passport and mark as matched
        payment.matched_pass_id = passport.id
        payment.matched_name = user_name
        payment.matched_amt = sold_amt
        payment.result = "MATCHED"
        payment.note = f"Manually matched via Create Passport by {session.get('admin', 'unknown')}"

        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Created passport from payment: {user_name} for '{activity.name}' (${sold_amt}) - Payment #{payment_id}"
        ))

        db.session.commit()
        db.session.expire_all()

        # Move the payment email to PaymentProcessed folder (same as automatic matching)
        email_moved = False
        try:
            from utils import get_setting
            import imaplib

            mail_user = get_setting("MAIL_USERNAME")
            mail_pwd = get_setting("MAIL_PASSWORD")
            processed_folder = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "PaymentProcessed")

            print(f"EMAIL MOVE: Starting...")
            print(f"EMAIL MOVE: Payment UID stored: {payment.email_uid}")

            if mail_user and mail_pwd and payment.email_uid:
                imap_server = get_setting("IMAP_SERVER")
                if not imap_server:
                    mail_server = get_setting("MAIL_SERVER")
                    imap_server = mail_server if mail_server else "imap.gmail.com"

                try:
                    mail = imaplib.IMAP4_SSL(imap_server)
                except:
                    mail = imaplib.IMAP4(imap_server, 143)
                    mail.starttls()

                mail.login(mail_user, mail_pwd)
                mail.select("inbox")

                # Use the stored UID directly - no need to search!
                uid = payment.email_uid
                print(f"Using stored UID: {uid}")

                # Check if folder exists, create if needed
                folder_status, _ = mail.select(processed_folder)
                if folder_status != 'OK':
                    print(f"📁 Folder '{processed_folder}' doesn't exist, creating...")
                    try:
                        mail.create(processed_folder)
                        print(f"Created folder '{processed_folder}'")
                    except Exception as create_err:
                        print(f"Could not create folder: {create_err}")

                # Switch back to inbox to perform the copy
                mail.select("inbox")

                # Copy and delete using stored UID
                copy_result = mail.uid("COPY", uid, processed_folder)
                if copy_result[0] == 'OK':
                    mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                    email_moved = True
                    print(f"Payment email moved to {processed_folder} folder")
                else:
                    print(f"Failed to copy email: {copy_result}")

                mail.expunge()
                mail.logout()
            elif not payment.email_uid:
                print(f"No email UID stored for this payment - cannot move email")
                print(f"   (This payment was processed before UID storage was implemented)")

        except Exception as e:
            import traceback
            print(f"Could not move payment email (non-critical): {e}")
            print(f"EMAIL MOVE TRACEBACK: {traceback.format_exc()}")
            # Don't fail the whole operation if email move fails

        # Small sleep for timestamp ordering (follows existing pattern)
        time.sleep(0.3)

        # Send confirmation emails (only if user has email)
        if user_email:
            now_utc = datetime.now(timezone.utc)
            # Send "passport created" email
            notify_pass_event(
                app=current_app._get_current_object(),
                event_type="pass_created",
                pass_data=passport,
                activity=activity,
                admin_email=session.get("admin"),
                timestamp=now_utc
            )
            # Also send "payment confirmed" email since passport is already paid
            notify_pass_event(
                app=current_app._get_current_object(),
                event_type="pass_paid",
                pass_data=passport,
                activity=activity,
                admin_email=session.get("admin"),
                timestamp=now_utc
            )
            email_sent = True
        else:
            email_sent = False

        # Flash message - green if fully successful, warning if email move failed
        result_msg = f"Passport created for {user_name}"
        if email_sent:
            result_msg += f" - confirmation email sent to {user_email}"

        if email_moved:
            # Full success - green
            flash(result_msg, "success")
        else:
            # Partial success - warning (yellow)
            result_msg += ". Warning: payment email could not be moved from inbox (manual cleanup needed)"
            flash(result_msg, "warning")

        return jsonify({
            "success": True,
            "message": result_msg,
            "passport_id": passport.id,
            "pass_code": passport.pass_code,
            "email_sent": email_sent,
            "email_moved": email_moved
        }), 200

    except Exception as e:
        import traceback
        print(f"Error creating passport from payment: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        flash(f"Failed to create passport: {str(e)}", "error")
        return jsonify({"error": f"Failed to create passport: {str(e)}"}), 500


@app.route("/api/unpaid-passports-by-amount/<float:amount>")
def api_get_unpaid_passports_by_amount(amount):
    """Get list of unpaid passports at a specific amount for the Check Unpaid Passports modal"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    passports = db.session.query(Passport).join(User).join(Activity).filter(
        Passport.paid == False,
        Passport.sold_amt == amount
    ).order_by(Passport.created_dt.desc()).all()

    return jsonify([{
        'id': p.id,
        'user_name': p.user.name if p.user else 'Unknown',
        'user_email': p.user.email if p.user else '',
        'activity_name': p.activity.name if p.activity else 'Unknown',
        'passport_type': p.passport_type.name if p.passport_type else (p.passport_type_name or 'N/A'),
        'created_dt': p.created_dt.strftime('%Y-%m-%d') if p.created_dt else ''
    } for p in passports])


@app.route("/api/update-passport-name/<int:passport_id>", methods=["POST"])
def api_update_passport_name(passport_id):
    """Update passport user name - used when matching payment to existing passport with different name"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    new_name = data.get('name', '').strip() if data else ''

    if not new_name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    passport = Passport.query.get(passport_id)
    if not passport:
        return jsonify({'success': False, 'error': 'Passport not found'}), 404

    if not passport.user:
        return jsonify({'success': False, 'error': 'Passport has no associated user'}), 400

    old_name = passport.user.name
    passport.user.name = new_name

    # Log the action
    log = AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=f"Updated passport user name: Passport {passport.pass_code}: '{old_name}' -> '{new_name}'"
    )
    db.session.add(log)
    db.session.commit()

    # Set flash message for page reload
    flash(f"Name updated to \"{new_name}\". Will match on next sync.", "success")

    return jsonify({'success': True, 'old_name': old_name, 'new_name': new_name})


@app.route("/api/payment-notification-html/<notification_id>", methods=["POST"])
@csrf.exempt
def api_payment_notification_html(notification_id):
    """Render HTML for payment notification"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Get notification data from request
        notification_data = request.get_json()
        if not notification_data:
            return jsonify({"error": "No notification data provided"}), 400
        
        # Render the notification template
        html = render_template('partials/event_notification.html', data=notification_data)
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        current_app.logger.error(f"Error rendering payment notification HTML: {e}")
        return jsonify({"error": "Failed to render notification"}), 500

@app.route("/api/signup-notification-html/<notification_id>", methods=["POST"])
@csrf.exempt
def api_signup_notification_html(notification_id):
    """Render HTML for signup notification"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Get notification data from request
        notification_data = request.get_json()
        if not notification_data:
            return jsonify({"error": "No notification data provided"}), 400
        
        # Render the notification template
        html = render_template('partials/event_notification.html', data=notification_data)
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        current_app.logger.error(f"Error rendering signup notification HTML: {e}")
        return jsonify({"error": "Failed to render notification"}), 500

@app.route("/api/payment-bot/logs", methods=["GET"])
def api_payment_bot_logs():
    """Get recent payment logs (sanitized for XSS prevention)"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    from markupsafe import escape
    
    # Get last 10 payment logs
    recent_payments = EbankPayment.query.order_by(EbankPayment.timestamp.desc()).limit(10).all()
    
    # Sanitize and format for display
    logs = []
    for payment in recent_payments:
        logs.append({
            "id": payment.id,
            "date_sent": payment.timestamp.strftime("%Y-%m-%d %H:%M") if payment.timestamp else "Unknown",
            "from_email": escape(payment.from_email or "Unknown"),
            "subject": escape(payment.subject or "No subject")[:100],
            "amount": float(payment.bank_info_amt) if payment.bank_info_amt else 0.0,
            "bank_info_name": escape(payment.bank_info_name or "Unknown")[:50],
            "matched_pass": bool(payment.matched_pass_id),
            "match_confidence": payment.name_score or 0
        })
    
    return jsonify({"logs": logs}), 200


# ================================
# 📱 PUSH NOTIFICATION API ROUTES
# ================================

@app.route("/service-worker.js")
def serve_service_worker():
    """Serve service worker from root for full site scope (required for push notifications)"""
    return send_from_directory(
        app.static_folder,
        'service-worker.js',
        mimetype='application/javascript'
    )


@app.route("/manifest.json")
def dynamic_manifest():
    """Serve dynamic manifest with subdomain as app name for PWA.

    Each subdomain gets a unique PWA identity via the 'id' field.
    This allows multiple installations (LHGI, HEQ, etc.) on the same device.
    """
    host = request.host.split(':')[0]
    parts = host.split('.')

    if len(parts) >= 3:
        subdomain = parts[0].upper()
        subdomain_lower = parts[0].lower()
    else:
        subdomain = "Minipass"
        subdomain_lower = "minipass"

    manifest = {
        "id": f"/{subdomain_lower}/",
        "name": f"{subdomain} - Activity Manager",
        "short_name": subdomain,
        "description": "Manage activities, signups, payments, and digital passes",
        "start_url": "/?source=pwa",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#00ab66",
        "orientation": "any",
        "scope": "/",
        "icons": [
            {"src": "/static/favicon.png", "sizes": "32x32", "type": "image/png"},
            {"src": "/static/icons/icon-96x96.png", "sizes": "96x96", "type": "image/png"},
            {"src": "/static/icons/icon-144x144.png", "sizes": "144x144", "type": "image/png"},
            {"src": "/static/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
            {"src": "/static/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    }

    response = jsonify(manifest)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


@app.route("/api/push/vapid-public-key", methods=["GET"])
def get_vapid_public_key():
    """Return the VAPID public key for client-side subscription"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    from utils import get_or_create_vapid_keys
    try:
        keys = get_or_create_vapid_keys()
        return jsonify({"publicKey": keys['public_key']})
    except Exception as e:
        current_app.logger.error(f"Error getting VAPID keys: {e}")
        return jsonify({"error": "Failed to get VAPID keys"}), 500


@csrf.exempt
@app.route("/api/push/subscribe", methods=["POST"])
def push_subscribe():
    """Save a push notification subscription for the current admin"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or not data.get('subscription'):
        return jsonify({"error": "Invalid subscription data"}), 400

    subscription = data['subscription']
    endpoint = subscription.get('endpoint')
    keys = subscription.get('keys', {})
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')

    if not all([endpoint, p256dh, auth]):
        return jsonify({"error": "Missing subscription fields"}), 400

    admin = Admin.query.filter_by(email=session.get("admin")).first()
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    from models import PushSubscription

    # Check if subscription already exists (update or create)
    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        existing.admin_id = admin.id
        existing.p256dh_key = p256dh
        existing.auth_key = auth
        existing.user_agent = request.headers.get('User-Agent', '')[:255]
    else:
        new_sub = PushSubscription(
            admin_id=admin.id,
            endpoint=endpoint,
            p256dh_key=p256dh,
            auth_key=auth,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(new_sub)

    db.session.commit()

    from utils import log_admin_action
    log_admin_action(f"Push notifications enabled by {session.get('admin')}")

    return jsonify({"success": True, "message": "Subscription saved"})


@csrf.exempt
@app.route("/api/push/unsubscribe", methods=["POST"])
def push_unsubscribe():
    """Remove a push notification subscription"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    endpoint = data.get('endpoint') if data else None

    admin = Admin.query.filter_by(email=session.get("admin")).first()
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    from models import PushSubscription

    if endpoint:
        # Remove specific subscription
        PushSubscription.query.filter_by(
            admin_id=admin.id,
            endpoint=endpoint
        ).delete()
    else:
        # Remove all subscriptions for this admin
        PushSubscription.query.filter_by(admin_id=admin.id).delete()

    db.session.commit()

    from utils import log_admin_action
    log_admin_action(f"Push notifications disabled by {session.get('admin')}")

    return jsonify({"success": True, "message": "Unsubscribed"})


@app.route("/api/push/status", methods=["GET"])
def push_status():
    """Check if current admin has active push subscriptions"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    admin = Admin.query.filter_by(email=session.get("admin")).first()
    if not admin:
        return jsonify({"subscribed": False})

    from models import PushSubscription
    count = PushSubscription.query.filter_by(admin_id=admin.id).count()
    return jsonify({
        "subscribed": count > 0,
        "subscription_count": count
    })


@csrf.exempt
@app.route("/api/push/test", methods=["POST"])
def push_test():
    """Send a test push notification to the current admin"""
    if "admin" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    admin = Admin.query.filter_by(email=session.get("admin")).first()
    if not admin:
        return jsonify({"success": False, "error": "Admin not found"}), 404

    from models import PushSubscription
    subscriptions = PushSubscription.query.filter_by(admin_id=admin.id).all()

    if not subscriptions:
        return jsonify({
            "success": False,
            "error": "No push subscriptions found. Please enable push notifications first.",
            "subscription_count": 0
        })

    from utils import send_push_notification_to_admin
    try:
        sent_count = send_push_notification_to_admin(
            admin_id=admin.id,
            title="Test Notification",
            body="If you see this, push notifications are working!",
            url="/unified_settings",
            tag="test-notification"
        )
        return jsonify({
            "success": True,
            "message": f"Test notification sent to {sent_count} device(s)",
            "sent_count": sent_count,
            "subscription_count": len(subscriptions)
        })
    except Exception as e:
        current_app.logger.error(f"Push test error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "subscription_count": len(subscriptions)
        }), 500


@app.route("/setup", methods=["GET", "POST"])
def setup():

    ##
    ##  POST REQUEST 
    ##

    if request.method == "POST":
        # 🔐 Step 1: Admin accounts
        admin_emails = request.form.getlist("admin_email[]")
        admin_passwords = request.form.getlist("admin_password[]")
        admin_first_names = request.form.getlist("admin_first_name[]")
        admin_last_names = request.form.getlist("admin_last_name[]")

        # Create avatar upload directory if needed
        avatar_dir = os.path.join(app.config["UPLOAD_FOLDER"], "avatars")
        os.makedirs(avatar_dir, exist_ok=True)

        # Process admins with names and avatar support
        for i, (email, password) in enumerate(zip(admin_emails, admin_passwords)):
            email = email.strip()
            password = password.strip()
            first_name = admin_first_names[i].strip() if i < len(admin_first_names) else ""
            last_name = admin_last_names[i].strip() if i < len(admin_last_names) else ""
            
            if not email:
                continue

            # Handle avatar upload
            avatar_filename = None
            avatar_file_key = f"admin_avatar_{i+1}"
            if avatar_file_key in request.files:
                avatar_file = request.files[avatar_file_key]
                if avatar_file and avatar_file.filename:
                    # Generate unique filename
                    ext = os.path.splitext(avatar_file.filename)[1]
                    avatar_filename = f"admin_{email.replace('@', '_').replace('.', '_')}_{int(time.time())}{ext}"
                    avatar_path = os.path.join(avatar_dir, avatar_filename)
                    avatar_file.save(avatar_path)

            existing = Admin.query.filter_by(email=email).first()
            if existing:
                # Update existing admin (passwords managed via /change-password and /reset-admin-password)
                # Update names (allow empty values for backward compatibility)
                existing.first_name = first_name if first_name else None
                existing.last_name = last_name if last_name else None
                # Update avatar if uploaded
                if avatar_filename:
                    # Delete old avatar if exists
                    if existing.avatar_filename:
                        old_avatar = os.path.join(avatar_dir, existing.avatar_filename)
                        if os.path.exists(old_avatar):
                            os.remove(old_avatar)
                    existing.avatar_filename = avatar_filename
            else:
                # Create new admin
                if password and password != "********":
                    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    new_admin = Admin(
                        email=email, 
                        password_hash=hashed,
                        first_name=first_name if first_name else None,
                        last_name=last_name if last_name else None,
                        avatar_filename=avatar_filename
                    )
                    db.session.add(new_admin)

        # 🗑️ Step 2: Remove deleted admins
        deleted_emails_raw = request.form.get("deleted_admins", "")
        if deleted_emails_raw:
            for email in deleted_emails_raw.split(","):
                email = email.strip()
                if email:
                    admin_to_delete = Admin.query.filter_by(email=email).first()
                    if admin_to_delete:
                        # Clear foreign key references before deleting to avoid constraint errors
                        Activity.query.filter_by(created_by=admin_to_delete.id).update({"created_by": None})
                        Passport.query.filter_by(created_by=admin_to_delete.id).update({"created_by": None})
                        SurveyTemplate.query.filter_by(created_by=admin_to_delete.id).update({"created_by": None})
                        Survey.query.filter_by(created_by=admin_to_delete.id).update({"created_by": None})
                        db.session.delete(admin_to_delete)

        # 📧 Step 3: Email settings
        email_settings = {
            "MAIL_SERVER": request.form.get("mail_server", "").strip(),
            "MAIL_PORT": request.form.get("mail_port", "587").strip(),
            "MAIL_USE_TLS": "mail_use_tls" in request.form,
            "MAIL_USERNAME": request.form.get("mail_username", "").strip(),
            "MAIL_PASSWORD": request.form.get("mail_password_raw", "").strip(),
            "MAIL_DEFAULT_SENDER": request.form.get("mail_default_sender", "").strip(),
            "MAIL_SENDER_NAME": request.form.get("mail_sender_name", "").strip()
        }

        for key, value in email_settings.items():
            if key == "MAIL_PASSWORD" and (not value or value == "********"):
                continue
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
            else:
                db.session.add(Setting(key=key, value=str(value)))

        # ⚙️ Step 4: App-level settings
        extra_settings = {
            # OBSOLETE: These fields removed from UI on 2025-01-24, using hardcoded defaults
            # "DEFAULT_PASS_AMOUNT": request.form.get("default_pass_amount", "50").strip(),
            # "DEFAULT_SESSION_QT": request.form.get("default_session_qt", "4").strip(),
            # "EMAIL_INFO_TEXT": request.form.get("email_info_text", "").strip(),
            # "EMAIL_FOOTER_TEXT": request.form.get("email_footer_text", "").strip(),
            "DEFAULT_PASS_AMOUNT": str(REMOVED_FIELD_DEFAULTS['default_pass_amount']),
            "DEFAULT_SESSION_QT": str(REMOVED_FIELD_DEFAULTS['default_session_qt']),
            "EMAIL_INFO_TEXT": REMOVED_FIELD_DEFAULTS['email_info_text'],
            "EMAIL_FOOTER_TEXT": REMOVED_FIELD_DEFAULTS['email_footer_text']
        }

        # Only update ORG_NAME and CALL_BACK_DAYS if they're in the form (prevents overwriting from other tabs)
        if "ORG_NAME" in request.form:
            extra_settings["ORG_NAME"] = request.form.get("ORG_NAME", "").strip()
        if "CALL_BACK_DAYS" in request.form:
            extra_settings["CALL_BACK_DAYS"] = request.form.get("CALL_BACK_DAYS", "0").strip()
        if "FISCAL_YEAR_START_MONTH" in request.form:
            extra_settings["FISCAL_YEAR_START_MONTH"] = request.form.get("FISCAL_YEAR_START_MONTH", "1").strip()

        for key, value in extra_settings.items():
            existing = Setting.query.filter_by(key=key).first()
            if existing:
                existing.value = value
            else:
                db.session.add(Setting(key=key, value=value))

        # 🤖 Step 5: Email Payment Bot Config
        # Only update bot settings if they're in the form (prevents overwriting from other tabs)
        bot_settings = {
            "GMAIL_LABEL_FOLDER_PROCESSED": REMOVED_FIELD_DEFAULTS['gmail_label_folder_processed']
        }

        if "enable_email_payment_bot" in request.form or "bank_email_from" in request.form:
            # Bot config section was submitted, update all bot settings
            bot_settings["ENABLE_EMAIL_PAYMENT_BOT"] = "enable_email_payment_bot" in request.form
            bot_settings["BANK_EMAIL_FROM"] = request.form.get("bank_email_from", "").strip()
            bot_settings["BANK_EMAIL_SUBJECT"] = request.form.get("bank_email_subject", "").strip()
            bot_settings["BANK_EMAIL_NAME_CONFIDANCE"] = request.form.get("bank_email_name_confidance", "85").strip()

        for key, value in bot_settings.items():
            existing = Setting.query.filter_by(key=key).first()
            if existing:
                existing.value = str(value)
            else:
                db.session.add(Setting(key=key, value=str(value)))

        # 🏷 Step 6: Activity Tags
        # OBSOLETE: Activity tags/ACTIVITY_LIST field removed from UI on 2025-01-24
        # activity_raw = request.form.get("activities", "").strip()
        # Using hardcoded default empty list
        try:
            activity_list = REMOVED_FIELD_DEFAULTS['activity_tags']
            setting = Setting.query.filter_by(key="ACTIVITY_LIST").first()
            if setting:
                setting.value = json.dumps(activity_list)
            else:
                db.session.add(Setting(key="ACTIVITY_LIST", value=json.dumps(activity_list)))
        except Exception as e:
            print("Failed to save activity list:", e)

        # 🖼 Step 7: Logo Upload
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        logo_file = request.files.get("ORG_LOGO_FILE")

        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            logo_file.save(logo_path)

            setting = Setting.query.filter_by(key="LOGO_FILENAME").first()
            if setting:
                setting.value = filename
            else:
                db.session.add(Setting(key="LOGO_FILENAME", value=filename))

            flash("Logo uploaded successfully!", "success")

            # Propagate new org logo to all existing activity owner_logo snapshots
            for act in Activity.query.all():
                snapshot = os.path.join(app.config["UPLOAD_FOLDER"], f"{act.id}_owner_logo.png")
                if os.path.exists(snapshot):
                    shutil.copy(logo_path, snapshot)

        db.session.commit()
        print("[SETUP] Admins configured:", admin_emails)
        print("[SETUP] Settings saved:", list(email_settings.keys()) + list(extra_settings.keys()))

        flash("Setup completed successfully!", "success")
        return redirect(url_for("setup"))

    ##
    ##  GET request — Load existing config
    ##

    settings = {s.key: s.value for s in Setting.query.all()}
    admins = Admin.query.all()
    backup_file = request.args.get("backup_file")

    backup_dir = os.path.join("static", "backups")
    backup_files = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".zip")],
        reverse=True
    ) if os.path.exists(backup_dir) else []

    print("📥 Received backup_file from args:", backup_file)
    
    # Safely check and create static/backups directory if needed
    if os.path.exists("static/backups"):
        print("🗂️ Available backups in static/backups/:", os.listdir("static/backups"))
    else:
        print("🗂️ static/backups directory not found - creating it")
        os.makedirs("static/backups", exist_ok=True)
        print("🗂️ Available backups in static/backups/:", [])

    template_base = os.path.join("templates", "email_templates")
    email_templates = []

    # Safely check if templates directory exists
    if not os.path.exists(template_base):
        print(f"Templates directory not found: {template_base}")
        os.makedirs(template_base, exist_ok=True)

    for entry in os.listdir(template_base):
        full_path = os.path.join(template_base, entry)

        if entry.endswith(".html") and os.path.isfile(full_path):
            email_templates.append(entry)
        elif entry.endswith("_compiled") and os.path.isdir(full_path):
            index_path = os.path.join(full_path, "index.html")
            if os.path.exists(index_path):
                email_templates.append(entry.replace("_compiled", "") + ".html")

    # Add survey invitation template manually since it's in the main templates folder
    email_templates.append("email_survey_invitation.html")
    email_templates.sort()

    # Get fiscal year display string
    from utils import get_fiscal_year_display
    fiscal_year_display = get_fiscal_year_display()

    return render_template(
        "setup.html",
        settings=settings,
        admins=admins,
        backup_file=backup_file,
        backup_files=backup_files,
        email_templates=email_templates,
        fiscal_year_display=fiscal_year_display
    )


# ================================
# 🔧 UNIFIED SETTINGS MANAGEMENT
# ================================

@app.route("/admin/unified-settings", methods=["GET", "POST"])
def unified_settings():
    """Unified settings page that consolidates organization, email, and payment bot settings"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    # Check if this is a GET request with test_payment_bot parameter
    if request.args.get("test_payment_bot") == "1":
        try:
            from utils import match_gmail_payments_to_passes, log_admin_action
            print("🔧 GET Manual payment bot trigger activated!")
            
            log_admin_action(f"Manual payment bot test by {session.get('admin', 'Unknown')}")
            result = match_gmail_payments_to_passes()
            
            if result and isinstance(result, dict):
                matched = result.get('matched', 0)
                no_match = result.get('no_match', 0)
                skipped = result.get('skipped', 0)
                emails_found = result.get('emails_found', 0)

                if matched > 0:
                    # Success - found and matched payments
                    flash(f"Found {matched} payment(s) matched to passports!", "success")
                elif no_match > 0:
                    # Warning - found payments but couldn't match
                    flash(f"Found {no_match} payment(s) - needs manual review (no matching passport)", "warning")
                elif emails_found > 0 and skipped > 0:
                    # Info - found emails but all were already processed
                    flash(f"{skipped} payment(s) already processed - no new payments.", "info")
                else:
                    # Info - no payments found in inbox
                    flash("No new payments found in inbox.", "info")
            else:
                flash("Payment bot completed. No emails to process.", "info")
                
        except Exception as e:
            print(f"Payment bot test error: {e}")
            flash(f"Payment bot test failed: {str(e)}", "error")

        # Redirect back to payment_bot_matches page
        return redirect(url_for("payment_bot_matches"))
    
    # Check if this is a GET request with test_late_payment parameter
    if request.args.get("test_late_payment") == "1":
        try:
            from utils import send_unpaid_reminders, log_admin_action
            print("🔧 GET Manual late payment reminder test activated!")
            
            log_admin_action(f"Manual late payment reminder test by {session.get('admin', 'Unknown')}")
            send_unpaid_reminders(current_app, force_send=True)
            
            flash("Late payment reminder test completed. Check console for details.", "success")
                
        except Exception as e:
            print(f"Late payment reminder test error: {e}")
            flash(f"Late payment reminder test failed: {str(e)}", "error")

        # Redirect back to payment_bot_matches if that's where they came from
        return redirect(url_for("payment_bot_matches"))
    
    if request.method == "POST":
        # Check if this is a manual payment bot trigger
        if request.form.get("action") == "test_payment_bot":
            try:
                from utils import match_gmail_payments_to_passes, log_admin_action
                print("🔧 Manual payment bot trigger activated!")
                
                log_admin_action(f"Manual payment bot test by {session.get('admin', 'Unknown')}")
                result = match_gmail_payments_to_passes()
                
                if result and isinstance(result, dict):
                    matched = result.get('matched', 0)
                    no_match = result.get('no_match', 0)
                    skipped = result.get('skipped', 0)
                    emails_found = result.get('emails_found', 0)

                    if matched > 0:
                        flash(f"Found {matched} payment(s) matched to passports!", "success")
                    elif no_match > 0:
                        flash(f"Found {no_match} payment(s) - needs manual review (no matching passport)", "warning")
                    elif emails_found > 0 and skipped > 0:
                        flash(f"{skipped} payment(s) already processed - no new payments.", "info")
                    else:
                        flash("No new payments found in inbox.", "info")
                else:
                    flash("Payment bot completed. No emails to process.", "info")

            except Exception as e:
                print(f"Payment bot test error: {e}")
                flash(f"Payment bot test failed: {str(e)}", "error")

            return redirect(url_for("unified_settings"))
            
        try:
            # Step 1: Organization Settings
            org_settings = {
                "ORG_NAME": request.form.get("ORG_NAME", "").strip(),
                "CALL_BACK_DAYS": request.form.get("CALL_BACK_DAYS", "0").strip(),
                # Keep hardcoded defaults for removed fields
                "DEFAULT_PASS_AMOUNT": str(REMOVED_FIELD_DEFAULTS['default_pass_amount']),
                "DEFAULT_SESSION_QT": str(REMOVED_FIELD_DEFAULTS['default_session_qt']),
                "EMAIL_INFO_TEXT": REMOVED_FIELD_DEFAULTS['email_info_text'],
                "EMAIL_FOOTER_TEXT": REMOVED_FIELD_DEFAULTS['email_footer_text'],
            }
            
            for key, value in org_settings.items():
                existing = Setting.query.filter_by(key=key).first()
                if existing:
                    existing.value = value
                else:
                    db.session.add(Setting(key=key, value=value))
            
            # Step 2: Logo Upload / Delete
            logo_filename = None  # Track uploaded logo for response
            delete_logo = request.form.get("delete_logo") == "1"
            if delete_logo:
                logo_setting = Setting.query.filter_by(key="LOGO_FILENAME").first()
                if logo_setting and logo_setting.value:
                    old_logo_path = os.path.join(app.config["UPLOAD_FOLDER"], logo_setting.value)
                    if os.path.exists(old_logo_path):
                        os.remove(old_logo_path)
                    logo_setting.value = ""
                # Clean up activity owner_logo snapshots so they regenerate
                for act in Activity.query.all():
                    snapshot = os.path.join(app.config["UPLOAD_FOLDER"], f"{act.id}_owner_logo.png")
                    if os.path.exists(snapshot):
                        os.remove(snapshot)

            logo_file = request.files.get("ORG_LOGO_FILE")
            if logo_file and logo_file.filename and not delete_logo:
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                filename = secure_filename(logo_file.filename)
                logo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                logo_file.save(logo_path)
                logo_filename = filename  # Store for JSON response
                
                setting = Setting.query.filter_by(key="LOGO_FILENAME").first()
                if setting:
                    setting.value = filename
                else:
                    db.session.add(Setting(key="LOGO_FILENAME", value=filename))

                # Propagate new org logo to all existing activity owner_logo snapshots
                for act in Activity.query.all():
                    snapshot = os.path.join(app.config["UPLOAD_FOLDER"], f"{act.id}_owner_logo.png")
                    if os.path.exists(snapshot):
                        shutil.copy(logo_path, snapshot)

            # Step 3: Email Settings
            email_settings = {
                "MAIL_SERVER": request.form.get("mail_server", "").strip(),
                "MAIL_PORT": request.form.get("mail_port", "587").strip(),
                "MAIL_USE_TLS": "mail_use_tls" in request.form,
                "MAIL_USERNAME": request.form.get("mail_username", "").strip(),
                "MAIL_PASSWORD": request.form.get("mail_password_raw", "").strip(),
                "MAIL_DEFAULT_SENDER": request.form.get("mail_default_sender", "").strip(),
                "MAIL_SENDER_NAME": request.form.get("mail_sender_name", "").strip()
            }
            
            for key, value in email_settings.items():
                if key == "MAIL_PASSWORD" and (not value or value == "********"):
                    continue
                setting = Setting.query.filter_by(key=key).first()
                if setting:
                    setting.value = str(value)
                else:
                    db.session.add(Setting(key=key, value=str(value)))
            
            # Step 4: Payment Bot Settings
            bot_settings = {
                "ENABLE_EMAIL_PAYMENT_BOT": "enable_email_payment_bot" in request.form,
                "BANK_EMAIL_FROM": request.form.get("bank_email_from", "").strip(),
                "BANK_EMAIL_SUBJECT": request.form.get("bank_email_subject", "").strip(),
                "BANK_EMAIL_NAME_CONFIDANCE": request.form.get("bank_email_name_confidance", "85").strip(),
                "GMAIL_LABEL_FOLDER_PROCESSED": REMOVED_FIELD_DEFAULTS['gmail_label_folder_processed'],
                "DISPLAY_PAYMENT_EMAIL": request.form.get("display_payment_email", "").strip()
            }
            
            for key, value in bot_settings.items():
                existing = Setting.query.filter_by(key=key).first()
                if existing:
                    existing.value = str(value)
                else:
                    db.session.add(Setting(key=key, value=str(value)))
            
            # Step 5: Save all changes
            db.session.commit()

            # Log the action
            from utils import log_admin_action
            log_admin_action(f"Unified Settings Updated by {session.get('admin', 'Unknown')}")

            # Always use standard flash messages and redirect
            flash("All settings saved successfully!", "success")
            return redirect(url_for("unified_settings"))

        except Exception as e:
            db.session.rollback()

            # Always use standard flash messages and redirect
            flash(f"Error saving settings: {str(e)}", "error")
            return redirect(url_for("unified_settings"))
    
    # GET request - load all settings
    settings = {s.key: s.value for s in Setting.query.all()}

    return render_template("unified_settings.html", settings=settings)


# Alternative route name to match template url_for reference
@app.route("/admin/save-unified-settings", methods=["POST"])
def save_unified_settings():
    """Alternative endpoint name to match template url_for reference"""
    return unified_settings()


@app.route("/current-plan", methods=['GET', 'POST'])
def current_plan():
    """Display current subscription plan and manage subscription."""
    if "admin" not in session:
        return redirect(url_for("login"))

    logger.info(f"[CURRENT_PLAN] === Request: {request.method} ===")

    # Get tier information (existing logic)
    tier_info = get_tier_info()
    usage_info = get_activity_usage_display()

    # Get subscription metadata from .env - renamed to avoid conflict with context processor
    subscription_meta = get_subscription_metadata()
    logger.info(f"[CURRENT_PLAN] Subscription meta - is_paid: {subscription_meta['is_paid_subscriber']}, ID: {subscription_meta.get('subscription_id')}")

    # Get live subscription details from Stripe API
    subscription_details = get_subscription_details()
    logger.info(f"[CURRENT_PLAN] Live details from Stripe: {subscription_details}")

    # Handle unsubscribe POST request
    if request.method == 'POST':
        action = request.form.get('action')
        logger.info(f"[CURRENT_PLAN] POST action received: '{action}'")

        if action == 'cancel' and subscription_meta['is_paid_subscriber']:
            logger.info(f"[CURRENT_PLAN] ✓ Condition passed - calling cancel_subscription")
            success, message = cancel_subscription(subscription_meta['subscription_id'])

            logger.info(f"[CURRENT_PLAN] Cancel result - success: {success}, message: {message}")
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')

            return redirect(url_for('current_plan'))
        else:
            logger.warning(f"[CURRENT_PLAN] ✗ Cancel condition FAILED - action: '{action}', is_paid: {subscription_meta['is_paid_subscriber']}")

    return render_template(
        "current_plan.html",
        tier_info=tier_info,
        usage_info=usage_info,
        subscription_meta=subscription_meta,
        subscription_details=subscription_details
    )


@app.route("/erase-app-data", methods=["POST"])
def erase_app_data():
    if "admin" not in session:
        return redirect(url_for("login"))

    try:
        # 📛 List of tables to exclude
        protected_tables = ["Admin", "Setting"]

        # 🧨 Dynamically delete data from all tables except Admin and Setting
        from models import db
        for table in db.metadata.sorted_tables:
            if table.name not in [t.lower() for t in protected_tables]:
                db.session.execute(table.delete())

        db.session.commit()
        flash("All app data erased successfully, except Admins and Settings.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error erasing data: {e}")
        flash("An error occurred while erasing data.", "error")

    return redirect(url_for("setup"))



@app.route("/generate-backup")
def generate_backup():
    if "admin" not in session:
        return redirect(url_for("login"))

    from zipfile import ZipFile
    import tempfile
    import shutil

    try:
        # ✅ Use real DB path from config
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        db_path = db_uri.replace("sqlite:///", "")
        db_filename = os.path.basename(db_path)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_filename = f"minipass_backup_{timestamp}.zip"
        print("Generating backup:", zip_filename)

        tmp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(tmp_dir, zip_filename)

        with ZipFile(zip_path, "w") as zipf:
            # Add database in expected folder structure
            zipf.write(db_path, arcname=f"database/{db_filename}")
            
            # Add metadata
            metadata = {
                "backup_type": "full",
                "version": "2.0",
                "created_by": session.get("admin", "unknown"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "database_file": db_filename
            }
            zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            
            # Add all uploaded files
            uploads_dir = os.path.join(app.static_folder, "uploads")
            if os.path.exists(uploads_dir):
                for root, dirs, files in os.walk(uploads_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Create archive path relative to app root
                        archive_path = os.path.relpath(file_path, start=os.path.dirname(app.static_folder))
                        zipf.write(file_path, arcname=archive_path)
            
            # Add ALL email template files (HTML, compiled, images, etc.)
            email_templates_dir = os.path.join("templates", "email_templates")
            if os.path.exists(email_templates_dir):
                for root, dirs, files in os.walk(email_templates_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Keep relative path from app root
                        archive_path = os.path.relpath(file_path, start='.')
                        zipf.write(file_path, arcname=archive_path)

        final_path = os.path.join("static", "backups", zip_filename)
        os.makedirs(os.path.dirname(final_path), exist_ok=True)

        print(f"🛠 Moving zip from {zip_path} → {final_path}")
        shutil.move(zip_path, final_path)
        print(f"Backup saved to: {final_path}")

        # Auto-cleanup: Keep only the 5 most recent backups
        backup_dir = os.path.join("static", "backups")
        if os.path.exists(backup_dir):
            backup_files = sorted(
                [f for f in os.listdir(backup_dir) if f.endswith(".zip")],
                reverse=True  # Most recent first
            )
            if len(backup_files) > 5:
                for old_backup in backup_files[5:]:  # Keep first 5, delete rest
                    old_path = os.path.join(backup_dir, old_backup)
                    os.remove(old_path)
                    print(f"Deleted old backup: {old_backup}")

        flash(f"Backup created: {zip_filename}", "success")
    except Exception as e:
        print("Backup failed:", str(e))
        flash("Backup failed. Check logs.", "danger")

    return redirect(url_for("setup", backup_file=zip_filename) + "#tab-backup")


@app.route("/delete-backup/<filename>", methods=["POST"])
def delete_backup(filename):
    if "admin" not in session:
        return redirect(url_for("login"))

    try:
        # Security: Only allow .zip files and prevent path traversal
        if not filename.endswith(".zip") or "/" in filename or "\\" in filename:
            flash("Invalid backup filename.", "danger")
            return redirect(url_for("setup") + "#tab-backup")

        backup_path = os.path.join("static", "backups", filename)
        if os.path.exists(backup_path):
            os.remove(backup_path)
            print(f"Backup deleted: {filename}")
            flash(f"Backup deleted: {filename}", "success")
        else:
            flash("Backup file not found.", "danger")
    except Exception as e:
        print("Delete backup failed:", str(e))
        flash("Failed to delete backup. Check logs.", "danger")

    return redirect(url_for("setup") + "#tab-backup")


@app.route("/restore-backup/<filename>", methods=["POST"])
def restore_backup(filename):
    if "admin" not in session:
        return redirect(url_for("login"))

    try:
        # Security: Only allow .zip files and prevent path traversal
        if not filename.endswith(".zip") or "/" in filename or "\\" in filename:
            flash("Invalid backup filename.", "danger")
            return redirect(url_for("setup") + "#tab-backup")

        backup_path = os.path.join("static", "backups", filename)
        if not os.path.exists(backup_path):
            flash("Backup file not found.", "danger")
            return redirect(url_for("setup") + "#tab-backup")

        # Import restore functions directly
        from api.backup import restore_database, restore_uploads, restore_templates, create_restore_point
        from zipfile import ZipFile
        import tempfile
        
        try:
            # Create restore point before restoration
            create_restore_point()
            
            # Extract and restore from the backup file
            with tempfile.TemporaryDirectory() as temp_extract_dir:
                with ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_extract_dir)
                
                # Restore database, uploads, and templates
                restore_database(temp_extract_dir)
                restore_uploads(temp_extract_dir)
                restore_templates(temp_extract_dir)
            
            flash(f"Successfully restored from backup: {filename}", "success")
            
        except Exception as restore_error:
            print(f"Direct restore failed: {str(restore_error)}")
            flash(f"Restore failed: {str(restore_error)}", "danger")

    except Exception as e:
        print("Restore backup failed:", str(e))
        flash("Failed to restore backup. Check logs.", "danger")

    return redirect(url_for("setup") + "#tab-backup")


@app.route("/upload-and-restore-backup", methods=["POST"])
def upload_and_restore_backup():
    if "admin" not in session:
        return redirect(url_for("login"))

    try:
        # Check if file was uploaded
        if 'backup_file' not in request.files:
            flash("No backup file selected.", "danger")
            return redirect(url_for("setup") + "#tab-backup")

        file = request.files['backup_file']
        if file.filename == '':
            flash("No backup file selected.", "danger")
            return redirect(url_for("setup") + "#tab-backup")

        # Validate file extension
        if not file.filename.endswith('.zip'):
            flash("Only ZIP backup files are supported.", "danger")
            return redirect(url_for("setup") + "#tab-backup")

        # Save uploaded file temporarily
        import tempfile
        import shutil
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"uploaded_backup_{timestamp}_{filename}"
        
        # Ensure backup directory exists
        backup_dir = os.path.join("static", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Save uploaded file
        temp_backup_path = os.path.join(backup_dir, temp_filename)
        file.save(temp_backup_path)
        
        # Import restore functions directly
        from api.backup import restore_database, restore_uploads, restore_templates, create_restore_point, cleanup_old_safety_backups
        from zipfile import ZipFile

        try:
            # Create restore point before restoration
            create_restore_point()

            # Extract and restore from the uploaded backup
            with tempfile.TemporaryDirectory() as temp_extract_dir:
                with ZipFile(temp_backup_path, 'r') as zipf:
                    zipf.extractall(temp_extract_dir)

                # Restore database, uploads, and templates
                restore_database(temp_extract_dir)
                restore_uploads(temp_extract_dir)
                restore_templates(temp_extract_dir)

            # CLEANUP OLD BACKUPS - Keep only 3 most recent
            cleanup_old_safety_backups(keep_count=3)

            # Clean up the temporary uploaded file
            try:
                os.remove(temp_backup_path)
            except:
                pass

            flash(f"Successfully restored from uploaded backup: {filename}", "success")
            
        except Exception as restore_error:
            # Clean up the temporary uploaded file
            try:
                os.remove(temp_backup_path)
            except:
                pass
            
            print(f"Direct restore failed: {str(restore_error)}")
            flash(f"Restore failed: {str(restore_error)}", "danger")

    except Exception as e:
        print("Upload and restore failed:", str(e))
        flash("Failed to upload and restore backup. Check logs.", "danger")

    return redirect(url_for("setup") + "#tab-backup")


@app.route("/users.json")
def users_json():
    from models import User

    # Get all users ordered by ID descending (newest first)
    users = (
        db.session.query(User.name, User.email, User.phone_number, User.id)
        .filter(User.name.isnot(None))
        .filter(User.name != '')
        .order_by(User.id.desc())
        .all()
    )

    # Deduplicate by name (case-insensitive), keeping the first (newest) record
    seen_names = set()
    result = []
    for u in users:
        name_lower = u[0].strip().lower()
        if name_lower not in seen_names:
            seen_names.add(name_lower)
            result.append({
                "name": u[0],
                "email": u[1] or "",
                "phone": u[2] or ""
            })

    print("Sending user cache JSON:", result)
    return jsonify(result)







# ================================
# Helper Functions
# ================================

def calculate_activity_survey_rating(activity_id):
    """
    Calculate the average survey rating for an activity based on completed survey responses.
    Returns tuple (average_rating, total_responses) or (None, 0) if no data available.
    """
    try:
        # Find all completed survey responses for this activity
        survey_responses = db.session.query(SurveyResponse).join(
            Survey, SurveyResponse.survey_id == Survey.id
        ).filter(
            Survey.activity_id == activity_id,
            SurveyResponse.completed == True
        ).all()

        if not survey_responses:
            return None, 0

        ratings = []
        for response in survey_responses:
            if response.responses:
                try:
                    response_data = json.loads(response.responses)
                    # Look for rating questions (typically 1-5 scale)
                    for question_key, answer in response_data.items():
                        # Handle both numeric and string ratings
                        rating_value = None
                        if isinstance(answer, (int, float)) and 1 <= answer <= 5:
                            rating_value = float(answer)
                        elif isinstance(answer, str) and answer.replace('.', '', 1).isdigit():
                            try:
                                rating_value = float(answer)
                                if not (1 <= rating_value <= 5):
                                    rating_value = None
                            except ValueError:
                                rating_value = None

                        if rating_value is not None:
                            ratings.append(rating_value)
                            break  # Take first rating found per response
                except (json.JSONDecodeError, ValueError):
                    continue

        if not ratings:
            return None, len(survey_responses)

        average_rating = sum(ratings) / len(ratings)
        return round(average_rating, 1), len(ratings)

    except Exception as e:
        print(f"Error calculating survey rating for activity {activity_id}: {e}")
        return None, 0


@app.route("/change-password", methods=["POST"])
def change_password():
    if "admin" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": "Both current and new password are required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400

    admin = Admin.query.filter_by(email=session["admin"]).first()
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    stored_hash = admin.password_hash
    if isinstance(stored_hash, bytes):
        stored_hash = stored_hash.decode()

    if not bcrypt.checkpw(current_password.encode(), stored_hash.encode()):
        return jsonify({"error": "Current password is incorrect"}), 403

    admin.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    db.session.commit()

    return jsonify({"success": True, "message": "Password changed successfully"})


@app.route("/reset-admin-password/<int:admin_id>", methods=["POST"])
def reset_admin_password(admin_id):
    if "admin" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    current_admin = Admin.query.filter_by(email=session["admin"]).first()
    if not current_admin:
        return jsonify({"error": "Admin not found"}), 404

    target_admin = Admin.query.get(admin_id)
    if not target_admin:
        return jsonify({"error": "Target admin not found"}), 404

    if target_admin.id == current_admin.id:
        return jsonify({"error": "Use Change Password for your own account"}), 400

    alphabet = string.ascii_letters + string.digits + string.punctuation
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))

    target_admin.password_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()
    db.session.commit()

    return jsonify({"success": True, "temp_password": temp_password})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        print(f"📨 Login attempt for: {email}")
        print(f"🔑 Password entered: {password}")

        with app.app_context():
            admin = Admin.query.filter_by(email=email).first()

        if not admin:
            print("No admin found with that email.")
        else:
            print(f"Admin found: {admin.email}")
            print(f"🔐 Stored hash (type): {type(admin.password_hash)}")
            print(f"🔐 Stored hash (value): {admin.password_hash}")

            try:
                stored_hash = admin.password_hash
                if isinstance(stored_hash, bytes):
                    stored_hash = stored_hash.decode()

                if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                    print("Password matched.")
                    session["admin"] = email
                    return redirect(url_for("dashboard"))
                else:
                    print("Password does NOT match.")
            except Exception as e:
                print("💥 Exception during bcrypt check:", e)

        flash("Invalid login!", "error")
        return redirect(url_for("login"))

    return render_template("login_standalone.html")





@app.route("/pass/<pass_code>")
def show_pass(pass_code):
    from models import Passport

    hockey_pass = Passport.query.filter_by(pass_code=pass_code).first()

    if not hockey_pass:
        return "Pass not found", 404

    # ✅ Generate QR code
    qr_image_io = generate_qr_code_image(pass_code)
    qr_data = base64.b64encode(qr_image_io.read()).decode()

    # ✅ Pass fallback admin email for correct "Par" display
    history = get_pass_history_data(pass_code, fallback_admin_email=session.get("admin"))

    # ✅ Check if admin is logged in
    is_admin = "admin" in session

    # ✅ Load system settings
    settings_raw = {s.key: s.value for s in Setting.query.all()}

    # ✅ Render payment instructions
    email_info_rendered = render_template_string(
        settings_raw.get("EMAIL_INFO_TEXT", ""),
        hockey_pass=hockey_pass
    )

    return render_template(
        "pass.html",
        hockey_pass=hockey_pass,
        qr_data=qr_data,
        history=history,
        is_admin=is_admin,
        settings=settings_raw,
        email_info=email_info_rendered
    )




@app.route("/redeem-qr/<pass_code>", methods=["POST"])
def redeem_passport_qr(pass_code):
    from models import Passport, Redemption, AdminActionLog
    from utils import notify_pass_event
    from datetime import datetime, timezone, timedelta
    import time

    if "admin" not in session:
        return redirect(url_for("login"))

    now_utc = datetime.now(timezone.utc)

    passport = Passport.query.filter_by(pass_code=pass_code).first()
    if not passport:
        flash("Passport not found!", "error")
        return redirect(url_for("dashboard"))

    # 🛡️ Prevent duplicate redemptions (double-click protection)
    global recent_redemptions
    admin_id = session.get("admin", "unknown")
    throttle_key = f"{passport.id}_{admin_id}"

    # Check in-memory cache for recent redemptions (last 5 seconds)
    if throttle_key in recent_redemptions:
        last_redemption_time = recent_redemptions[throttle_key]
        if (now_utc - last_redemption_time).total_seconds() < 5:
            flash("Redemption already in progress. Please wait.", "warning")
            return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))

    # Check database for recent redemptions (last 10 seconds) for persistent protection
    five_seconds_ago = now_utc - timedelta(seconds=10)
    recent_db_redemption = Redemption.query.filter_by(
        passport_id=passport.id
    ).filter(
        Redemption.date_used >= five_seconds_ago
    ).first()

    if recent_db_redemption:
        flash("This passport was recently redeemed. Please refresh the page.", "warning")
        return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))

    # Record this redemption attempt in memory cache
    recent_redemptions[throttle_key] = now_utc

    # Clean up old entries from memory cache (keep only last 30 seconds)
    cutoff_time = now_utc - timedelta(seconds=30)
    recent_redemptions = {k: v for k, v in recent_redemptions.items() if v > cutoff_time}

    if passport.uses_remaining > 0:
        passport.uses_remaining -= 1
        db.session.add(passport)

        # ✅ Save Redemption
        redemption = Redemption(
            passport_id=passport.id,
            date_used=now_utc,
            redeemed_by=session.get("admin", "unknown")
        )
        db.session.add(redemption)
        db.session.commit()

        # ✅ Log Admin Action BEFORE sending email
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Passport {passport.pass_code} redeemed by QR scan."
        ))
        db.session.commit()

        # ✅ Sleep 0.5 seconds for natural separation
        time.sleep(0.5)

        # ✅ Fresh now_utc after sleep
        now_utc = datetime.now(timezone.utc)

        # ✅ Send confirmation email AFTER admin log
        notify_pass_event(
            app=current_app._get_current_object(),
            event_type="pass_redeemed",
            pass_data=passport,
            activity=passport.activity,
            admin_email=session.get("admin"),
            timestamp=now_utc
        )

        flash(f"Passport {passport.pass_code} redeemed via QR scan!", "success")

        # Check if passport is now empty and activity offers renewal
        if passport.uses_remaining == 0:
            activity = passport.activity
            passport_type = passport.passport_type
            if (activity.offer_passport_renewal
                    and passport_type
                    and passport_type.status == 'active'):
                session['renewal_prompt'] = {
                    'pass_code': passport.pass_code,
                    'user_name': passport.user.name if passport.user else 'Unknown',
                    'activity_name': activity.name,
                    'passport_type_name': passport_type.name,
                    'sessions': passport_type.sessions_included,
                    'price': passport_type.price_per_user,
                }
    else:
        flash("No uses left on this passport!", "error")

    return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))






@app.route("/edit-passport/<int:passport_id>", methods=["GET", "POST"])
def edit_passport(passport_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Passport, Activity

    passport = db.session.get(Passport, passport_id)
    if not passport:
        flash("Passport not found.", "error")
        return redirect(url_for("dashboard2"))

    if request.method == "POST":
        # Update passport fields
        passport.sold_amt = float(request.form.get("sold_amt", passport.sold_amt))
        passport.uses_remaining = int(request.form.get("uses_remaining", passport.uses_remaining))
        passport.paid = "paid_ind" in request.form
        passport.notes = request.form.get("notes", passport.notes).strip()
        
        # Update user information
        user_name = request.form.get("user_name", "").strip()
        user_email = request.form.get("user_email", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        
        if passport.user:
            passport.user.name = user_name
            passport.user.email = user_email
            passport.user.phone_number = phone_number
        
        # Handle passport type update
        passport_type_id = request.form.get("passport_type_id")
        if passport_type_id and passport_type_id != "":
            passport.passport_type_id = int(passport_type_id)
            # Update passport type name
            from models import PassportType
            passport_type = db.session.get(PassportType, passport.passport_type_id)
            if passport_type:
                passport.passport_type_name = passport_type.name
        else:
            passport.passport_type_id = None
            passport.passport_type_name = None

        db.session.commit()

        # Log admin action for audit trail
        from models import AdminActionLog
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Passport for {passport.user.name if passport.user else 'Unknown'} ({passport.pass_code}) edited by {session.get('admin', 'unknown')}"
        ))
        db.session.commit()

        flash("Passport updated successfully.", "success")
        return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))

    # 🟢 FIX: fetch activities and pass to template
    activity_list = Activity.query.filter_by(status='active').order_by(Activity.name).all()
    
    # Load passport types for the passport's activity
    from models import PassportType
    passport_types = PassportType.query.filter_by(activity_id=passport.activity_id, status='active').all()

    return render_template(
        "passport_form.html",
        passport=passport,
        activity_list=activity_list,
        passport_types=passport_types,
        selected_activity_id=passport.activity_id
    )




@app.route("/scan-qr")
def scan_qr():
    return render_template("scan_qr.html")




@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))



 

@app.route("/activity-log")
def activity_log():
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import get_all_activity_logs
    logs = get_all_activity_logs()

    return render_template("activity_log.html", logs=logs)




@app.route("/tier-limit-exceeded")
def tier_limit_exceeded():
    """Blocking page when user has exceeded their activity limit."""
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Activity

    # Check if they're actually over the limit
    is_over, excess, message = is_over_activity_limit()

    # If they're not over limit anymore, redirect to dashboard
    if not is_over:
        flash('You are now within your tier limit. Welcome back!', 'success')
        return redirect(url_for("dashboard"))

    # Get all active activities so user can choose which to archive
    active_activities = Activity.query.filter_by(status='active').all()

    tier_info = get_tier_info()
    current_count = count_active_activities()

    return render_template(
        "tier_limit_exceeded.html",
        message=message,
        excess=excess,
        active_activities=active_activities,
        tier_info=tier_info,
        current_count=current_count
    )


@app.route("/archive-activity-from-limit/<int:activity_id>", methods=["POST"])
def archive_activity_from_limit(activity_id):
    """Archive activity from tier limit exceeded page and redirect back to check limit."""
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Activity, db

    activity = db.session.get(Activity, activity_id)

    if not activity:
        flash("Activity not found.", "error")
        return redirect(url_for("tier_limit_exceeded"))

    # Archive the activity
    activity.status = 'inactive'
    db.session.commit()

    flash(f'Activity "{activity.name}" has been archived.', 'success')

    # Redirect back to tier_limit_exceeded which will auto-redirect to dashboard if now within limit
    return redirect(url_for("tier_limit_exceeded"))


@app.route("/activities")
def list_activities():
    if "admin" not in session:
        return redirect(url_for("login"))

    # CHECK IF USER IS OVER THEIR TIER LIMIT
    is_over, excess, message = is_over_activity_limit()
    if is_over:
        return redirect(url_for("tier_limit_exceeded"))

    # Get filter parameters
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    activity_type = request.args.get("type", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    show_all_param = request.args.get("show_all", "")

    # Default to 'active' filter if no status specified (unless explicitly showing all)
    if not status and show_all_param != "true":
        status = "active"

    # Query ALL activities first for statistics (before any filters)
    all_activities = Activity.query.options(
        db.joinedload(Activity.passports),
        db.joinedload(Activity.passport_types)
    ).all()

    # Calculate TRUE total activities count for "All" button
    all_activities_count = Activity.query.count()

    # Calculate statistics using ALL activities (not filtered results)
    active_activities = len([a for a in all_activities if a.status == 'active'])
    inactive_activities = len([a for a in all_activities if a.status != 'active'])

    # Create statistics dict to pass to template
    statistics = {
        'total_activities': all_activities_count,
        'active_activities': active_activities,
        'inactive_activities': inactive_activities,
    }

    # Base query with eager loading for performance
    query = Activity.query.options(
        db.joinedload(Activity.passports),
        db.joinedload(Activity.passport_types)
    ).order_by(Activity.created_dt.desc())

    # Apply filters
    if q:
        query = query.filter(
            db.or_(
                Activity.name.ilike(f"%{q}%"),
                Activity.description.ilike(f"%{q}%"),
                Activity.type.ilike(f"%{q}%")
            )
        )

    if status:
        if status == 'not_active':
            query = query.filter(Activity.status != 'active')
        else:
            query = query.filter(Activity.status == status)

    if activity_type:
        query = query.filter(Activity.type.ilike(f"%{activity_type}%"))

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Activity.start_date >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Activity.end_date <= end_dt)
        except ValueError:
            pass

    activities = query.all()

    # Determine if showing all (explicitly requested)
    show_all = show_all_param == "true"

    # Get revenue from SQL view for consistency with Financial Report
    from utils import get_activity_revenue_from_view
    activity_revenue = get_activity_revenue_from_view()

    # Calculate statistics for each activity
    for activity in activities:
        activity.signup_count = len([p for p in activity.passports if p.paid])
        activity.total_revenue = activity_revenue.get(activity.id, 0)
        activity.passport_types_count = len(activity.passport_types)
        activity.active_passports_count = len([p for p in activity.passports if p.paid and p.uses_remaining > 0])

    # Get unique activity types for filter dropdown
    activity_types = db.session.query(Activity.type).distinct().filter(Activity.type.isnot(None)).all()
    activity_types = [t[0] for t in activity_types if t[0]]

    # Determine empty state type
    is_first_time_empty = all_activities_count == 0
    is_zero_results = len(activities) == 0 and not is_first_time_empty

    return render_template("activities.html",
                         activities=activities,
                         activity_types=activity_types,
                         statistics=statistics,
                         is_first_time_empty=is_first_time_empty,
                         is_zero_results=is_zero_results,
                         current_filters={
                             'q': q,
                             'status': status,
                             'type': activity_type,
                             'start_date': start_date,
                             'end_date': end_date,
                             'show_all': show_all
                         })


@app.route("/surveys")
def list_surveys():
    if "admin" not in session:
        return redirect(url_for("login"))

    # Get filter parameters
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    show_all_param = request.args.get("show_all", "")
    activity_id = request.args.get("activity", "")
    template_id = request.args.get("template", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    # Default to 'active' filter if no status specified (unless explicitly showing all)
    if not status and show_all_param != "true":
        status = "active"

    # Base query with eager loading for performance
    query = Survey.query.options(
        db.joinedload(Survey.activity),
        db.joinedload(Survey.template),
        db.joinedload(Survey.passport_type),
        db.joinedload(Survey.responses)
    ).order_by(Survey.created_dt.desc())

    # Apply filters
    if q:
        query = query.filter(
            db.or_(
                Survey.name.ilike(f"%{q}%"),
                Survey.description.ilike(f"%{q}%")
            )
        )
    
    if status:
        query = query.filter(Survey.status == status)
    
    if activity_id:
        query = query.filter(Survey.activity_id == activity_id)
        
    if template_id:
        query = query.filter(Survey.template_id == template_id)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Survey.created_dt >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Survey.created_dt <= end_dt)
        except ValueError:
            pass

    # Calculate TRUE statistics BEFORE filters (for filter button counts)
    all_surveys = Survey.query.all()
    total_surveys_count = len(all_surveys)
    active_surveys_count = len([s for s in all_surveys if s.status == 'active'])
    closed_surveys_count = len([s for s in all_surveys if s.status == 'closed'])

    # NOW apply filters to get the displayed surveys
    surveys = query.all()

    # Get activities and templates for filter dropdowns
    activities = Activity.query.filter_by(status='active').order_by(Activity.name).all()
    survey_templates = SurveyTemplate.query.order_by(SurveyTemplate.name).all()

    # Calculate KPI statistics for displayed surveys only
    total_surveys = len(surveys)
    active_surveys = len([s for s in surveys if s.status == 'active'])
    inactive_surveys = total_surveys - active_surveys
    
    # Calculate proper completion rates based on invitations sent vs completed
    total_invitations = sum(len([r for r in s.responses if r.invited_dt]) for s in surveys)
    completed_responses = sum(len([r for r in s.responses if r.completed]) for s in surveys)
    avg_completion_rate = (completed_responses / total_invitations * 100) if total_invitations > 0 else 0
    
    # Calculate statistics for each survey
    for survey in surveys:
        survey.invitation_count = len([r for r in survey.responses if r.invited_dt])  # Invited users
        survey.response_count = len([r for r in survey.responses if r.started_dt])    # Users who started
        survey.completed_count = len([r for r in survey.responses if r.completed])   # Users who completed
        survey.completion_rate = (survey.completed_count / survey.invitation_count * 100) if survey.invitation_count > 0 else 0
    
    statistics = {
        'total_surveys': total_surveys_count,  # TRUE total for filter button
        'active_surveys': active_surveys_count,  # TRUE active count for filter button
        'closed_surveys': closed_surveys_count,  # TRUE closed count for filter button
        'inactive_surveys': inactive_surveys,
        'total_invitations': total_invitations,
        'total_responses': completed_responses,  # Keep this for compatibility
        'completed_responses': completed_responses,
        'avg_completion_rate': avg_completion_rate
    }

    # Determine empty state type
    is_first_time_empty = total_surveys_count == 0
    is_zero_results = len(surveys) == 0 and not is_first_time_empty

    return render_template("surveys.html",
                         surveys=surveys,
                         activities=activities,
                         survey_templates=survey_templates,
                         statistics=statistics,
                         is_first_time_empty=is_first_time_empty,
                         is_zero_results=is_zero_results,
                         current_filters={
                             'q': q,
                             'status': status,
                             'show_all': show_all_param == "true",
                             'activity': activity_id,
                             'template': template_id,
                             'start_date': start_date,
                             'end_date': end_date
                         })


@app.route("/passports")
def list_passports():
    if "admin" not in session:
        return redirect(url_for("login"))

    # Get filter parameters
    q = request.args.get("q", "").strip()
    activity_id = request.args.get("activity", "")
    payment_status = request.args.get("payment_status", "")
    status = request.args.get("status", "")
    show_all_param = request.args.get("show_all", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    min_amount = request.args.get("min_amount", "")
    max_amount = request.args.get("max_amount", "")

    # Default to 'active' filter if no status or payment_status specified (unless explicitly showing all)
    if not status and not payment_status and show_all_param != "true":
        status = "active"

    # Base query with eager loading for performance
    query = Passport.query.options(
        db.joinedload(Passport.user),
        db.joinedload(Passport.activity),
        db.joinedload(Passport.passport_type)
    ).order_by(Passport.created_dt.desc())

    # Calculate TRUE total passports (before any filters) for "All" button
    all_passports_count = Passport.query.count()

    # Apply filters
    if q:
        query = query.join(User).filter(
            db.or_(
                User.name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
                Passport.pass_code.ilike(f"%{q}%"),
                Passport.notes.ilike(f"%{q}%")
            )
        )

    if activity_id:
        query = query.filter(Passport.activity_id == activity_id)

    # Status filter for "active" (has remaining uses OR unpaid)
    if status == "active":
        query = query.filter(
            db.or_(
                Passport.uses_remaining > 0,
                Passport.paid == False
            )
        )
    elif payment_status == "paid":
        query = query.filter(Passport.paid == True)
    elif payment_status == "unpaid":
        query = query.filter(Passport.paid == False)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Passport.created_dt >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Passport.created_dt <= end_dt)
        except ValueError:
            pass
    
    if min_amount:
        try:
            min_amt = float(min_amount)
            query = query.filter(Passport.sold_amt >= min_amt)
        except ValueError:
            pass
    
    if max_amount:
        try:
            max_amt = float(max_amount)
            query = query.filter(Passport.sold_amt <= max_amt)
        except ValueError:
            pass

    passports = query.all()

    # Get activities for filter dropdown
    activities = Activity.query.filter_by(status='active').order_by(Activity.name).all()

    # Get all passports for statistics (unfiltered counts)
    all_passports = Passport.query.all()

    # Calculate statistics using ALL passports (not filtered results)
    paid_passports = len([p for p in all_passports if p.paid])
    unpaid_passports = len([p for p in all_passports if not p.paid])
    # Active = has remaining uses OR unpaid
    active_passports = len([p for p in all_passports if p.uses_remaining > 0 or not p.paid])
    total_revenue = sum(p.sold_amt for p in all_passports if p.paid)
    pending_revenue = sum(p.sold_amt for p in all_passports if not p.paid)

    statistics = {
        'total_passports': all_passports_count,
        'paid_passports': paid_passports,
        'unpaid_passports': unpaid_passports,
        'active_passports': active_passports,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue
    }

    # Determine if showing all (explicitly requested)
    show_all = show_all_param == "true"

    # Determine empty state type
    is_first_time_empty = all_passports_count == 0
    is_zero_results = len(passports) == 0 and not is_first_time_empty

    return render_template("passports.html",
                         passports=passports,
                         activities=activities,
                         statistics=statistics,
                         is_first_time_empty=is_first_time_empty,
                         is_zero_results=is_zero_results,
                         current_filters={
                             'q': q,
                             'activity': activity_id,
                             'payment_status': payment_status,
                             'status': status,
                             'start_date': start_date,
                             'end_date': end_date,
                             'min_amount': min_amount,
                             'max_amount': max_amount,
                             'show_all': show_all
                         })


# ================================
# 📊 FINANCIAL REPORTING ROUTES
# ================================

@app.route("/reports/financial")
def financial_report():
    """Display comprehensive financial report with income, expenses, and activity breakdown"""
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import get_financial_data_from_views, get_fiscal_year_range, get_fiscal_year_display

    # Get period filter (default to fiscal year)
    period = request.args.get('period', 'fy')

    # Calculate date range based on period
    start_date = None
    end_date = None
    period_display = "All Time"

    if period == 'fy':
        fy_start, fy_end = get_fiscal_year_range()
        start_date = fy_start.strftime('%Y-%m-%d')
        end_date = fy_end.strftime('%Y-%m-%d')
        period_display = get_fiscal_year_display()
    elif period == 'all':
        start_date = None
        end_date = None
        period_display = "All Time"

    # Get financial data with date filters
    financial_data = get_financial_data_from_views(start_date=start_date, end_date=end_date, activity_filter=None)

    # Get all activities for the drawer form
    activities = Activity.query.order_by(Activity.name).all()

    # Determine empty state type based on total income records
    total_records = len(financial_data.get('by_activity', []))
    is_first_time_empty = total_records == 0
    is_zero_results = False  # Financial page doesn't have filters currently

    return render_template("financial_report.html",
                         financial_data=financial_data,
                         activities=activities,
                         is_first_time_empty=is_first_time_empty,
                         is_zero_results=is_zero_results,
                         current_period=period,
                         period_display=period_display)


def generate_smart_filename(source_type, record_id, date, amount, original_filename):
    """
    Generate smart filename for ZIP export: {TYPE}-{ID}_{DATE}_{AMOUNT}_{original}.{ext}
    Example: INCOME-42_2025-01-15_150_00_receipt.jpg
    """
    import re
    from werkzeug.utils import secure_filename

    # Extract extension
    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'file'

    # Extract original base name (remove UUID prefix if present)
    original_base = original_filename.rsplit('.', 1)[0]
    original_base = re.sub(r'^(income|expense)_[a-f0-9]{32}', '', original_base)
    if not original_base:
        original_base = 'receipt'
    original_base = secure_filename(original_base) or 'receipt'

    # Format date
    if hasattr(date, 'strftime'):
        date_str = date.strftime('%Y-%m-%d')
    else:
        date_str = str(date).split()[0]

    # Format amount (replace . with _ for filename safety)
    amount_str = f"{float(amount):.2f}".replace('.', '_')

    # Build filename
    type_prefix = source_type.upper()
    return f"{type_prefix}-{record_id}_{date_str}_{amount_str}_{original_base}.{ext}"


@app.route("/reports/financial/export")
def financial_report_export():
    """Export financial report in various formats (CSV, IIF, XLSX)"""
    if "admin" not in session:
        return redirect(url_for("login"))

    from flask import Response
    from datetime import datetime
    from sqlalchemy import text
    import csv
    from io import StringIO

    export_format = request.args.get("format", "csv")

    # Get period parameter (supports 'fy' for fiscal year, 'all' for all time)
    period = request.args.get('period', 'fy')

    # Get date range parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    activity_filter = request.args.get('activity_filter')

    # If period is specified but not explicit dates, calculate from period
    if period == 'fy' and not start_date and not end_date:
        from utils import get_fiscal_year_range
        fy_start, fy_end = get_fiscal_year_range()
        start_date = fy_start.strftime('%Y-%m-%d')
        end_date = fy_end.strftime('%Y-%m-%d')
    elif period == 'all':
        start_date = None
        end_date = None

    # Generate filename
    if start_date and end_date:
        base_filename = f"financial_report_{start_date}_to_{end_date}"
    else:
        base_filename = "financial_report_all_time"

    if export_format == "zip":
        filename = f"{base_filename}_with_docs.zip"
    else:
        filename = f"{base_filename}.{export_format}"

    # Export based on format
    if export_format == "csv":
        # Query view directly for CSV export (exact structure)
        query = """
            SELECT
                month,
                project,
                transaction_type,
                transaction_date,
                customer,
                memo,
                amount,
                payment_status,
                entered_by
            FROM monthly_transactions_detail
            WHERE 1=1
        """

        params = {}

        # Add date filters if provided
        if start_date:
            query += " AND transaction_date >= :start_date"
            params['start_date'] = start_date
        if end_date:
            query += " AND transaction_date <= :end_date"
            params['end_date'] = end_date

        # Add activity filter if provided
        if activity_filter:
            activity = Activity.query.get(int(activity_filter))
            if activity:
                query += " AND project = :activity_name"
                params['activity_name'] = activity.name

        # Order by date descending
        query += " ORDER BY transaction_date DESC"

        # Execute query
        result = db.session.execute(text(query), params)

        # Create CSV with exact view column names
        output = StringIO()
        writer = csv.writer(output)

        # Write header (exact view column names)
        writer.writerow([
            'month',
            'project',
            'transaction_type',
            'transaction_date',
            'customer',
            'memo',
            'amount',
            'payment_status',
            'entered_by'
        ])

        # Write data
        for row in result:
            writer.writerow([
                row.month,
                row.project,
                row.transaction_type,
                row.transaction_date,
                row.customer or '',
                row.memo or '',
                f"{row.amount:.2f}",
                row.payment_status,
                row.entered_by or ''
            ])

        csv_content = output.getvalue()
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif export_format == "zip":
        # ZIP export with all documents (exports ALL data, ignores filters)
        from io import BytesIO
        from zipfile import ZipFile
        import os

        # Query ALL transactions (Passport sales + Income + Expense) with receipt info
        # Matches the monthly_transactions_detail view structure
        zip_query = """
            SELECT
                strftime('%Y-%m', COALESCE(p.paid_date, p.created_dt)) as month,
                a.name as project,
                'Income' as transaction_type,
                COALESCE(p.paid_date, p.created_dt) as transaction_date,
                u.name as customer,
                p.notes as memo,
                p.sold_amt as amount,
                CASE WHEN p.paid = 1 THEN 'Paid' ELSE 'Unpaid (AR)' END as payment_status,
                'Passport System' as entered_by,
                NULL as record_id,
                'passport' as source_type,
                NULL as receipt_filename
            FROM passport p
            JOIN activity a ON p.activity_id = a.id
            LEFT JOIN user u ON p.user_id = u.id

            UNION ALL

            SELECT
                strftime('%Y-%m', i.date) as month,
                a.name as project,
                'Income' as transaction_type,
                i.date as transaction_date,
                NULL as customer,
                i.note as memo,
                i.amount,
                CASE WHEN i.payment_status = 'received' THEN 'Paid' ELSE 'Unpaid (AR)' END as payment_status,
                COALESCE(i.created_by, 'System') as entered_by,
                i.id as record_id,
                'income' as source_type,
                i.receipt_filename
            FROM income i
            JOIN activity a ON i.activity_id = a.id

            UNION ALL

            SELECT
                strftime('%Y-%m', e.date) as month,
                a.name as project,
                'Expense' as transaction_type,
                e.date as transaction_date,
                NULL as customer,
                e.description as memo,
                e.amount,
                CASE WHEN e.payment_status = 'paid' THEN 'Paid' ELSE 'Unpaid (AP)' END as payment_status,
                COALESCE(e.created_by, 'System') as entered_by,
                e.id as record_id,
                'expense' as source_type,
                e.receipt_filename
            FROM expense e
            JOIN activity a ON e.activity_id = a.id

            ORDER BY transaction_date DESC
        """

        # Execute query (no filters - exports everything)
        zip_result = db.session.execute(text(zip_query))

        # Create in-memory ZIP
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zipf:
            # Generate CSV with document_filename column
            csv_output = StringIO()
            writer = csv.writer(csv_output)

            # Write header with document_filename column
            writer.writerow([
                'month',
                'project',
                'transaction_type',
                'transaction_date',
                'customer',
                'memo',
                'amount',
                'payment_status',
                'entered_by',
                'document_filename'
            ])

            documents_added = set()
            receipts_dir = os.path.join(app.static_folder, 'uploads', 'receipts')

            for row in zip_result:
                doc_filename = ''

                if row.receipt_filename:
                    # Generate smart filename
                    doc_filename = generate_smart_filename(
                        source_type=row.source_type,
                        record_id=row.record_id,
                        date=row.transaction_date,
                        amount=row.amount,
                        original_filename=row.receipt_filename
                    )

                    # Add document to ZIP if not already added and file exists
                    if doc_filename not in documents_added:
                        receipt_path = os.path.join(receipts_dir, row.receipt_filename)
                        # Security: verify path is within receipts directory
                        receipt_path = os.path.abspath(receipt_path)
                        if receipt_path.startswith(os.path.abspath(receipts_dir)) and os.path.exists(receipt_path):
                            zipf.write(receipt_path, f'documents/{doc_filename}')
                            documents_added.add(doc_filename)
                        else:
                            # File missing - skip silently, leave doc_filename empty
                            doc_filename = ''

                # Write CSV row
                writer.writerow([
                    row.month,
                    row.project,
                    row.transaction_type,
                    row.transaction_date,
                    row.customer or '',
                    row.memo or '',
                    f"{row.amount:.2f}",
                    row.payment_status,
                    row.entered_by or '',
                    doc_filename
                ])

            # Add CSV to ZIP
            zipf.writestr('financial_report.csv', csv_output.getvalue())

        zip_buffer.seek(0)
        return Response(
            zip_buffer.getvalue(),
            mimetype='application/zip',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    elif export_format == "iif":
        # TODO: Implement QuickBooks IIF export in Phase 2
        flash("QuickBooks IIF export coming soon! Use CSV for now.", "info")
        return redirect(url_for("financial_report"))
    elif export_format == "xlsx":
        # TODO: Implement Excel export in Phase 2
        flash("Excel export coming soon! Use CSV for now.", "info")
        return redirect(url_for("financial_report"))
    else:
        flash("Invalid export format", "error")
        return redirect(url_for("financial_report"))


@app.route("/reports/user-contacts")
def user_contacts_report():
    """Display user contact list with engagement metrics"""
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import get_user_contact_report

    # Get filter parameters
    q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    show_all_param = request.args.get("show_all", "")

    # Set default filter to "active" if no filter specified
    if not status_filter and show_all_param != "true":
        status_filter = "active"

    # Get user contact data with search
    user_data = get_user_contact_report(
        search_query=q,
        status_filter=status_filter,
        show_all=(show_all_param == "true")
    )

    # Calculate statistics for filter counts
    all_users_data = get_user_contact_report(search_query="", status_filter="", show_all=True)
    active_users_data = get_user_contact_report(search_query="", status_filter="active", show_all=False)

    statistics = {
        'total_users': all_users_data['summary']['total_users'],
        'active_users': active_users_data['summary']['active_users'],
    }

    # Determine empty state type
    is_first_time_empty = statistics['total_users'] == 0
    is_zero_results = len(user_data['users']) == 0 and not is_first_time_empty

    # Current filter state
    current_filters = {
        'q': q,
        'status': status_filter,
        'show_all': show_all_param == "true"
    }

    return render_template("user_contacts_report.html",
                         users=user_data['users'],
                         statistics=statistics,
                         is_first_time_empty=is_first_time_empty,
                         is_zero_results=is_zero_results,
                         current_filters=current_filters)


@app.route("/reports/user-contacts/export")
def user_contacts_export():
    """Export user contact list in CSV format - RAW data (one row per passport)"""
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import export_user_contacts_raw_csv
    from datetime import datetime, timezone
    from flask import Response

    # Get search filter (if any)
    q = request.args.get("q", "").strip()

    # Generate filename
    now = datetime.now(timezone.utc)
    search_part = f"_search_{q[:20]}" if q else ""
    filename = f"user_contacts_raw{search_part}_{now.strftime('%Y-%m-%d')}.csv"

    # Export raw passport data to CSV
    csv_content = export_user_contacts_raw_csv(search_query=q)

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/payment-bot-matches")
def payment_bot_matches():
    """Display all payment bot activity with deduplication and filtering"""
    if "admin" not in session:
        return redirect(url_for("login"))

    # Get filter parameters
    q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    show_all_param = request.args.get("show_all", "")
    page = request.args.get("page", 1, type=int)
    per_page = 50

    # Set default filter to 'no_match' if no filter specified
    if not status_filter and show_all_param != "true":
        status_filter = "no_match"

    # Subquery to get latest ID for each unique payment (deduplication)
    latest_payment_ids = db.session.query(
        db.func.max(EbankPayment.id).label('max_id')
    ).group_by(
        EbankPayment.bank_info_name,
        EbankPayment.bank_info_amt,
        EbankPayment.from_email
    ).subquery()

    # Base query with deduplication
    # Sort by email_received_date if available, fallback to timestamp
    query = db.session.query(EbankPayment).filter(
        EbankPayment.id.in_(
            db.session.query(latest_payment_ids.c.max_id)
        )
    ).order_by(
        db.case(
            (EbankPayment.email_received_date.isnot(None), EbankPayment.email_received_date),
            else_=EbankPayment.timestamp
        ).desc()
    )

    # Apply status filter (skip if show_all is true)
    if show_all_param != "true":
        if status_filter == "no_match":
            query = query.filter(EbankPayment.result == 'NO_MATCH')
        elif status_filter == "matched":
            query = query.filter(EbankPayment.result == 'MATCHED')
        elif status_filter == "manual":
            query = query.filter(EbankPayment.result == 'MANUAL_PROCESSED')

    # Apply search filter (name and amount only, not email)
    if q:
        query = query.filter(
            db.or_(
                EbankPayment.bank_info_name.ilike(f"%{q}%"),
                db.cast(EbankPayment.bank_info_amt, db.String).ilike(f"%{q}%")
            )
        )

    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    payments = pagination.items

    # Get unpaid passport counts by amount for NO_MATCH payments
    # Use a single query to get counts for all amounts in current page
    no_match_amounts = set(p.bank_info_amt for p in payments if p.result == 'NO_MATCH' and p.bank_info_amt)
    unpaid_counts_by_amount = {}
    if no_match_amounts:
        unpaid_counts = db.session.query(
            Passport.sold_amt,
            db.func.count(Passport.id)
        ).filter(
            Passport.paid == False,
            Passport.sold_amt.in_(no_match_amounts)
        ).group_by(Passport.sold_amt).all()
        unpaid_counts_by_amount = {amt: count for amt, count in unpaid_counts}

    # Add unpaid_count attribute to each payment for template access
    for payment in payments:
        if payment.result == 'NO_MATCH' and payment.bank_info_amt:
            payment.unpaid_count = unpaid_counts_by_amount.get(payment.bank_info_amt, 0)
        else:
            payment.unpaid_count = 0

    # Calculate statistics from ALL records (not filtered)
    total_payments = db.session.query(EbankPayment.id).filter(
        EbankPayment.id.in_(db.session.query(latest_payment_ids.c.max_id))
    ).count()
    no_match_count = db.session.query(EbankPayment.id).filter(
        EbankPayment.result == 'NO_MATCH',
        EbankPayment.id.in_(db.session.query(latest_payment_ids.c.max_id))
    ).count()
    matched_count = db.session.query(EbankPayment.id).filter(
        EbankPayment.result == 'MATCHED',
        EbankPayment.id.in_(db.session.query(latest_payment_ids.c.max_id))
    ).count()
    manual_count = db.session.query(EbankPayment.id).filter(
        EbankPayment.result == 'MANUAL_PROCESSED',
        EbankPayment.id.in_(db.session.query(latest_payment_ids.c.max_id))
    ).count()

    statistics = {
        'total_payments': total_payments,
        'no_match_count': no_match_count,
        'matched_count': matched_count,
        'manual_count': manual_count
    }

    # Determine empty state type
    is_first_time_empty = total_payments == 0
    is_zero_results = len(payments) == 0 and not is_first_time_empty

    # Get active activities for the Create Passport modal
    activities = Activity.query.filter_by(status='active').order_by(Activity.name).all()

    return render_template("payment_bot_matches.html",
                         payments=payments,
                         pagination=pagination,
                         statistics=statistics,
                         is_first_time_empty=is_first_time_empty,
                         is_zero_results=is_zero_results,
                         activities=activities,
                         current_filters={
                             'q': q,
                             'status': status_filter,
                             'show_all': show_all_param == "true"
                         })


@app.route("/passports/bulk-action", methods=["POST"])
def passports_bulk_action():
    if "admin" not in session:
        return redirect(url_for("login"))
    
    action = request.form.get("action")
    # Handle both parameter names for backward compatibility
    passport_ids = request.form.getlist("passport_ids[]") or request.form.getlist("selected_passports")
    
    if not passport_ids:
        flash("No passports selected.", "error")
        return redirect(url_for("list_passports"))
    
    passports = Passport.query.filter(Passport.id.in_(passport_ids)).all()
    
    if action == "mark_paid":
        count = 0
        paid_passports = []  # Track passports for notifications
        for passport in passports:
            if not passport.paid:
                passport.paid = True
                passport.paid_date = datetime.now(timezone.utc)
                passport.marked_paid_by = session.get("admin", "unknown")
                paid_passports.append(passport)
                count += 1
        
        db.session.commit()
        
        # SSE notifications removed for leaner performance
        
        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Bulk marked {count} passports as paid by {session.get('admin', 'unknown')}"
        ))
        db.session.commit()
        
        flash(f"Marked {count} passports as paid.", "success")
    
    elif action == "send_reminders":
        count = 0
        for passport in passports:
            if not passport.paid:
                # Send payment reminder email
                notify_pass_event(
                    app=current_app._get_current_object(),
                    event_type="payment_late",
                    pass_data=passport,
                    activity=passport.activity,
                    admin_email=session.get("admin"),
                    timestamp=datetime.now(timezone.utc)
                )
                count += 1
        
        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Sent payment reminders to {count} unpaid passports by {session.get('admin', 'unknown')}"
        ))
        db.session.commit()
        
        flash(f"Sent payment reminders to {count} unpaid passports.", "success")
    
    elif action == "delete":
        count = len(passports)
        # Collect passport details before deletion
        # Note: Associated redemptions will be auto-deleted via CASCADE DELETE
        passport_info = []
        for passport in passports:
            user_name = passport.user.name if passport.user else "Unknown User"
            activity_name = passport.activity.name if passport.activity else "Unknown Activity"
            passport_info.append(f"{user_name} - {activity_name}")
            db.session.delete(passport)  # CASCADE will delete redemptions

        db.session.commit()

        # Log admin action with detailed information
        passport_word = "passport" if count == 1 else "passports"
        details = ', '.join(passport_info[:5])
        if len(passport_info) > 5:
            details += '...'

        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Deleted {count} {passport_word}: {details} by {session.get('admin', 'unknown')}"
        ))
        db.session.commit()

        flash(f"Deleted {count} passports.", "success")

    else:
        flash("Invalid bulk action.", "error")

    # Check if request came from activity dashboard
    activity_id = request.form.get("activity_id")
    if activity_id:
        return redirect(url_for("activity_dashboard", activity_id=activity_id))

    return redirect(url_for("list_passports"))


@app.route("/passports/export")
def export_passports():
    if "admin" not in session:
        return redirect(url_for("login"))
    
    import csv
    import io
    from flask import make_response
    
    # Get all filters from current session
    q = request.args.get("q", "").strip()
    activity_id = request.args.get("activity", "")
    payment_status = request.args.get("payment_status", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    
    # Build the same query as the main passports page
    query = Passport.query.options(
        db.joinedload(Passport.user),
        db.joinedload(Passport.activity),
        db.joinedload(Passport.passport_type)
    ).order_by(Passport.created_dt.desc())
    
    # Apply the same filters
    if q:
        query = query.join(User).filter(
            db.or_(
                User.name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
                Passport.pass_code.ilike(f"%{q}%")
            )
        )
    
    if activity_id:
        query = query.filter(Passport.activity_id == activity_id)
    
    if payment_status == "paid":
        query = query.filter(Passport.paid == True)
    elif payment_status == "unpaid":
        query = query.filter(Passport.paid == False)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Passport.created_dt >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Passport.created_dt <= end_dt)
        except ValueError:
            pass
    
    passports = query.all()
    
    # Create CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        'Passport Code', 'User Name', 'User Email', 'Activity', 'Passport Type',
        'Amount', 'Payment Status', 'Uses Remaining', 'Created Date', 'Paid Date', 'Notes'
    ])
    
    # Data rows
    for passport in passports:
        writer.writerow([
            passport.pass_code,
            passport.user.name if passport.user else '-',
            passport.user.email if passport.user else '-',
            passport.activity.name if passport.activity else '-',
            passport.passport_type.name if passport.passport_type else '-',
            passport.sold_amt,
            'Paid' if passport.paid else 'Unpaid',
            passport.uses_remaining,
            passport.created_dt.strftime('%Y-%m-%d %H:%M') if passport.created_dt else '-',
            passport.paid_date.strftime('%Y-%m-%d %H:%M') if passport.paid_date else '-',
            passport.notes or ''
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=passports_export_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    
    # Log admin action
    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=f"Exported {len(passports)} passports to CSV by {session.get('admin', 'unknown')}"
    ))
    db.session.commit()
    
    return response


@app.route("/admin/activity-income/<int:activity_id>", methods=["GET", "POST"])
@app.route("/admin/activity-income/<int:activity_id>/edit/<int:income_id>", methods=["GET", "POST"])
def activity_income(activity_id, income_id=None):
    activity = Activity.query.get_or_404(activity_id)
    income = db.session.get(Income, income_id) if income_id else None

    income_categories = [
        "Ticket Sales", "Sponsorship", "Donations",
        "Vendor Fees", "Service Income", "Merchandise Sales", "Other"
    ]

    if request.method == "POST":
        is_update = income is not None

        if income:
            # Update existing income
            income.category = request.form.get("category")
            income.amount = request.form.get("amount", type=float)
            income.note = request.form.get("note")
            income.date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")
            # Payment status fields
            income.payment_status = request.form.get("payment_status", "received")
            income.payment_date = datetime.strptime(request.form.get("payment_date"), "%Y-%m-%d") if request.form.get("payment_date") and request.form.get("payment_status") == "received" else None
            income.payment_method = request.form.get("payment_method")
        else:
            # Create new income
            income = Income(
                activity_id=activity.id,
                category=request.form.get("category"),
                amount=request.form.get("amount", type=float),
                note=request.form.get("note"),
                date=datetime.strptime(request.form.get("date"), "%Y-%m-%d"),
                created_by=session.get("admin"),
                # Payment status fields
                payment_status=request.form.get("payment_status", "received"),
                payment_date=datetime.strptime(request.form.get("payment_date"), "%Y-%m-%d") if request.form.get("payment_date") and request.form.get("payment_status") == "received" else None,
                payment_method=request.form.get("payment_method")
            )
            db.session.add(income)

        # Handle receipt deletion if requested
        remove_receipt = request.form.get("remove_receipt") == "true"
        if remove_receipt and income and income.receipt_filename:
            # Delete old receipt file from disk
            old_receipt_path = os.path.join(app.static_folder, "uploads/receipts", income.receipt_filename)
            if os.path.exists(old_receipt_path):
                os.remove(old_receipt_path)
            income.receipt_filename = None

        # Handle file upload
        receipt_file = request.files.get("receipt")
        if receipt_file and receipt_file.filename:
            # Delete old receipt if exists and new one is being uploaded
            if income and income.receipt_filename:
                old_receipt_path = os.path.join(app.static_folder, "uploads/receipts", income.receipt_filename)
                if os.path.exists(old_receipt_path):
                    os.remove(old_receipt_path)

            ext = os.path.splitext(receipt_file.filename)[1]
            filename = f"income_{uuid.uuid4().hex}{ext}"
            receipts_dir = os.path.join(app.static_folder, "uploads/receipts")
            os.makedirs(receipts_dir, exist_ok=True)
            path = os.path.join(receipts_dir, filename)
            receipt_file.save(path)
            income.receipt_filename = filename

        # Log the income operation
        action_type = "Updated" if is_update else "Added"
        log_action = f"{action_type} Income: ${income.amount:.2f} - {income.category} for Activity '{activity.name}'"
        db.session.add(AdminActionLog(
            admin_email=session.get("admin"),
            action=log_action
        ))

        db.session.commit()
        flash("Income saved successfully!", "success")

        # Handle AJAX requests (from financial report drawer)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Income saved successfully',
                'transaction': {
                    'id': income.id,
                    'date': income.date.strftime('%Y-%m-%d'),
                    'category': income.category,
                    'amount': float(income.amount),
                    'description': income.note or income.category,
                    'receipt_filename': income.receipt_filename
                }
            })

        # Check if we should return to activity form or financial report
        return_to = request.form.get('return_to') or request.args.get('return_to')
        if return_to == 'activity_form':
            return redirect(url_for("activity_form", activity_id=activity.id))
        elif return_to == 'financial_report':
            return redirect(url_for("financial_report"))
        else:
            return redirect(url_for("activity_income", activity_id=activity.id))

    incomes = Income.query.filter_by(activity_id=activity.id).order_by(Income.date.desc()).all()
    passport_income = sum(p.sold_amt for p in activity.passports if p.paid)
    other_income = sum(i.amount for i in incomes)

    summary = {
        "passport_income": passport_income,
        "other_income": other_income,
        "total_income": passport_income + other_income
    }

    return render_template("activity_income.html",
        activity=activity,
        income=income,
        incomes=incomes,
        categories=income_categories,
        summary=summary,
        now=dt.now
    )







@app.route("/admin/activity-expenses/<int:activity_id>", methods=["GET", "POST"])
@app.route("/admin/activity-expenses/<int:activity_id>/edit/<int:expense_id>", methods=["GET", "POST"])
def activity_expenses(activity_id, expense_id=None):
    activity = Activity.query.get_or_404(activity_id)
    expense = db.session.get(Expense, expense_id) if expense_id else None

    expense_categories = [
        "Cost of Goods Sold", "Staff", "Venue", "Equipment Rental",
        "Insurance", "Marketing", "Travel", "Supplies", "Other"
    ]

    if request.method == "POST":
        is_update = expense is not None

        if expense:
            # Update
            expense.category = request.form.get("category")
            expense.amount = request.form.get("amount", type=float)
            expense.description = request.form.get("description")
            expense.date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")
            # Payment status fields
            expense.payment_status = request.form.get("payment_status", "paid")
            expense.payment_date = datetime.strptime(request.form.get("payment_date"), "%Y-%m-%d") if request.form.get("payment_date") and request.form.get("payment_status") == "paid" else None
            expense.due_date = datetime.strptime(request.form.get("due_date"), "%Y-%m-%d") if request.form.get("due_date") and request.form.get("payment_status") == "unpaid" else None
            expense.payment_method = request.form.get("payment_method")
        else:
            # Create new
            expense = Expense(
                activity_id=activity.id,
                category=request.form.get("category"),
                amount=request.form.get("amount", type=float),
                description=request.form.get("description"),
                date=datetime.strptime(request.form.get("date"), "%Y-%m-%d"),
                created_by=session.get("admin"),
                # Payment status fields
                payment_status=request.form.get("payment_status", "paid"),
                payment_date=datetime.strptime(request.form.get("payment_date"), "%Y-%m-%d") if request.form.get("payment_date") and request.form.get("payment_status") == "paid" else None,
                due_date=datetime.strptime(request.form.get("due_date"), "%Y-%m-%d") if request.form.get("due_date") and request.form.get("payment_status") == "unpaid" else None,
                payment_method=request.form.get("payment_method")
            )
            db.session.add(expense)

        # Handle receipt deletion if requested
        remove_receipt = request.form.get("remove_receipt") == "true"
        if remove_receipt and expense and expense.receipt_filename:
            # Delete old receipt file from disk
            old_receipt_path = os.path.join(app.static_folder, "uploads/receipts", expense.receipt_filename)
            if os.path.exists(old_receipt_path):
                os.remove(old_receipt_path)
            expense.receipt_filename = None

        # Upload receipt
        receipt_file = request.files.get("receipt")
        if receipt_file and receipt_file.filename:
            # Delete old receipt if exists and new one is being uploaded
            if expense and expense.receipt_filename:
                old_receipt_path = os.path.join(app.static_folder, "uploads/receipts", expense.receipt_filename)
                if os.path.exists(old_receipt_path):
                    os.remove(old_receipt_path)

            ext = os.path.splitext(receipt_file.filename)[1]
            filename = f"expense_{uuid.uuid4().hex}{ext}"
            receipts_dir = os.path.join(app.static_folder, "uploads/receipts")
            os.makedirs(receipts_dir, exist_ok=True)
            path = os.path.join(receipts_dir, filename)
            receipt_file.save(path)
            expense.receipt_filename = filename

        # Log the expense operation
        action_type = "Updated" if is_update else "Added"
        log_action = f"{action_type} Expense: ${expense.amount:.2f} - {expense.category} for Activity '{activity.name}'"
        db.session.add(AdminActionLog(
            admin_email=session.get("admin"),
            action=log_action
        ))

        db.session.commit()
        flash("Expense saved successfully!", "success")

        # Handle AJAX requests (from financial report drawer)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Expense saved successfully',
                'transaction': {
                    'id': expense.id,
                    'date': expense.date.strftime('%Y-%m-%d'),
                    'category': expense.category,
                    'amount': float(expense.amount),
                    'description': expense.description or expense.category,
                    'receipt_filename': expense.receipt_filename
                }
            })

        # Check if we should return to activity form or financial report
        return_to = request.form.get('return_to') or request.args.get('return_to')
        if return_to == 'activity_form':
            return redirect(url_for("activity_form", activity_id=activity.id))
        elif return_to == 'financial_report':
            return redirect(url_for("financial_report"))
        else:
            return redirect(url_for("activity_expenses", activity_id=activity.id))

    expenses = Expense.query.filter_by(activity_id=activity.id).order_by(Expense.date.desc()).all()

    gross_revenue = sum(p.sold_amt for p in activity.passports if p.paid)
    cogs_total = sum(e.amount for e in expenses if e.category == "Cost of Goods Sold")
    opex_total = sum(e.amount for e in expenses if e.category != "Cost of Goods Sold")
    gross_profit = gross_revenue - cogs_total
    total_expenses = cogs_total + opex_total
    net_income = gross_revenue - total_expenses

    summary = {
        "gross_revenue": gross_revenue,
        "cogs_total": cogs_total,
        "gross_profit": gross_profit,
        "opex_total": opex_total,
        "total_expenses": total_expenses,
        "net_income": net_income
    }

    return render_template("activity_expenses.html",
        activity=activity,
        expense=expense,
        expenses=expenses,
        categories=expense_categories,
        summary=summary,
        now=dt.now
    )





@app.route("/admin/delete-income/<int:income_id>", methods=["POST"])
def delete_income(income_id):
    income = Income.query.get_or_404(income_id)
    activity_id = income.activity_id
    activity = Activity.query.get(activity_id)

    # Log the deletion before deleting
    log_action = f"Deleted Income: ${income.amount:.2f} - {income.category} for Activity '{activity.name if activity else 'Unknown'}'"
    db.session.add(AdminActionLog(
        admin_email=session.get("admin"),
        action=log_action
    ))

    db.session.delete(income)
    db.session.commit()
    flash("Income deleted.", "success")

    # Handle AJAX requests (from financial report)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Income deleted successfully'
        })

    # Check if we should return to activity form or financial report
    return_to = request.form.get('return_to') or request.args.get('return_to')
    if return_to == 'activity_form':
        return redirect(url_for("activity_form", activity_id=activity_id))
    elif return_to == 'financial_report':
        return redirect(url_for("financial_report"))
    else:
        return redirect(url_for("activity_income", activity_id=activity_id))


@app.route("/admin/delete-expense/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    activity_id = expense.activity_id
    activity = Activity.query.get(activity_id)

    # Log the deletion before deleting
    log_action = f"Deleted Expense: ${expense.amount:.2f} - {expense.category} for Activity '{activity.name if activity else 'Unknown'}'"
    db.session.add(AdminActionLog(
        admin_email=session.get("admin"),
        action=log_action
    ))

    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "success")

    # Handle AJAX requests (from financial report)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Expense deleted successfully'
        })

    # Check if we should return to activity form or financial report
    return_to = request.form.get('return_to') or request.args.get('return_to')
    if return_to == 'activity_form':
        return redirect(url_for("activity_form", activity_id=activity_id))
    elif return_to == 'financial_report':
        return redirect(url_for("financial_report"))
    else:
        return redirect(url_for("activity_expenses", activity_id=activity_id))


@app.route('/admin/mark-income-paid/<int:income_id>', methods=['POST'])
def mark_income_paid(income_id):
    """Mark an income transaction as received"""
    if 'admin_logged_in' not in session and 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        income = Income.query.get_or_404(income_id)

        # Update payment status
        income.payment_status = 'received'
        income.payment_date = datetime.now(timezone.utc)

        db.session.commit()

        flash(f'Income of ${income.amount:.2f} marked as received', 'success')
        return jsonify({'success': True, 'message': 'Income marked as received'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/mark-expense-paid/<int:expense_id>', methods=['POST'])
def mark_expense_paid(expense_id):
    """Mark an expense transaction as paid"""
    if 'admin_logged_in' not in session and 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        expense = Expense.query.get_or_404(expense_id)

        # Update payment status
        expense.payment_status = 'paid'
        expense.payment_date = datetime.now(timezone.utc)

        db.session.commit()

        flash(f'Expense of ${expense.amount:.2f} marked as paid', 'success')
        return jsonify({'success': True, 'message': 'Expense marked as paid'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route("/admin/activity", methods=["GET", "POST"])
@app.route("/admin/activity/<int:activity_id>", methods=["GET", "POST"])
def activity_form(activity_id=None):
    activity = db.session.get(Activity, activity_id) if activity_id else None
    is_edit = bool(activity)

    if request.method == "POST":
        if not activity:
            activity = Activity(created_by=1)  # replace with session-based admin ID if available
            db.session.add(activity)

        activity.name = request.form.get("name")
        activity.type = request.form.get("type")
        activity.status = request.form.get("status")
        activity.description = request.form.get("description")

        # Dates
        try:
            activity.start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%dT%H:%M")
        except:
            activity.start_date = None

        try:
            activity.end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%dT%H:%M")
        except:
            activity.end_date = None

        # Handle image upload
        upload_file = request.files.get("upload_image")
        if upload_file and upload_file.filename:
            ext = os.path.splitext(upload_file.filename)[1]
            filename = f"activity_{uuid.uuid4().hex}{ext}"
            path = os.path.join(app.static_folder, "uploads/activity_images", filename)
            upload_file.save(path)
            activity.image_filename = filename

        elif request.form.get("selected_image_filename"):
            activity.image_filename = request.form.get("selected_image_filename")

        db.session.commit()
        flash("Activity saved.", "success")
        return redirect(url_for("dashboard"))

    # Financial summary
    if activity:
        passport_income = sum(p.sold_amt for p in activity.passports if p.paid)
        other_income = sum(i.amount for i in activity.incomes)
        total_income = passport_income + other_income

        cogs = sum(e.amount for e in activity.expenses if e.category == "Cost of Goods Sold")
        opex = sum(e.amount for e in activity.expenses if e.category != "Cost of Goods Sold")
        total_expenses = cogs + opex
        net_income = total_income - total_expenses

        summary = {
            "passport_income": passport_income,
            "other_income": other_income,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_income": net_income
        }
    else:
        summary = None

    # Get passport types for the activity
    if activity:
        passport_types_objects = activity.passport_types
        # Convert to dictionaries for JSON serialization
        passport_types = []
        for pt in passport_types_objects:
            passport_types.append({
                'id': pt.id,
                'name': pt.name,
                'price_per_user': pt.price_per_user,
                'sessions_included': pt.sessions_included
            })
    else:
        passport_types = []
    
    # Get Google Maps API key for Places Autocomplete
    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')

    # Get payment email for display
    display_email = get_setting("DISPLAY_PAYMENT_EMAIL", "")
    payment_email = display_email if display_email else get_setting("MAIL_USERNAME", "")

    # Smart accordion expansion: detect which sections have data
    if activity:
        has_workflow_data = (
            activity.workflow_type == 'payment_first' or
            getattr(activity, 'offer_passport_renewal', False)
        )
        has_capacity_data = (
            getattr(activity, 'is_quantity_limited', False) or
            getattr(activity, 'allow_quantity_selection', False) or
            getattr(activity, 'max_sessions', None)
        )
        has_schedule_data = (
            activity.start_date or
            activity.end_date or
            getattr(activity, 'location_address_formatted', None)
        )
        has_advanced_data = (
            getattr(activity, 'goal_revenue', 0) and activity.goal_revenue > 0
        )
    else:
        has_workflow_data = False
        has_capacity_data = False
        has_schedule_data = False
        has_advanced_data = False

    return render_template("activity_form.html",
                           activity=activity,
                           passport_types=passport_types,
                           summary=summary,
                           google_maps_api_key=google_maps_api_key,
                           payment_email=payment_email,
                           has_workflow_data=has_workflow_data,
                           has_capacity_data=has_capacity_data,
                           has_schedule_data=has_schedule_data,
                           has_advanced_data=has_advanced_data)








@app.route("/delete-activity/<int:activity_id>", methods=["POST"])
def delete_activity(activity_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    # Import models at the beginning
    from models import PassportType, Expense, Income, Signup, Passport, Survey, AdminActionLog

    activity = db.session.get(Activity, activity_id)
    if not activity:
        flash("Activity not found.", "error")
        return redirect(url_for("list_activities"))

    # Check for active passports first
    active_passports = Passport.query.filter_by(
        activity_id=activity_id
    ).filter(Passport.uses_remaining > 0).count()

    if active_passports > 0:
        flash(f"Cannot delete activity. There are {active_passports} active passports.", "error")
        return redirect(url_for("activity_dashboard", activity_id=activity_id))

    # Capture activity details BEFORE deletion for logging
    activity_name = activity.name
    activity_type = activity.type if activity.type else "Unknown Type"

    # Delete related records first (in order to avoid FK constraints)
    # Note: Redemptions will be auto-deleted via CASCADE when passports are deleted

    # Delete redemptions first (explicit cleanup before CASCADE)
    passport_ids = [p.id for p in Passport.query.filter_by(activity_id=activity_id).all()]
    if passport_ids:
        Redemption.query.filter(Redemption.passport_id.in_(passport_ids)).delete(synchronize_session=False)

    PassportType.query.filter_by(activity_id=activity_id).delete()
    Expense.query.filter_by(activity_id=activity_id).delete()
    Income.query.filter_by(activity_id=activity_id).delete()
    Survey.query.filter_by(activity_id=activity_id).delete()
    Signup.query.filter_by(activity_id=activity_id).delete()
    Passport.query.filter_by(activity_id=activity_id).delete()

    # Now delete the activity
    db.session.delete(activity)

    # Log the deletion
    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=f"Deleted activity: {activity_name} ({activity_type}) by {session.get('admin', 'unknown')}"
    ))

    db.session.commit()
    flash("Activity deleted successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/check-activity-passports/<int:activity_id>")
def check_activity_passports(activity_id):
    """Check if activity has active passports (uses_remaining > 0)"""
    if "admin" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    active_passports = Passport.query.filter_by(
        activity_id=activity_id
    ).filter(Passport.uses_remaining > 0).all()
    
    passport_list = []
    for p in active_passports[:5]:  # Show max 5
        passport_list.append({
            'email': p.user.email if p.user else 'No email',
            'uses_remaining': p.uses_remaining
        })
    
    return jsonify({
        'has_active_passports': len(active_passports) > 0,
        'count': len(active_passports),
        'active_passports': passport_list
    })


@app.route("/activity-dashboard/<int:activity_id>")
def activity_dashboard(activity_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Activity, Signup, Passport, Survey, SurveyResponse, AdminActionLog, Expense, Income
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_, func
    from datetime import datetime, timezone, timedelta
    from kpi_renderer import render_revenue_card, render_active_users_card, render_passports_created_card, render_passports_unpaid_card, render_passports_redeemed_card

    activity = db.session.get(Activity, activity_id)
    if not activity:
        flash("Activity not found", "error")
        return redirect(url_for("dashboard2"))

    # Get filter and search parameters from request
    passport_filter = request.args.get('passport_filter', '')
    signup_filter = request.args.get('signup_filter', 'pending')
    show_all_param = request.args.get('show_all', '')
    q = request.args.get('q', '').strip()  # Add search parameter support

    # Default to 'active' filter if no passport filter specified (unless explicitly showing all)
    if not passport_filter and show_all_param != "true":
        passport_filter = "active"

    # Load all related signups with user eager-loaded
    signups_query = (
        Signup.query
        .options(joinedload(Signup.user))
        .filter_by(activity_id=activity_id)
    )
    
    # Apply signup filters
    if signup_filter == 'paid':
        signups_query = signups_query.filter_by(paid=True)
    elif signup_filter == 'unpaid':
        signups_query = signups_query.filter_by(paid=False)
    elif signup_filter == 'pending':
        signups_query = signups_query.filter_by(status='pending')
    elif signup_filter == 'approved':
        signups_query = signups_query.filter_by(status='approved')
    
    # IMPORTANT: On activity_dashboard, search only applies to passports, NOT signups
    # Signups are displayed unfiltered by search query for clarity
    
    signups = signups_query.order_by(Signup.signed_up_at.desc()).all()

    # Load passports with filtering
    passports_query = (
        Passport.query
        .options(joinedload(Passport.user), joinedload(Passport.activity), joinedload(Passport.passport_type))
        .filter(Passport.activity_id == activity_id)
    )
    
    # Apply passport filters
    if passport_filter == 'active':
        # Active = has remaining uses OR unpaid (same logic as Passports page)
        passports_query = passports_query.filter(
            or_(
                Passport.uses_remaining > 0,
                Passport.paid == False
            )
        )
    elif passport_filter == 'unpaid':
        passports_query = passports_query.filter_by(paid=False)
    elif passport_filter == 'paid':
        passports_query = passports_query.filter_by(paid=True)
    # else: show_all_param == "true" - no filter applied, show truly ALL passports
    
    # Apply search filter for passports
    if q:
        from models import User
        passports_query = passports_query.join(User).filter(
            or_(
                User.name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
                Passport.pass_code.ilike(f"%{q}%"),
                Passport.notes.ilike(f"%{q}%")
            )
        )
    
    passports = passports_query.order_by(Passport.created_dt.desc()).all()

    # Use the enhanced get_kpi_data function with activity filtering
    from utils import get_kpi_data
    kpi_data = get_kpi_data(activity_id=activity_id)  # Filter for this specific activity

    # Generate fiscal year data for mobile view
    mobile_kpi_data = get_kpi_data(activity_id=activity_id, period='fy')

    # Get the 7-day KPI data by default (this will be the initial view)
    current_kpi = kpi_data.get('revenue', {})

    # Calculate all-time revenue for progress bar (cash basis accounting)
    # Sum all PAID passport revenue + all income for this activity
    from sqlalchemy import func
    paid_passport_revenue = db.session.query(func.sum(Passport.sold_amt)).filter(
        Passport.activity_id == activity_id,
        Passport.paid == True
    ).scalar() or 0

    all_passport_revenue = db.session.query(func.sum(Passport.sold_amt)).filter(
        Passport.activity_id == activity_id
    ).scalar() or 0

    income_revenue = db.session.query(func.sum(Income.amount)).filter(
        Income.activity_id == activity_id
    ).scalar() or 0

    # Total paid revenue (for progress bar - cash basis)
    total_paid_revenue = paid_passport_revenue + income_revenue
    # Total sold revenue (for display - shows all sales)
    total_sold_revenue = all_passport_revenue + income_revenue
    
    # Calculate additional activity-specific metrics
    now = datetime.now(timezone.utc)
    three_days_ago = now - timedelta(days=3)
    
    # Get all passports and signups for this activity for additional calculations and counts
    all_passports = Passport.query.filter_by(activity_id=activity_id).all()
    all_signups = Signup.query.filter_by(activity_id=activity_id).all()

    # Calculate statistics using ALL passports (not filtered results) - for filter button counts
    total_passports_count = len(all_passports)
    paid_passports_count = len([p for p in all_passports if p.paid])
    unpaid_passports_count = len([p for p in all_passports if not p.paid])
    # Active = has remaining uses OR unpaid
    active_passports_count = len([p for p in all_passports if p.uses_remaining > 0 or not p.paid])

    # Statistics dict for template (used in filter button counts)
    passport_statistics = {
        'total_passports': total_passports_count,
        'paid_passports': paid_passports_count,
        'unpaid_passports': unpaid_passports_count,
        'active_passports': active_passports_count,
    }
    
    # Helper function to safely compare dates
    def is_recent(dt, cutoff_date):
        if not dt:
            return False
        # Make timezone-naive datetime timezone-aware if needed
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= cutoff_date
    
    # Unpaid passport statistics
    unpaid_passports = [p for p in all_passports if not p.paid]
    unpaid_count = len(unpaid_passports)
    overdue_count = len([p for p in unpaid_passports if p.created_dt and not is_recent(p.created_dt, three_days_ago)])
    
    # Activity profit calculation (combining revenue with expenses/income)
    try:
        activity_expenses = sum(e.amount for e in activity.expenses) if hasattr(activity, 'expenses') else 0
        activity_income = sum(i.amount for i in activity.incomes) if hasattr(activity, 'incomes') else 0
        total_income = current_kpi.get('revenue', 0) + activity_income
        profit = total_income - activity_expenses
        profit_margin = (profit / total_income * 100) if total_income > 0 else 0
    except:
        profit = current_kpi.get('revenue', 0)  # Fallback to just revenue if expenses not tracked
        profit_margin = 100
    
    # Signup statistics
    pending_signups = [s for s in signups if s.status == 'pending']
    approved_signups = [s for s in signups if s.status == 'approved']

    has_pending_signups = len(pending_signups) > 0
    activity_pending_signups_count = len(pending_signups)
    
    # Activity log entries (recent activity)
    # Use get_all_activity_logs to get properly formatted logs like dashboard does
    from utils import get_all_activity_logs
    all_activity_logs = get_all_activity_logs()
    # Filter for this activity
    activity_logs = [log for log in all_activity_logs if activity.name in log.get('action', '')][:10]

    # KPI data structure for the dashboard template
    # Using the same structure from get_kpi_data() as dashboard does - no transformation
    # The old custom structure is commented out below:
    # kpi_data = {
    #     'revenue': {
    #         'current': current_kpi.get('revenue', 0),
    #         'change_7d': current_kpi.get('revenue_change', 0),
    #         ...
    #     }
    # }
    
    # kpi_data is already set from line 4020: kpi_data = get_kpi_data(activity_id=activity_id)
    
    # Dashboard statistics
    dashboard_stats = {
        'total_passports': len(all_passports),
        'paid_passports': len([p for p in all_passports if p.paid]),
        'unpaid_passports': unpaid_count,
        'active_passports': current_kpi.get('active_users', 0),
        'pending_signups': len(pending_signups),
        'approved_signups': len(approved_signups),
        'recent_signups': current_kpi.get('pending_signups', 0),
        'total_users': len(set(p.user_id for p in all_passports))
    }

    # Load surveys for this activity (handle case where tables might not exist yet)
    try:
        surveys = (
            Survey.query
            .options(joinedload(Survey.responses))
            .filter_by(activity_id=activity_id)
            .order_by(Survey.created_dt.desc())
            .all()
        )
    except Exception as e:
        # If survey tables don't exist yet, return empty list
        print(f"Warning: Survey tables not found: {e}")
        surveys = []

    # Load available survey templates for the modal
    try:
        survey_templates = SurveyTemplate.query.filter_by(status='active').all()
    except Exception as e:
        print(f"Warning: Survey template tables not found: {e}")
        survey_templates = []

    # Load passport types for this activity
    from models import PassportType
    passport_types = PassportType.query.filter_by(activity_id=activity_id, status='active').all()

    # Calculate survey rating for activity header
    survey_rating, survey_count = calculate_activity_survey_rating(activity_id)

    # Render KPI cards with activity filter
    revenue_card = render_revenue_card(activity_id=activity_id)
    active_users_card = render_active_users_card(activity_id=activity_id)  
    passports_created_card = render_passports_created_card(activity_id=activity_id)
    passports_unpaid_card = render_passports_unpaid_card(activity_id=activity_id)

    # Determine if showing all (explicitly requested)
    show_all = show_all_param == "true"

    return render_template(
        "activity_dashboard.html",
        activity=activity,
        signups=signups,
        passes=passports,
        all_signups=all_signups,  # For filter counts
        all_passports=all_passports,  # For filter counts
        surveys=surveys,
        survey_templates=survey_templates,
        passport_types=passport_types,
        kpi_data=kpi_data,
        mobile_kpi_data=mobile_kpi_data,
        dashboard_stats=dashboard_stats,
        activity_logs=activity_logs,
        logs=activity_logs,  # Added for compatibility with copied KPI cards JavaScript
        current_datetime=datetime.now(),
        revenue_card=revenue_card,
        active_users_card=active_users_card,
        passports_created_card=passports_created_card,
        passports_unpaid_card=passports_unpaid_card,
        has_pending_signups=has_pending_signups,
        activity_pending_signups_count=activity_pending_signups_count,
        survey_rating=survey_rating,
        survey_count=survey_count,
        total_paid_revenue=total_paid_revenue,
        total_sold_revenue=total_sold_revenue,
        # Add filter-related data for server-side filtering (like Passports page)
        passport_statistics=passport_statistics,
        current_filters={
            'q': q,
            'passport_filter': passport_filter,
            'signup_filter': signup_filter,
            'show_all': show_all
        }
    )


@app.route("/api/activity-kpis/<int:activity_id>")
@admin_required
@rate_limit(max_requests=30, window=60)  # 30 requests per minute
@log_api_call
@cache_response(timeout=180)  # Cache for 3 minutes
def get_activity_kpis_api(activity_id):
    """Secure API endpoint to get KPI data for a specific activity and period
    
    Security Features:
    - Admin authentication required
    - Rate limiting (30 req/min)
    - Input validation and sanitization
    - SQL injection prevention
    - Request logging
    - Response caching
    """
    from markupsafe import escape
    
    # Input validation and sanitization
    try:
        # Validate activity_id
        if activity_id is None or activity_id <= 0:
            return jsonify({
                "success": False, 
                "error": "Invalid activity ID",
                "code": "INVALID_ACTIVITY_ID"
            }), 400
        
        # Validate and sanitize period parameter
        period_param = request.args.get('period', '7')
        try:
            period = int(escape(str(period_param)))
            if period not in [7, 30, 90, 365]:
                period = 7  # Default fallback
        except (ValueError, TypeError):
            period = 7
        
        # Validate activity exists and user has access
        from models import Activity
        activity = db.session.execute(
            text("SELECT id, name FROM activity WHERE id = :activity_id AND status = 'active'"),
            {"activity_id": activity_id}
        ).fetchone()
        
        if not activity:
            return jsonify({
                "success": False, 
                "error": "Activity not found or inactive",
                "code": "ACTIVITY_NOT_FOUND"
            }), 404
            
    except Exception as e:
        logger.error(f"Input validation error in KPI API: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Invalid request parameters",
            "code": "VALIDATION_ERROR"
        }), 400
    
    # Try to use new KPI Card component first, fallback to legacy implementation
    try:
        # Use the secure KPI Card component with validation
        dashboard_cards = generate_dashboard_cards(
            activity_id=activity_id,
            period=f"{period}d",
            device_type='desktop'
        )
        
        if dashboard_cards.get('success'):
            # Transform to expected format
            kpi_data = {}
            for card_id, card in dashboard_cards['cards'].items():
                card_type = card['card_type']
                if card_type == 'revenue':
                    kpi_data['revenue'] = {
                        'total': card['total'],
                        'change': card['change'],
                        'trend': card['trend_direction'],
                        'percentage': card['percentage'],
                        'trend_data': card['trend_data']
                    }
                elif card_type == 'active_users':
                    kpi_data['active_users'] = {
                        'total': card['total'],
                        'change': card['change'],
                        'trend': card['trend_direction'],
                        'percentage': card['percentage'],
                        'trend_data': card['trend_data']
                    }
                elif card_type == 'unpaid_passports':
                    kpi_data['unpaid_passports'] = {
                        'total': card['total'],
                        'change': card['change'],
                        'trend': card['trend_direction'],
                        'percentage': card['percentage'],
                        'overdue': card.get('overdue', 0),
                        'trend_data': card['trend_data']
                    }
                elif card_type == 'profit':
                    kpi_data['profit'] = {
                        'total': card['total'],
                        'margin': card.get('margin', 0),
                        'change': card['change'],
                        'trend': card['trend_direction'],
                        'percentage': card['percentage'],
                        'trend_data': card['trend_data']
                    }
            
            return jsonify({
                "success": True,
                "period": period,
                "kpi_data": kpi_data,
                "source": "kpi_component",
                "cache_info": {
                    "generation_time_ms": dashboard_cards.get('generation_time_ms', 0),
                    "cache_hit": any(card.get('cache_hit', False) for card in dashboard_cards['cards'].values())
                }
            })
        
        # Fallback to legacy implementation with enhanced security
        logger.info(f"Falling back to legacy KPI implementation for activity {activity_id}")
        
    except Exception as component_error:
        logger.warning(f"KPI component failed, using legacy: {str(component_error)}")
    
    # Legacy implementation with security enhancements
    from models import Activity, Passport
    from datetime import datetime, timezone, timedelta
    from utils import get_kpi_data
    import math
    
    try:
        # Secure database query using parameterized query
        activity = db.session.execute(
            text("SELECT * FROM activity WHERE id = :activity_id AND status = 'active'"),
            {"activity_id": activity_id}
        ).fetchone()
        
        if not activity:
            return jsonify({
                "success": False, 
                "error": "Activity not found",
                "code": "ACTIVITY_NOT_FOUND"
            }), 404
        
        # Use the enhanced get_kpi_stats function with activity filtering
        kpi_stats = get_kpi_data(activity_id=activity_id)
        
        # Map period to the correct key
        period_key = '7d'
        if period == 30:
            period_key = '30d'
        elif period == 90:
            period_key = '90d'
        
        # Get the KPI data for the requested period
        period_data = kpi_stats.get(period_key, {})
        
        # Helper function to safely validate and clean numeric values
        def safe_float(value, default=0.0):
            """Convert value to float, handling None, NaN, and invalid values"""
            try:
                if value is None:
                    return default
                float_val = float(value)
                if math.isnan(float_val) or math.isinf(float_val):
                    return default
                return round(float_val, 2)
            except (TypeError, ValueError):
                return default
        
        # Helper function to validate and clean trend data arrays
        def clean_trend_data(trend_data, default_length=7):
            """Clean trend data array, ensuring all values are valid numbers"""
            if not isinstance(trend_data, list):
                return [0] * default_length
            
            cleaned = []
            for value in trend_data:
                cleaned.append(safe_float(value, 0))
            
            # Ensure we have the right number of data points
            if len(cleaned) < default_length:
                cleaned.extend([0] * (default_length - len(cleaned)))
            elif len(cleaned) > default_length:
                cleaned = cleaned[-default_length:]
                
            return cleaned
        
        # Calculate additional activity-specific metrics
        now = datetime.now(timezone.utc)
        three_days_ago = now - timedelta(days=3)
        
        # Get all passports for unpaid statistics with proper error handling
        try:
            all_passports = Passport.query.filter_by(activity_id=activity_id).all()
            unpaid_passports = [p for p in all_passports if not p.paid]
            unpaid_count = len(unpaid_passports)
            
            # Helper function to safely compare dates
            def is_recent(dt, cutoff_date):
                if not dt:
                    return False
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt >= cutoff_date
            
            overdue_count = len([p for p in unpaid_passports if p.created_dt and not is_recent(p.created_dt, three_days_ago)])
        except Exception as e:
            print(f"Error calculating unpaid passports for activity {activity_id}: {e}")
            unpaid_count = 0
            overdue_count = 0
        
        # Calculate profit (combining revenue with expenses/income)
        try:
            activity_expenses = sum(safe_float(e.amount) for e in getattr(activity, 'expenses', []))
            activity_income = sum(safe_float(i.amount) for i in getattr(activity, 'incomes', []))
            current_revenue = safe_float(period_data.get('revenue', 0))
            total_income = current_revenue + activity_income
            profit = total_income - activity_expenses
            profit_margin = (profit / total_income * 100) if total_income > 0 else 0
            
            # Previous period profit for comparison
            previous_revenue = safe_float(period_data.get('revenue_prev', 0))
            previous_total_income = previous_revenue + activity_income
            previous_profit = previous_total_income - activity_expenses
            profit_change = ((profit - previous_profit) / previous_profit * 100) if previous_profit > 0 else 0
        except Exception as e:
            print(f"Error calculating profit for activity {activity_id}: {e}")
            profit = safe_float(period_data.get('revenue', 0))
            profit_margin = 100 if profit > 0 else 0
            profit_change = safe_float(period_data.get('revenue_change', 0))
        
        # Get and clean trend data length based on period
        trend_length = period if period in [7, 30, 90] else 7
        
        # Build KPI data with proper validation and cleaning
        kpi_data = {
            'revenue': {
                'total': safe_float(period_data.get('revenue', 0)),
                'change': safe_float(period_data.get('revenue_change', 0)),
                'trend': 'up' if safe_float(period_data.get('revenue_change', 0)) > 0 else 'down' if safe_float(period_data.get('revenue_change', 0)) < 0 else 'stable',
                'percentage': abs(safe_float(period_data.get('revenue_change', 0))),
                'trend_data': clean_trend_data(period_data.get('revenue_trend', []), trend_length)
            },
            'active_users': {
                'total': int(safe_float(period_data.get('active_users', 0))),
                'change': safe_float(period_data.get('passport_change', 0)),
                'trend': 'up' if safe_float(period_data.get('passport_change', 0)) > 0 else 'down' if safe_float(period_data.get('passport_change', 0)) < 0 else 'stable',
                'percentage': abs(safe_float(period_data.get('passport_change', 0))),
                'trend_data': clean_trend_data(period_data.get('active_users_trend', []), trend_length)
            },
            'unpaid_passports': {
                'total': unpaid_count,
                'change': 0,  # We don't track unpaid changes in the base KPI function
                'trend': 'stable',
                'percentage': 0,
                'overdue': overdue_count,
                'trend_data': [unpaid_count] * trend_length  # Simple placeholder with correct length
            },
            'profit': {
                'total': safe_float(profit),
                'margin': safe_float(profit_margin),
                'change': safe_float(profit_change),
                'trend': 'up' if safe_float(profit_change) > 0 else 'down' if safe_float(profit_change) < 0 else 'stable',
                'percentage': abs(safe_float(profit_change)),
                'trend_data': clean_trend_data(period_data.get('revenue_trend', []), trend_length)  # Use revenue trend as proxy for profit
            }
        }
        
        return jsonify({
            "success": True,
            "period": period,
            "kpi_data": kpi_data
        })
        
    except Exception as e:
        # Secure error logging without exposing sensitive data
        logger.error(f"Error in get_activity_kpis_api for activity {activity_id}: {str(e)}")
        
        # Log the full error for debugging but don't expose to client
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": str(e) if current_app.debug else "Please try again later",
            "activity_id": activity_id  # Safe to include
        }), 500


@app.route("/api/activity-dashboard-data/<int:activity_id>")
@admin_required
@rate_limit(max_requests=40, window=60)  # 40 requests per minute
@log_api_call
def get_activity_dashboard_data(activity_id):
    """Secure API endpoint to get filtered passport and signup data for activity dashboard
    
    Security Features:
    - Admin authentication required
    - Rate limiting (40 req/min)
    - Input validation and sanitization
    - SQL injection prevention
    - Request logging
    """
    from markupsafe import escape
    
    # Input validation and sanitization
    try:
        # Validate activity_id
        if activity_id is None or activity_id <= 0:
            return jsonify({
                "success": False, 
                "error": "Invalid activity ID",
                "code": "INVALID_ACTIVITY_ID"
            }), 400
        
        # Validate and sanitize filter parameters
        passport_filter = escape(str(request.args.get('passport_filter', 'active'))).strip()[:20]
        signup_filter = escape(str(request.args.get('signup_filter', 'all'))).strip()[:20]
        search_query = escape(str(request.args.get('q', ''))).strip()[:100]
        
        # Validate filter values
        valid_passport_filters = ['all', 'unpaid', 'active']
        valid_signup_filters = ['all', 'paid', 'unpaid', 'pending']

        if passport_filter not in valid_passport_filters:
            passport_filter = 'active'  # Default to active
        if signup_filter not in valid_signup_filters:
            signup_filter = 'all'
            
    except Exception as e:
        logger.error(f"Input validation error in activity dashboard API: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Invalid request parameters",
            "code": "VALIDATION_ERROR"
        }), 400
    
    from models import Activity, Signup, Passport
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_
    
    try:
        # Use secure parameterized query to check activity exists
        activity = db.session.execute(
            text("SELECT id, name FROM activity WHERE id = :activity_id AND status = 'active'"),
            {"activity_id": activity_id}
        ).fetchone()
        
        if not activity:
            return jsonify({
                "success": False, 
                "error": "Activity not found or inactive",
                "code": "ACTIVITY_NOT_FOUND"
            }), 404
        
        # Get filter and search parameters (already validated above)
        q = search_query
        
        # Load filtered signups
        signups_query = (
            Signup.query
            .options(joinedload(Signup.user))
            .filter_by(activity_id=activity_id)
        )
        
        if signup_filter == 'paid':
            signups_query = signups_query.filter_by(paid=True)
        elif signup_filter == 'unpaid':
            signups_query = signups_query.filter_by(paid=False)
        elif signup_filter == 'pending':
            signups_query = signups_query.filter_by(status='pending')
        elif signup_filter == 'approved':
            signups_query = signups_query.filter_by(status='approved')
        
        # IMPORTANT: On activity_dashboard, search only applies to passports, NOT signups
        # Signups are displayed unfiltered by search query for clarity
        
        signups = signups_query.order_by(Signup.signed_up_at.desc()).all()
        
        # Load filtered passports
        passports_query = (
            Passport.query
            .options(joinedload(Passport.user), joinedload(Passport.activity), joinedload(Passport.passport_type))
            .filter(Passport.activity_id == activity_id)
        )
        
        if passport_filter == 'unpaid':
            passports_query = passports_query.filter_by(paid=False)
        elif passport_filter == 'active':
            # Active = has remaining uses OR unpaid
            passports_query = passports_query.filter(
                or_(
                    Passport.uses_remaining > 0,
                    Passport.paid == False
                )
            )
        # 'all' - no additional filter, show all passports
        
        # Apply search filter if provided
        if q:
            passports_query = passports_query.join(User).filter(
                or_(
                    User.name.ilike(f"%{q}%"),
                    User.email.ilike(f"%{q}%"),
                    Passport.pass_code.ilike(f"%{q}%")
                )
            )
        
        passports = passports_query.order_by(Passport.created_dt.desc()).all()
        
        # Get all passports and signups for filter counts
        all_passports = Passport.query.filter_by(activity_id=activity_id).all()
        all_signups = Signup.query.filter_by(activity_id=activity_id).all()
        
        # Get passport types for signup template
        from models import PassportType
        passport_types = PassportType.query.filter_by(activity_id=activity_id).all()
        
        # Render the table HTML fragments
        from flask import render_template_string
        
        # Passport table HTML
        passport_html = render_template('partials/passport_table_rows.html', 
                                      passes=passports, activity=activity)
        
        # Signup table HTML  
        signup_html = render_template('partials/signup_table_rows.html',
                                    signups=signups, passport_types=passport_types)
        
        # Calculate filter counts
        passport_counts = {
            'all': len(all_passports),
            'unpaid': len([p for p in all_passports if not p.paid]),
            'active': len([p for p in all_passports if p.uses_remaining > 0 or not p.paid])
        }
        
        signup_counts = {
            'all': len(all_signups),
            'unpaid': len([s for s in all_signups if not s.paid]),
            'paid': len([s for s in all_signups if s.paid]),
            'pending': len([s for s in all_signups if s.status == 'pending']),
            'approved': len([s for s in all_signups if s.status == 'approved'])
        }
        
        return jsonify({
            "success": True,
            "passport_html": passport_html,
            "signup_html": signup_html,
            "passport_counts": passport_counts,
            "signup_counts": signup_counts
        })
        
    except Exception as e:
        print(f"Error in get_activity_dashboard_data for activity {activity_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e) if current_app.debug else "Please try again later"
        }), 500

@app.route("/api/global-kpis")
@admin_required
@rate_limit(max_requests=60, window=60)  # 60 requests per minute for global data
@log_api_call
@cache_response(timeout=300)  # Cache for 5 minutes
def get_global_kpis_api():
    """Secure API endpoint to get global KPI data for a specific period
    
    Security Features:
    - Admin authentication required
    - Rate limiting (60 req/min)
    - Input validation and sanitization
    - Request logging
    - Response caching
    """
    from markupsafe import escape
    
    # Input validation and sanitization
    try:
        # Validate and sanitize period parameter
        period_param = request.args.get('period', '7d')
        period = escape(str(period_param)).strip()
        
        # Validate period format
        valid_periods = ['7d', '30d', '90d']
        if period not in valid_periods:
            return jsonify({
                "success": False,
                "error": f"Invalid period. Must be one of: {', '.join(valid_periods)}",
                "code": "INVALID_PERIOD"
            }), 400
            
    except Exception as e:
        logger.error(f"Input validation error in global KPI API: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Invalid request parameters",
            "code": "VALIDATION_ERROR"
        }), 400
    
    # Try to use new KPI Card component first, fallback to legacy implementation
    try:
        # Use the secure KPI Card component
        dashboard_cards = generate_dashboard_cards(
            activity_id=None,  # Global data
            period=period,
            device_type='desktop'
        )
        
        if dashboard_cards.get('success'):
            # Transform to expected format for global dashboard
            kpi_data = {}
            for card_id, card in dashboard_cards['cards'].items():
                card_type = card['card_type']
                
                # Map card types to expected global KPI format
                if card_type == 'revenue':
                    kpi_data['revenue'] = {
                        'total': card['total'],
                        'change': card['change'],
                        'trend': card['trend_direction'],
                        'percentage': card['percentage'],
                        'trend_data': card['trend_data']
                    }
                elif card_type == 'active_users':
                    kpi_data['active_passports'] = {
                        'total': card['total'],
                        'change': card['change'],
                        'trend': card['trend_direction'],
                        'percentage': card['percentage'],
                        'trend_data': card['trend_data']
                    }
                elif card_type == 'passports_created':
                    kpi_data['passports_created'] = {
                        'total': card['total'],
                        'change': card['change'],
                        'trend': card['trend_direction'],
                        'percentage': card['percentage'],
                        'trend_data': card['trend_data']
                    }
                elif card_type == 'pending_signups':
                    kpi_data['pending_signups'] = {
                        'total': card['total'],
                        'change': card['change'],
                        'trend': card['trend_direction'],
                        'percentage': card['percentage'],
                        'trend_data': card['trend_data']
                    }
            
            return jsonify({
                "success": True,
                "period": period,
                "kpi_data": kpi_data,
                "source": "kpi_component",
                "cache_info": {
                    "generation_time_ms": dashboard_cards.get('generation_time_ms', 0),
                    "cache_hit": any(card.get('cache_hit', False) for card in dashboard_cards['cards'].values())
                }
            })
        
        # Fallback to legacy implementation
        logger.info("Falling back to legacy global KPI implementation")
        
    except Exception as component_error:
        logger.warning(f"Global KPI component failed, using legacy: {str(component_error)}")
    
    # Legacy implementation with enhanced security
    from utils import get_kpi_data
    import math
    
    try:
        # Get global KPI stats with error handling
        kpi_stats = get_kpi_data()
        
        # Get the requested period data with validation
        period_data = kpi_stats.get(period, {})
        if not period_data:
            logger.warning(f"No KPI data available for period: {period}")
            return jsonify({
                "success": False, 
                "error": f"No data available for period: {period}",
                "code": "NO_DATA"
            }), 404
        
        # Helper function to safely validate and clean numeric values
        def safe_float(value, default=0.0):
            """Convert value to float, handling None, NaN, and invalid values"""
            try:
                if value is None:
                    return default
                float_val = float(value)
                if math.isnan(float_val) or math.isinf(float_val):
                    return default
                return round(float_val, 2)
            except (TypeError, ValueError):
                return default
        
        # Helper function to validate and clean trend data arrays
        def clean_trend_data(trend_data, default_length=7):
            """Clean trend data array, ensuring all values are valid numbers"""
            if not isinstance(trend_data, list):
                return [0] * default_length
            
            cleaned = []
            for value in trend_data:
                cleaned.append(safe_float(value, 0))
            
            # Ensure we have the right number of data points
            if len(cleaned) < default_length:
                cleaned.extend([0] * (default_length - len(cleaned)))
            elif len(cleaned) > default_length:
                cleaned = cleaned[-default_length:]
                
            return cleaned
        
        # Determine trend data length based on period
        period_days = {'7d': 7, '30d': 30, '90d': 90}
        trend_length = period_days.get(period, 7)
        
        # Format the response to match the frontend expectations with data validation
        kpi_data = {
            'revenue': {
                'total': safe_float(period_data.get('revenue', 0)),
                'change': safe_float(period_data.get('revenue_change', 0)),
                'trend': 'up' if safe_float(period_data.get('revenue_change', 0)) > 0 else 'down' if safe_float(period_data.get('revenue_change', 0)) < 0 else 'stable',
                'percentage': abs(safe_float(period_data.get('revenue_change', 0))),
                'trend_data': clean_trend_data(period_data.get('revenue_trend', []), trend_length)
            },
            'active_passports': {
                'total': int(safe_float(period_data.get('active_users', 0))),
                'change': safe_float(period_data.get('passport_change', 0)),
                'trend': 'up' if safe_float(period_data.get('passport_change', 0)) > 0 else 'down' if safe_float(period_data.get('passport_change', 0)) < 0 else 'stable',
                'percentage': abs(safe_float(period_data.get('passport_change', 0))),
                'trend_data': clean_trend_data(period_data.get('active_users_trend', []), trend_length)
            },
            'passports_created': {
                'total': int(safe_float(period_data.get('pass_created', 0))),
                'change': safe_float(period_data.get('new_passports_change', 0)),
                'trend': 'up' if safe_float(period_data.get('new_passports_change', 0)) > 0 else 'down' if safe_float(period_data.get('new_passports_change', 0)) < 0 else 'stable',
                'percentage': abs(safe_float(period_data.get('new_passports_change', 0))),
                'trend_data': clean_trend_data(period_data.get('pass_created_trend', []), trend_length)
            },
            'pending_signups': {
                'total': int(safe_float(period_data.get('pending_signups', 0))),
                'change': safe_float(period_data.get('signup_change', 0)),
                'trend': 'up' if safe_float(period_data.get('signup_change', 0)) > 0 else 'down' if safe_float(period_data.get('signup_change', 0)) < 0 else 'stable',
                'percentage': abs(safe_float(period_data.get('signup_change', 0))),
                'trend_data': clean_trend_data(period_data.get('pending_signups_trend', []), trend_length)
            }
        }
        
        return jsonify({
            "success": True,
            "period": period,
            "kpi_data": kpi_data
        })
        
    except Exception as e:
        # Secure error logging
        logger.error(f"Error in get_global_kpis_api: {str(e)}")
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": str(e) if current_app.debug else "Please try again later",
            "period": period if 'period' in locals() else 'unknown'
        }), 500


@app.route('/api/kpi-data', methods=['GET'])
@admin_required
@rate_limit(max_requests=30, window=60)
@log_api_call
@cache_response(timeout=60)
def get_kpi_data_api():
    """
    Unified KPI data endpoint for both global and activity-specific KPIs.
    Supports periods: 7d, 30d, 90d, all
    Optional activity_id parameter for activity-specific data
    """
    from utils import get_kpi_data
    from models import Activity
    from markupsafe import escape
    
    try:
        # Get and validate period parameter
        period = request.args.get('period', '7d')
        valid_periods = ['7d', '30d', '90d', 'fy', 'all']
        
        if period not in valid_periods:
            return jsonify({
                'success': False,
                'error': f'Invalid period. Must be one of: {", ".join(valid_periods)}'
            }), 400
        
        # Get optional activity_id parameter
        activity_id = request.args.get('activity_id', type=int)
        
        # Validate activity_id if provided
        if activity_id is not None:
            activity = db.session.get(Activity, activity_id)
            if not activity:
                return jsonify({
                    'success': False,
                    'error': f'Activity with id {activity_id} not found'
                }), 404
        
        # Get KPI data using the existing function
        kpi_data = get_kpi_data(activity_id=activity_id, period=period)
        
        # Return successful response
        return jsonify({
            'success': True,
            'period': period,
            'activity_id': activity_id,
            'kpi_data': kpi_data
        })
        
    except Exception as e:
        logger.error(f"Error in get_kpi_data_api: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching KPI data',
            'details': str(e) if app.debug else None
        }), 500


@app.template_filter("from_json")
def from_json_filter(json_str):
    """Parse JSON string in templates"""
    try:
        return json.loads(json_str) if json_str else {}
    except:
        return {}

@app.template_filter("days_ago")
def days_ago_filter(dt):
    """Calculate days between a datetime and now"""
    try:
        if dt:
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            diff = now - dt
            return diff.days
        return 0
    except:
        return 0

@app.template_filter("utc_to_local")
def jinja_utc_to_local_filter(dt):
    from utils import utc_to_local
    return utc_to_local(dt)

@app.template_filter("accounting_format")
def accounting_format(value):
    """Format numbers in accounting style with parentheses for negatives"""
    try:
        num = float(value)
        if num < 0:
            return f"(${abs(num):.2f})"
        else:
            return f"${num:.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@app.template_filter("log_type_color")
def log_type_color(log_type):
    """Return badge color class suffix for activity log types"""
    colors = {
        'Passport Redeemed': 'red',
        'Email Sent': 'blue',
        'Passport Created': 'green',
        'Payment Matched': 'teal',
        'Marked Paid': 'green',
        'Signup Submitted': 'yellow',
        'Signup Approved': 'green',
        'Signup Rejected': 'red',
        'Signup Cancelled': 'red',
        'Activity Created': 'purple',
        'Admin Action': 'gray',
        'Reminder Sent': 'purple',
    }
    return colors.get(log_type, 'gray')




##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##
##    ROUTES THAT USING SEND_EMAIL FUNCTION
##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##



@app.route("/create-passport", methods=["GET", "POST"])
def create_passport():
    from models import Passport, User, AdminActionLog, Activity
    import time

    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # ✅ Get current admin
        current_admin = Admin.query.filter_by(email=session.get("admin")).first()

        # ✅ Gather form data
        user_name = request.form.get("user_name", "").strip()
        user_email = request.form.get("user_email", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        sold_amt = float(request.form.get("sold_amt", 50))
        sessions_qt = int(request.form.get("sessionsQt") or request.form.get("uses_remaining") or 4)
        paid = "paid_ind" in request.form
        activity_id = int(request.form.get("activity_id", 0))
        passport_type_id = request.form.get("passport_type_id")
        passport_type_id = int(passport_type_id) if passport_type_id and passport_type_id != "" else None
        notes = request.form.get("notes", "").strip()

        # ✅ Validate required fields - Email is mandatory for all passport communications
        if not user_name:
            flash("Name is required.", "error")
            return redirect(request.url)
        if not user_email:
            flash("Email is required - all passport communications are sent via email.", "error")
            return redirect(request.url)
        if not activity_id:
            flash("Activity is required.", "error")
            return redirect(request.url)

        # ✅ Always create a new user (even if same email is reused)
        user = User(name=user_name, email=user_email, phone_number=phone_number)
        db.session.add(user)
        db.session.flush()  # Assign user.id

        # ✅ Get passport type name if passport_type_id is provided
        passport_type_name = None
        if passport_type_id:
            from models import PassportType
            passport_type = db.session.get(PassportType, passport_type_id)
            if passport_type:
                passport_type_name = passport_type.name

        # ✅ Create Passport object
        passport = Passport(
            pass_code=generate_pass_code(),
            user_id=user.id,
            activity_id=activity_id,
            passport_type_id=passport_type_id,
            passport_type_name=passport_type_name,
            sold_amt=sold_amt,
            uses_remaining=sessions_qt,
            created_by=current_admin.id if current_admin else None,
            created_dt=datetime.now(timezone.utc),  # fresh datetime (UTC)
            paid=paid,
            notes=notes
        )

        db.session.add(passport)
        db.session.commit()
        db.session.expire_all()

        # ✅ Log Admin Action (passport creation)
        activity_obj = db.session.get(Activity, activity_id)
        activity_name = activity_obj.name if activity_obj else "-"
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Passport created for {user.name} for activity '{activity_name}' by {session.get('admin', 'unknown')}"
        ))
        db.session.commit()

        # 💤 Small sleep to fix timestamp ordering
        time.sleep(0.5)

        # ✅ Refresh now_utc AFTER the passport and admin log are committed
        now_utc = datetime.now(timezone.utc)

        # ✅ Send confirmation email
        notify_pass_event(
            app=current_app._get_current_object(),
            event_type="pass_created",
            pass_data=passport,
            activity=passport.activity,
            admin_email=session.get("admin"),
            timestamp=now_utc
        )

        flash("Passport created and confirmation email sent.", "success")
        if activity_id and activity_id > 0:
            return redirect(url_for("activity_dashboard", activity_id=activity_id))
        else:
            return redirect(url_for("dashboard"))

    # 👉 GET METHOD
    default_amt = get_setting("DEFAULT_PASS_AMOUNT", "50")
    default_qt = get_setting("DEFAULT_SESSION_QT", "4")
    activity_list = Activity.query.filter_by(status='active').order_by(Activity.name).all()

    # Get activity_id from URL parameters if provided
    selected_activity_id = request.args.get('activity_id', type=int)
    
    # Load passport types for the selected activity or all activities
    from models import PassportType
    if selected_activity_id:
        passport_types = PassportType.query.filter_by(activity_id=selected_activity_id, status='active').all()
    else:
        passport_types = PassportType.query.filter_by(status='active').all()
    
    # Detect if activity has only one passport type for auto-selection
    single_passport_type_id = None
    if selected_activity_id and len(passport_types) == 1:
        single_passport_type_id = passport_types[0].id
        print(f"DEBUG: Auto-selecting passport type ID {single_passport_type_id} for activity {selected_activity_id}")
    elif selected_activity_id:
        print(f"DEBUG: Activity {selected_activity_id} has {len(passport_types)} passport types - no auto-selection")

    return render_template(
        "passport_form.html",
        passport=None,
        default_amt=default_amt,
        default_qt=default_qt,
        activity_list=activity_list,
        passport_types=passport_types,
        selected_activity_id=selected_activity_id,
        single_passport_type_id=single_passport_type_id
    )




# Store recent redemptions to prevent duplicate scans
recent_redemptions = {}

@app.route("/redeem/<pass_code>", methods=["POST"])
def redeem_passport(pass_code):
    from models import Passport, Redemption, AdminActionLog
    from utils import notify_pass_event
    from datetime import datetime, timezone, timedelta
    import time

    if "admin" not in session:
        return redirect(url_for("login"))

    now_utc = datetime.now(timezone.utc)

    passport = Passport.query.filter_by(pass_code=pass_code).first()
    if not passport:
        flash("Passport not found!", "error")
        return redirect(url_for("dashboard"))

    # 🛡️ Prevent duplicate redemptions (double-click protection)
    global recent_redemptions
    admin_id = session.get("admin", "unknown")
    throttle_key = f"{passport.id}_{admin_id}"

    # Check in-memory cache for recent redemptions (last 5 seconds)
    if throttle_key in recent_redemptions:
        last_redemption_time = recent_redemptions[throttle_key]
        if (now_utc - last_redemption_time).total_seconds() < 5:
            flash("Redemption already in progress. Please wait.", "warning")
            return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))

    # Check database for recent redemptions (last 10 seconds) for persistent protection
    five_seconds_ago = now_utc - timedelta(seconds=10)
    recent_db_redemption = Redemption.query.filter_by(
        passport_id=passport.id
    ).filter(
        Redemption.date_used >= five_seconds_ago
    ).first()

    if recent_db_redemption:
        flash("This passport was recently redeemed. Please refresh the page.", "warning")
        return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))

    # Record this redemption attempt in memory cache
    recent_redemptions[throttle_key] = now_utc

    # Clean up old entries from memory cache (keep only last 30 seconds)
    cutoff_time = now_utc - timedelta(seconds=30)
    recent_redemptions = {k: v for k, v in recent_redemptions.items() if v > cutoff_time}

    if passport.uses_remaining > 0:
        passport.uses_remaining -= 1
        db.session.add(passport)

        # ✅ Save Redemption for history tracking!
        redemption = Redemption(
            passport_id=passport.id,
            date_used=now_utc,
            redeemed_by=session.get("admin", "unknown")
        )
        db.session.add(redemption)

        db.session.commit()

        # ✅ Admin Action for activity_log
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Passport for {passport.user.name if passport.user else 'Unknown'} ({passport.pass_code}) was redeemed by {session.get('admin', 'unknown')}"
        ))
        db.session.commit()

        # ✅ Sleep to fix timestamp natural order
        time.sleep(0.5)

        # ✅ Fresh now_utc for email timestamp
        now_utc = datetime.now(timezone.utc)

        # ✅ Send confirmation email
        notify_pass_event(
            app=current_app._get_current_object(),
            event_type="pass_redeemed",
            pass_data=passport,
            activity=passport.activity,
            admin_email=session.get("admin"),
            timestamp=now_utc
        )

        flash(f"Session redeemed! {passport.uses_remaining} uses left.", "success")

        # Check if passport is now empty and activity offers renewal
        if passport.uses_remaining == 0:
            activity = passport.activity
            passport_type = passport.passport_type
            if (activity.offer_passport_renewal
                    and passport_type
                    and passport_type.status == 'active'):
                session['renewal_prompt'] = {
                    'pass_code': passport.pass_code,
                    'user_name': passport.user.name if passport.user else 'Unknown',
                    'activity_name': activity.name,
                    'passport_type_name': passport_type.name,
                    'sessions': passport_type.sessions_included,
                    'price': passport_type.price_per_user,
                }
    else:
        flash("No uses left on this passport!", "error")

    return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))


@app.route("/renew-passport/<pass_code>", methods=["POST"])
def renew_passport(pass_code):
    from models import Passport, AdminActionLog, Admin
    from utils import notify_pass_event, generate_pass_code
    from datetime import datetime, timezone
    import time

    if "admin" not in session:
        return redirect(url_for("login"))

    # Find the expired passport
    expired_passport = Passport.query.filter_by(pass_code=pass_code).first()
    if not expired_passport:
        flash("Passport not found.", "error")
        return redirect(url_for("dashboard"))

    # Validate: passport type must still be active
    passport_type = expired_passport.passport_type
    if not passport_type or passport_type.status != 'active':
        flash("Passport type is no longer active. Cannot renew.", "warning")
        return redirect(url_for("activity_dashboard", activity_id=expired_passport.activity_id))

    # Reuse the existing user
    user = expired_passport.user

    # Get current admin
    current_admin = Admin.query.filter_by(email=session.get("admin")).first()

    # Create new passport with same details
    new_passport = Passport(
        pass_code=generate_pass_code(),
        user_id=user.id,
        activity_id=expired_passport.activity_id,
        passport_type_id=passport_type.id,
        passport_type_name=passport_type.name,
        sold_amt=passport_type.price_per_user,
        uses_remaining=passport_type.sessions_included,
        created_by=current_admin.id if current_admin else None,
        created_dt=datetime.now(timezone.utc),
        paid=False,
        notes=f"Renewed from {pass_code}"
    )

    db.session.add(new_passport)
    db.session.commit()

    # Log admin action
    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=f"Passport renewed for {user.name} ({new_passport.pass_code}) from expired {pass_code}"
    ))
    db.session.commit()

    # Send new passport email
    time.sleep(0.5)
    now_utc = datetime.now(timezone.utc)
    notify_pass_event(
        app=current_app._get_current_object(),
        event_type="pass_created",
        pass_data=new_passport,
        activity=new_passport.activity,
        admin_email=session.get("admin"),
        timestamp=now_utc
    )

    flash(f"New passport created for {user.name}!", "success")
    return redirect(url_for("activity_dashboard", activity_id=expired_passport.activity_id))


@app.route("/mark-passport-paid/<int:passport_id>", methods=["POST"])
def mark_passport_paid(passport_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Passport, AdminActionLog
    import time
    from datetime import datetime, timezone, timedelta

    passport = db.session.get(Passport, passport_id)
    if not passport:
        flash("Passport not found!", "error")
        return redirect(url_for("dashboard2"))

    now_utc = datetime.now(timezone.utc)

    # ✅ Step 1: Mark Passport as Paid
    passport.paid = True
    passport.paid_date = now_utc
    passport.marked_paid_by = session.get("admin", "unknown")
    db.session.commit()

    # ✅ Step 2: Log Admin Action
    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=f"Passport for {passport.user.name if passport.user else 'Unknown'} ({passport.pass_code}) marked as PAID by {session.get('admin', 'unknown')}"
    ))
    db.session.commit()

    # ✅ Step 3: Sleep to separate timestamps naturally
    time.sleep(0.5)

    # ✅ Step 4: Refresh now_utc AFTER sleep
    now_utc = datetime.now(timezone.utc)

    # ✅ Step 5: Send confirmation email
    notify_pass_event(
        app=current_app._get_current_object(),
        event_type="payment_received",
        pass_data=passport,
        activity=passport.activity,
        admin_email=session.get("admin"),
        timestamp=now_utc
    )
    
    # SSE notifications removed for leaner performance

    flash(f" Passport {passport.pass_code} marked as paid. Email sent.", "success")
    return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))


@app.route("/passport/<int:passport_id>/send-reminder", methods=["POST"])
def send_passport_reminder(passport_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Passport, AdminActionLog
    from datetime import datetime, timezone

    passport = db.session.get(Passport, passport_id)
    if not passport:
        flash("Passport not found!", "error")
        return redirect(url_for("dashboard2"))

    if passport.paid:
        flash("Cannot send reminder for paid passport!", "error")
        return redirect(request.referrer or url_for("list_passports"))

    try:
        # Send payment reminder email (force send even if not late)
        notify_pass_event(
            app=current_app._get_current_object(),
            event_type="payment_late",
            pass_data=passport,
            activity=passport.activity,
            admin_email=session.get("admin"),
            timestamp=datetime.now(timezone.utc)
        )

        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Sent payment reminder to {passport.user.name if passport.user else 'Unknown'} for passport {passport.pass_code}"
        ))
        db.session.commit()

        flash(f"Payment reminder sent to {passport.user.name if passport.user else 'Unknown'}!", "success")
    except Exception as e:
        flash(f"Failed to send reminder: {str(e)}", "error")

    return redirect(request.referrer or url_for("list_passports"))


@app.route("/api/passport-type-dependencies/<int:passport_type_id>", methods=["GET"])
def check_passport_type_dependencies(passport_type_id):
    """Check if a passport type has dependencies (existing passports) that prevent deletion"""
    try:
        passport_type = PassportType.query.get_or_404(passport_type_id)
        
        # Count passports using this passport type
        passport_count = Passport.query.filter_by(passport_type_id=passport_type_id).count()
        
        # Count signups using this passport type
        signup_count = Signup.query.filter_by(passport_type_id=passport_type_id).count()
        
        has_dependencies = passport_count > 0 or signup_count > 0
        
        return jsonify({
            "success": True,
            "has_dependencies": has_dependencies,
            "passport_count": passport_count,
            "signup_count": signup_count,
            "passport_type_name": passport_type.name,
            "can_delete": not has_dependencies
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/passport-type-archive/<int:passport_type_id>", methods=["POST"])
@csrf.exempt
def archive_passport_type(passport_type_id):
    """Archive a passport type instead of deleting it"""
    try:
        passport_type = PassportType.query.get_or_404(passport_type_id)
        
        # Update passport type status to archived
        passport_type.status = "archived"
        passport_type.archived_at = datetime.now(timezone.utc)
        passport_type.archived_by = session.get("admin", "system")
        
        # Preserve passport type names in existing passports
        passports = Passport.query.filter_by(passport_type_id=passport_type_id).all()
        for passport in passports:
            if not passport.passport_type_name:  # Only update if not already preserved
                passport.passport_type_name = passport_type.name
        
        db.session.commit()

        # Log the action
        from utils import log_admin_action
        log_admin_action(f"Archived passport type: {passport_type.name} (ID: {passport_type_id})")

        return jsonify({
            "success": True,
            "message": f"Passport type '{passport_type.name}' has been deleted successfully.",
            "passport_type_name": passport_type.name
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ================================
# 📧 EMAIL CONNECTION TEST API
# ================================
@app.route("/api/test-email-connection", methods=["POST"])
def test_email_connection():
    """Test email server connection without sending an email"""
    if "admin" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        import smtplib
        import ssl
        
        # Get connection settings from request
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
            
        mail_server = data.get('mail_server')
        mail_port = int(data.get('mail_port', 587))
        mail_use_tls = data.get('mail_use_tls', True)
        mail_username = data.get('mail_username')
        mail_password = data.get('mail_password')
        
        if not all([mail_server, mail_username]):
            return jsonify({"success": False, "error": "Mail server and username are required"}), 400
        
        # Test connection
        try:
            # Create SMTP connection
            if mail_port == 465:  # SSL
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(mail_server, mail_port, context=context)
            else:  # Standard or TLS
                server = smtplib.SMTP(mail_server, mail_port)
                if mail_use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # Test authentication if password provided
            if mail_password:
                server.login(mail_username, mail_password)
            
            # Close connection
            server.quit()
            
            # Log successful test
            from utils import log_admin_action
            log_admin_action(f"Successfully tested email connection to {mail_server}:{mail_port}")
            
            return jsonify({
                "success": True, 
                "message": f"Successfully connected to {mail_server}:{mail_port}"
            })
            
        except smtplib.SMTPAuthenticationError:
            return jsonify({
                "success": False, 
                "error": "Authentication failed. Please check your username and password."
            }), 400
        except smtplib.SMTPConnectError:
            return jsonify({
                "success": False, 
                "error": f"Could not connect to {mail_server}:{mail_port}. Please check server and port."
            }), 400
        except smtplib.SMTPServerDisconnected:
            return jsonify({
                "success": False, 
                "error": "Server disconnected unexpectedly. Please try again."
            }), 400
        except Exception as smtp_error:
            return jsonify({
                "success": False, 
                "error": f"SMTP Error: {str(smtp_error)}"
            }), 400
            
    except ValueError as ve:
        return jsonify({"success": False, "error": f"Invalid port number: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Connection test failed: {str(e)}"}), 500

# ================================
# 📋 SURVEY SYSTEM ROUTES
# ================================

@app.route("/create-survey", methods=["POST"])
def create_survey():
    """Create a new survey for an activity"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    try:
        activity_id = request.form.get("activity_id")
        survey_name = request.form.get("survey_name")
        survey_description = request.form.get("survey_description", "")
        template_id = request.form.get("template_id")
        passport_type_id = request.form.get("passport_type_id")
        
        # Validate required fields
        if not activity_id or not survey_name or not template_id:
            flash("Missing required fields", "error")
            return redirect(url_for("activity_dashboard", activity_id=activity_id))
        
        # Verify activity exists
        activity = Activity.query.get_or_404(activity_id)
        
        # Get template from database or use hardcoded fallback
        if template_id.isdigit():
            # Numeric template ID - get from database
            template = db.session.get(SurveyTemplate, int(template_id))
            if not template:
                flash("Invalid survey template", "error")
                return redirect(url_for("activity_dashboard", activity_id=activity_id))
        else:
            # String template ID - get hardcoded template
            template_questions = get_survey_template_questions(template_id)
            if not template_questions:
                flash("Invalid survey template", "error")
                return redirect(url_for("activity_dashboard", activity_id=activity_id))
            
            # Create survey template in database if it doesn't exist
            template = get_or_create_survey_template(template_id, template_questions)
        
        # Generate unique survey token
        survey_token = generate_survey_token()
        
        # Create the survey
        survey = Survey(
            activity_id=activity_id,
            template_id=template.id,
            passport_type_id=passport_type_id if passport_type_id else None,
            name=survey_name,
            description=survey_description,
            survey_token=survey_token,
            created_by=session.get("admin_id"),
            status="active"
        )
        
        db.session.add(survey)
        db.session.commit()
        
        flash(f"Survey '{survey_name}' created successfully!", "success")
        return redirect(url_for("activity_dashboard", activity_id=activity_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating survey: {str(e)}", "error")
        return redirect(url_for("activity_dashboard", activity_id=activity_id))


@app.route("/api/survey-template/<int:template_id>", methods=["GET"])
def api_get_survey_template(template_id):
    """API endpoint to get survey template questions as JSON"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        template = SurveyTemplate.query.get(template_id)
        if not template:
            return jsonify({"error": "Template not found"}), 404

        # Parse questions JSON
        questions_data = json.loads(template.questions)
        questions = questions_data.get("questions", [])

        return jsonify({
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "questions": questions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/create-quick-survey", methods=["POST"])
def create_quick_survey():
    """Create a quick survey using a selected template"""
    if "admin" not in session:
        return redirect(url_for("login"))

    # Import logging function
    from utils import log_admin_action

    try:
        activity_id = request.form.get("activity_id")
        survey_name = request.form.get("survey_name", "").strip()
        template_id = request.form.get("template_id")

        if not activity_id or not survey_name or not template_id:
            flash("Activity, survey name, and template are required", "error")
            return redirect(url_for("list_surveys"))

        # Verify activity exists
        activity = db.session.get(Activity, activity_id)
        if not activity:
            flash("Activity not found", "error")
            return redirect(url_for("dashboard"))

        # Verify template exists
        template = db.session.get(SurveyTemplate, template_id)
        if not template:
            flash("Survey template not found", "error")
            return redirect(url_for("list_surveys"))

        # Generate unique survey token
        survey_token = generate_survey_token()

        # Create the survey
        survey = Survey(
            activity_id=activity_id,
            template_id=template.id,
            name=survey_name,
            description=f"Feedback survey for {activity.name} using {template.name}",
            survey_token=survey_token,
            status="active"
        )

        db.session.add(survey)
        db.session.commit()

        # Log the action
        log_admin_action(f"Created quick survey '{survey_name}' for activity '{activity.name}' using template '{template.name}'")

        flash(f"Survey '{survey_name}' created successfully using {template.name} template", "success")
        return redirect(url_for("list_surveys"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error creating survey: {str(e)}", "error")
        return redirect(url_for("list_surveys"))


@app.route("/survey/<survey_token>")
def take_survey(survey_token):
    """Public survey taking page"""
    try:
        survey = Survey.query.filter_by(survey_token=survey_token).first_or_404()
        
        if survey.status != "active":
            return render_template("survey_closed.html", survey=survey)
        
        # Check for specific user token (from email invitations)
        user_token = request.args.get('token')
        if user_token:
            # Find the user's response record and mark as started
            response = SurveyResponse.query.filter_by(
                survey_id=survey.id,
                response_token=user_token
            ).first()
            
            if response and not response.started_dt:
                response.started_dt = datetime.now(timezone.utc)
                db.session.commit()
        
        # Get survey questions from template
        template_questions = json.loads(survey.template.questions)
        
        return render_template("survey_form.html", 
                             survey=survey, 
                             questions=template_questions)
        
    except Exception as e:
        flash(f"Error loading survey: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/survey/<survey_token>/submit", methods=["POST"])
def submit_survey_response(survey_token):
    """Submit survey response"""
    try:
        survey = Survey.query.filter_by(survey_token=survey_token).first_or_404()
        
        if survey.status != "active":
            flash("This survey is no longer accepting responses", "error")
            return redirect(url_for("take_survey", survey_token=survey_token))
        
        # Collect responses
        responses = {}
        template_questions = json.loads(survey.template.questions)

        for question in template_questions.get("questions", []):
            question_id = str(question["id"])
            response_value = request.form.get(f"question_{question_id}")

            if question.get("required", False) and not response_value:
                flash(f"Please answer question: {question['question']}", "error")
                return redirect(url_for("take_survey", survey_token=survey_token))

            if response_value:
                responses[question_id] = response_value

        # Check if this is from an email invitation with response token
        response_token = request.form.get("response_token", "").strip()

        if response_token:
            # User came via email invitation - find their existing response record
            survey_response = SurveyResponse.query.filter_by(
                survey_id=survey.id,
                response_token=response_token
            ).first()

            if survey_response:
                # Update existing response record
                survey_response.responses = json.dumps(responses)
                survey_response.completed = True
                survey_response.completed_dt = datetime.now(timezone.utc)
                survey_response.ip_address = request.remote_addr
                survey_response.user_agent = request.headers.get('User-Agent')
            else:
                # Token not found - this shouldn't happen but handle gracefully
                flash("Invalid survey token. Please use the link from your email.", "error")
                return redirect(url_for("take_survey", survey_token=survey_token))
        else:
            # No response token - this is an anonymous submission
            # Generate new token for this anonymous response
            new_response_token = generate_response_token()

            # Get user ID from session or create anonymous user
            user_id = session.get("user_id")
            if not user_id:
                # For anonymous responses, try to find or create a user
                anonymous_user = User.query.filter_by(email="anonymous@survey.local").first()
                if not anonymous_user:
                    anonymous_user = User(
                        name="Anonymous Survey User",
                        email="anonymous@survey.local"
                    )
                    db.session.add(anonymous_user)
                    db.session.flush()  # Get the ID
                user_id = anonymous_user.id

            survey_response = SurveyResponse(
                survey_id=survey.id,
                user_id=user_id,
                response_token=new_response_token,
                responses=json.dumps(responses),
                completed=True,
                completed_dt=datetime.now(timezone.utc),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )

            db.session.add(survey_response)

        db.session.commit()
        
        return render_template("survey_thank_you.html", survey=survey)
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error submitting survey: {str(e)}", "error")
        return redirect(url_for("take_survey", survey_token=survey_token))


def get_survey_template_questions(template_id):
    """Get questions for a survey template"""
    templates = {
        "default": {
            "name": "Activity Feedback Survey",
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "How would you rate your overall experience?",
                    "options": ["Excellent", "Good", "Fair", "Poor"],
                    "required": True
                },
                {
                    "id": 2,
                    "type": "multiple_choice",
                    "question": "How likely are you to recommend this activity to others?",
                    "options": ["Very likely", "Likely", "Unlikely", "Very unlikely"],
                    "required": True
                },
                {
                    "id": 3,
                    "type": "multiple_choice",
                    "question": "What did you like most about this activity?",
                    "options": ["Instruction quality", "Facilities", "Organization", "Other participants"],
                    "required": False
                },
                {
                    "id": 4,
                    "type": "multiple_choice",
                    "question": "Would you participate in this activity again?",
                    "options": ["Definitely", "Probably", "Maybe", "No"],
                    "required": True
                },
                {
                    "id": 5,
                    "type": "open_ended",
                    "question": "Any additional feedback or suggestions for improvement?",
                    "required": False,
                    "max_length": 500
                }
            ]
        },
        "quick": {
            "name": "Quick Feedback Survey",
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "How satisfied were you with this activity?",
                    "options": ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied"],
                    "required": True
                },
                {
                    "id": 2,
                    "type": "multiple_choice",
                    "question": "Would you recommend this to a friend?",
                    "options": ["Yes", "Maybe", "No"],
                    "required": True
                },
                {
                    "id": 3,
                    "type": "open_ended",
                    "question": "What could we improve?",
                    "required": False,
                    "max_length": 300
                }
            ]
        }
    }
    
    return templates.get(template_id)


def get_or_create_survey_template(template_id, template_data):
    """Get existing template or create new one"""
    # Check if template already exists
    template = SurveyTemplate.query.filter_by(name=template_data["name"]).first()
    
    if not template:
        template = SurveyTemplate(
            name=template_data["name"],
            description=f"Default {template_data['name'].lower()}",
            questions=json.dumps(template_data),
            status="active"
        )
        db.session.add(template)
        db.session.flush()  # To get the ID
    
    return template


def create_default_survey_template():
    """Create and seed the default Post-Activity Feedback survey template"""
    template_name = "Post-Activity Feedback"
    
    # Check if template already exists
    existing_template = SurveyTemplate.query.filter_by(name=template_name).first()
    if existing_template:
        return existing_template
    
    # Create the default survey questions
    default_questions = [
        {
            "id": 1,
            "text": "How would you rate your overall satisfaction with this activity?",
            "type": "rating",
            "required": True,
            "min_rating": 1,
            "max_rating": 5,
            "labels": {
                "1": "Very Dissatisfied",
                "2": "Dissatisfied", 
                "3": "Neutral",
                "4": "Satisfied",
                "5": "Very Satisfied"
            }
        },
        {
            "id": 2,
            "text": "How would you rate the instructor/facilitator?",
            "type": "rating",
            "required": True,
            "min_rating": 1,
            "max_rating": 5,
            "labels": {
                "1": "Poor",
                "2": "Fair",
                "3": "Good", 
                "4": "Very Good",
                "5": "Excellent"
            }
        },
        {
            "id": 3,
            "text": "What did you enjoy most about this activity?",
            "type": "text",
            "required": False,
            "max_length": 500,
            "placeholder": "Please share what you enjoyed most..."
        },
        {
            "id": 4,
            "text": "What could be improved for future activities?",
            "type": "text",
            "required": False,
            "max_length": 500,
            "placeholder": "Please share your suggestions for improvement..."
        },
        {
            "id": 5,
            "text": "Would you recommend this activity to others?",
            "type": "multiple_choice",
            "required": True,
            "allow_multiple": False,
            "options": [
                {"value": "definitely_yes", "text": "Definitely yes"},
                {"value": "probably_yes", "text": "Probably yes"},
                {"value": "not_sure", "text": "Not sure"},
                {"value": "probably_no", "text": "Probably no"},
                {"value": "definitely_no", "text": "Definitely no"}
            ]
        }
    ]
    
    # Create the template
    template = SurveyTemplate(
        name=template_name,
        description="Standard post-activity feedback survey with ratings, open feedback, and recommendation questions",
        questions=json.dumps({"questions": default_questions}),
        status="active"
    )
    
    try:
        db.session.add(template)
        db.session.commit()
        print(f"Default survey template '{template_name}' created successfully")
        return template
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default survey template: {str(e)}")
        return None


def create_french_simple_survey_template():
    """Create a simple French post-activity feedback survey template"""
    template_name = "Sondage d'Activité - Simple (questions)"

    # Check if template already exists - if so, delete it to recreate with proper format
    existing_template = SurveyTemplate.query.filter_by(name=template_name).first()
    if existing_template:
        try:
            db.session.delete(existing_template)
            db.session.commit()
            print(f" Deleted existing French template to recreate with proper format")
        except Exception as e:
            db.session.rollback()
            print(f"Warning: Could not delete existing template: {str(e)}")

    # Create French survey questions with UI-compatible format
    # IMPORTANT: Use "question" key (not "text") and simple string arrays for options
    french_questions = [
        {
            "id": 1,
            "question": "Comment évaluez-vous votre satisfaction globale concernant cette activité?",
            "type": "rating",
            "required": True,
            "min_rating": 1,
            "max_rating": 5,
            "labels": {
                "1": "Très insatisfait",
                "2": "Insatisfait",
                "3": "Neutre",
                "4": "Satisfait",
                "5": "Très satisfait"
            }
        },
        {
            "id": 2,
            "question": "Le prix demandé pour cette activité est-il justifié?",
            "type": "multiple_choice",
            "required": True,
            "options": [
                "Trop cher",
                "Un peu cher",
                "Juste",
                "Bon rapport qualité-prix",
                "Excellent rapport qualité-prix"
            ]
        },
        {
            "id": 3,
            "question": "Recommanderiez-vous cette activité à un ami?",
            "type": "multiple_choice",
            "required": True,
            "options": [
                "Certainement",
                "Probablement",
                "Peut-être",
                "Probablement pas",
                "Certainement pas"
            ]
        },
        {
            "id": 4,
            "question": "Comment évaluez-vous l'emplacement/les installations?",
            "type": "multiple_choice",
            "required": False,
            "options": [
                "Excellent",
                "Très bien",
                "Bien",
                "Moyen",
                "Insuffisant"
            ]
        },
        {
            "id": 5,
            "question": "L'horaire de l'activité vous convenait-il?",
            "type": "multiple_choice",
            "required": False,
            "options": [
                "Parfaitement",
                "Bien",
                "Acceptable",
                "Peu pratique",
                "Très peu pratique"
            ]
        },
        {
            "id": 6,
            "question": "Qu'avez-vous le plus apprécié de cette activité?",
            "type": "open_ended",
            "required": False,
            "max_length": 300,
            "placeholder": "Partagez ce que vous avez le plus aimé..."
        },
        {
            "id": 7,
            "question": "Qu'est-ce qui pourrait être amélioré?",
            "type": "open_ended",
            "required": False,
            "max_length": 300,
            "placeholder": "Partagez vos suggestions d'amélioration..."
        },
        {
            "id": 8,
            "question": "Souhaiteriez-vous participer à nouveau à une activité similaire?",
            "type": "multiple_choice",
            "required": True,
            "options": [
                "Oui, certainement",
                "Oui, probablement",
                "Peut-être",
                "Probablement pas",
                "Non"
            ]
        }
    ]

    # Create the template
    template = SurveyTemplate(
        name=template_name,
        description="Sondage simple en français pour recueillir les retours après une activité ponctuelle (tournoi de golf, événement sportif, etc.). Temps de réponse: ~2 minutes.",
        questions=json.dumps({"questions": french_questions}),
        status="active"
    )

    try:
        db.session.add(template)
        db.session.commit()
        print(f"French survey template '{template_name}' created successfully with proper format")
        return template
    except Exception as e:
        db.session.rollback()
        print(f"Error creating French survey template: {str(e)}")
        return None


# ================================
# Survey Template Management Routes
# ================================

@app.route("/survey-templates")
def list_survey_templates():
    if "admin" not in session:
        return redirect(url_for("login"))

    # Get filter parameters
    q = request.args.get("q", "").strip()
    usage_filter = request.args.get("usage_filter", "")
    show_all_param = request.args.get("show_all", "")

    # Query ALL templates first (for statistics)
    all_templates = SurveyTemplate.query.all()
    all_templates_count = SurveyTemplate.query.count()

    # Calculate usage statistics for ALL templates
    for template in all_templates:
        template.usage_count = Survey.query.filter_by(template_id=template.id).count()
        # Parse questions to get count
        try:
            questions_data = json.loads(template.questions)
            template.question_count = len(questions_data.get('questions', []))
        except:
            template.question_count = 0

    # Calculate statistics from ALL templates (before filtering)
    used_templates = len([t for t in all_templates if t.usage_count > 0])

    statistics = {
        'total_templates': all_templates_count,
        'used_templates': used_templates,
    }

    # Set default filter if no parameters - "used" is now the default
    if not usage_filter and show_all_param != "true":
        usage_filter = "used"

    # Base query for filtered results
    query = SurveyTemplate.query.order_by(SurveyTemplate.created_dt.desc())

    # Apply search filter to query
    if q:
        query = query.filter(
            db.or_(
                SurveyTemplate.name.ilike(f"%{q}%"),
                SurveyTemplate.description.ilike(f"%{q}%")
            )
        )

    # Get filtered templates
    templates = query.all()

    # Calculate usage statistics for filtered templates (if not already done)
    for template in templates:
        if not hasattr(template, 'usage_count'):
            template.usage_count = Survey.query.filter_by(template_id=template.id).count()
            try:
                questions_data = json.loads(template.questions)
                template.question_count = len(questions_data.get('questions', []))
            except:
                template.question_count = 0

    # Apply usage filter to templates list
    if usage_filter == "used":
        templates = [t for t in templates if t.usage_count > 0]

    return render_template("survey_templates.html",
                         templates=templates,
                         statistics=statistics,
                         current_filters={
                             'q': q,
                             'usage_filter': usage_filter,
                             'show_all': show_all_param == 'true'
                         })


@app.route("/create-survey-template", methods=["GET", "POST"])
def create_survey_template():
    if "admin" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("Template name is required", "error")
            return redirect(url_for("create_survey_template"))
        
        # Build questions from form data
        questions = []
        question_index = 1
        
        while f"question_{question_index}" in request.form:
            question_text = request.form.get(f"question_{question_index}", "").strip()
            question_type = request.form.get(f"question_type_{question_index}", "multiple_choice")
            required = f"required_{question_index}" in request.form
            
            if question_text:
                question_data = {
                    "id": question_index,
                    "question": question_text,
                    "type": question_type,
                    "required": required
                }
                
                if question_type == "multiple_choice":
                    options = []
                    option_index = 1
                    while f"question_{question_index}_option_{option_index}" in request.form:
                        option = request.form.get(f"question_{question_index}_option_{option_index}", "").strip()
                        if option:
                            options.append(option)
                        option_index += 1
                    question_data["options"] = options
                
                elif question_type == "open_ended":
                    max_length = request.form.get(f"max_length_{question_index}", "")
                    if max_length:
                        try:
                            question_data["max_length"] = int(max_length)
                        except ValueError:
                            pass
                
                questions.append(question_data)
            
            question_index += 1
        
        if not questions:
            flash("At least one question is required", "error")
            return redirect(url_for("create_survey_template"))
        
        # Create template
        template = SurveyTemplate(
            name=name,
            description=description,
            questions=json.dumps({"questions": questions}),
            created_dt=datetime.now(timezone.utc)
        )
        
        try:
            db.session.add(template)
            db.session.commit()
            flash(f"Survey template '{name}' created successfully", "success")
            return redirect(url_for("list_survey_templates"))
        except Exception as e:
            db.session.rollback()
            flash("Error creating survey template", "error")
            return redirect(url_for("create_survey_template"))
    
    return render_template("create_survey_template.html")


@app.route("/edit-survey-template/<int:template_id>", methods=["GET", "POST"])
def edit_survey_template(template_id):
    if "admin" not in session:
        return redirect(url_for("login"))
    
    template = SurveyTemplate.query.get_or_404(template_id)
    
    if request.method == "POST":
        template.name = request.form.get("name", "").strip()
        template.description = request.form.get("description", "").strip()
        
        if not template.name:
            flash("Template name is required", "error")
            return redirect(url_for("edit_survey_template", template_id=template_id))
        
        # Build questions from form data (same logic as create)
        questions = []
        question_index = 1
        
        while f"question_{question_index}" in request.form:
            question_text = request.form.get(f"question_{question_index}", "").strip()
            question_type = request.form.get(f"question_type_{question_index}", "multiple_choice")
            required = f"required_{question_index}" in request.form

            if question_text:
                question_data = {
                    "id": question_index,
                    "question": question_text,
                    "type": question_type,
                    "required": required
                }

                if question_type == "rating":
                    # For rating questions, preserve existing rating data from original template
                    # Rating questions are read-only in the UI, so we need to fetch original data
                    try:
                        original_data = json.loads(template.questions)
                        original_questions = original_data.get("questions", [])
                        original_q = next((q for q in original_questions if q.get("id") == question_index), None)
                        if original_q:
                            question_data["min_rating"] = original_q.get("min_rating", 1)
                            question_data["max_rating"] = original_q.get("max_rating", 5)
                            question_data["labels"] = original_q.get("labels", {})
                    except:
                        # Fallback defaults if we can't find original
                        question_data["min_rating"] = 1
                        question_data["max_rating"] = 5
                        question_data["labels"] = {}

                elif question_type == "multiple_choice":
                    options = []
                    option_index = 1
                    while f"question_{question_index}_option_{option_index}" in request.form:
                        option = request.form.get(f"question_{question_index}_option_{option_index}", "").strip()
                        if option:
                            options.append(option)
                        option_index += 1
                    question_data["options"] = options

                elif question_type == "open_ended" or question_type == "text":
                    max_length = request.form.get(f"max_length_{question_index}", "")
                    if max_length:
                        try:
                            question_data["max_length"] = int(max_length)
                        except ValueError:
                            pass

                questions.append(question_data)

            question_index += 1

        if not questions:
            flash("At least one question is required", "error")
            return redirect(url_for("edit_survey_template", template_id=template_id))
        
        template.questions = json.dumps({"questions": questions})
        
        try:
            db.session.commit()
            flash(f"Survey template '{template.name}' updated successfully", "success")
            return redirect(url_for("list_survey_templates"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating survey template", "error")
    
    # Parse questions for editing with backward compatibility
    try:
        questions_data = json.loads(template.questions)
        raw_questions = questions_data.get('questions', [])

        # Normalize questions to standard format for editing
        # Standard format: {"question": "...", "type": "multiple_choice|open_ended", "options": ["str1", "str2"]}
        normalized_questions = []
        for q in raw_questions:
            normalized = {
                "id": q.get("id", len(normalized_questions) + 1),
                "required": q.get("required", True)
            }

            # Handle question text (both "text" and "question" keys)
            normalized["question"] = q.get("question") or q.get("text", "")

            # Handle question type normalization
            q_type = q.get("type", "multiple_choice")
            if q_type == "rating":
                # Keep rating questions as rating
                normalized["type"] = "rating"
                # Copy rating-specific fields
                if "min_rating" in q:
                    normalized["min_rating"] = q["min_rating"]
                if "max_rating" in q:
                    normalized["max_rating"] = q["max_rating"]
                if "labels" in q:
                    normalized["labels"] = q["labels"]
            elif q_type == "multiple_choice":
                normalized["type"] = "multiple_choice"
            elif q_type == "text":
                normalized["type"] = "open_ended"
            else:
                normalized["type"] = q_type

            # Handle options (both object format and string array format)
            if "options" in q and normalized["type"] != "rating":
                if isinstance(q["options"], list) and len(q["options"]) > 0:
                    if isinstance(q["options"][0], dict):
                        # Convert object format to string array
                        normalized["options"] = [opt.get("text", str(opt)) for opt in q["options"]]
                    else:
                        # Already string array
                        normalized["options"] = q["options"]
                else:
                    normalized["options"] = []
            else:
                normalized["options"] = []

            # Handle max_length for open-ended questions
            if "max_length" in q:
                normalized["max_length"] = q["max_length"]

            normalized_questions.append(normalized)

        template.parsed_questions = normalized_questions
    except Exception as e:
        print(f"Error parsing questions: {e}")
        template.parsed_questions = []

    return render_template("edit_survey_template.html", template=template)


@app.route("/delete-survey-template/<int:template_id>", methods=["POST"])
def delete_survey_template(template_id):
    if "admin" not in session:
        return redirect(url_for("login"))
    
    template = SurveyTemplate.query.get_or_404(template_id)
    
    # Check if template is being used by any surveys
    surveys_using_template = Survey.query.filter_by(template_id=template_id).count()
    if surveys_using_template > 0:
        flash(f"Cannot delete template '{template.name}' - it is being used by {surveys_using_template} surveys", "error")
        return redirect(url_for("list_survey_templates"))
    
    try:
        db.session.delete(template)
        db.session.commit()
        flash(f"Survey template '{template.name}' deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting survey template", "error")
    
    return redirect(url_for("list_survey_templates"))


# ================================
# Enhanced Survey Action Routes
# ================================

@app.route("/survey/<int:survey_id>/results")
def survey_results(survey_id):
    if "admin" not in session:
        return redirect(url_for("login"))
    
    survey = Survey.query.get_or_404(survey_id)
    responses = SurveyResponse.query.filter_by(survey_id=survey_id).all()
    
    # Parse questions for analysis
    try:
        questions_data = json.loads(survey.template.questions)
        questions = questions_data.get('questions', [])
    except:
        questions = []
    
    # Analyze responses
    analysis = {}
    for question in questions:
        question_id = str(question['id'])
        analysis[question_id] = {
            'question': question,
            'responses': [],
            'summary': {}
        }

        for response in responses:
            if response.responses:
                try:
                    response_data = json.loads(response.responses)
                    if question_id in response_data:
                        analysis[question_id]['responses'].append(response_data[question_id])
                except (json.JSONDecodeError, TypeError):
                    continue  # Skip malformed responses
        
        # Generate summary based on question type
        if question['type'] == 'multiple_choice':
            summary = {}
            for resp in analysis[question_id]['responses']:
                summary[resp] = summary.get(resp, 0) + 1
            analysis[question_id]['summary'] = summary
        else:
            analysis[question_id]['summary'] = {'count': len(analysis[question_id]['responses'])}
    
    return render_template("survey_results.html", 
                         survey=survey, 
                         responses=responses, 
                         analysis=analysis)


@app.route("/send-survey-invitations/<int:survey_id>", methods=["POST"])
def send_survey_invitations(survey_id):
    import sys
    log_file = open("/tmp/survey_debug.log", "a")
    def log(msg):
        print(msg)
        log_file.write(msg + "\n")
        log_file.flush()
        sys.stdout.flush()

    log(f"\n{'='*80}")
    log(f"🚀 SEND_SURVEY_INVITATIONS ROUTE CALLED - Survey ID: {survey_id}")
    log(f"{'='*80}\n")

    if "admin" not in session:
        log("No admin in session - redirecting to login")
        log_file.close()
        return redirect(url_for("login"))

    from sqlalchemy.orm import joinedload
    print(f"📥 Loading survey with eager loading...")
    survey = db.session.get(Survey, survey_id, options=[
        joinedload(Survey.activity)
    ])

    if not survey:
        print(f"Survey {survey_id} not found!")
        flash("Survey not found", "error")
        return redirect(url_for("list_surveys"))

    print(f"Survey loaded: {survey.name}")
    print(f"   Activity: {survey.activity.name}")
    
    # For surveys, include all participants (paid and unpaid)
    # Eagerly load user and activity relationships to avoid detached instance errors
    if survey.passport_type_id:
        passports = Passport.query.options(
            joinedload(Passport.user),
            joinedload(Passport.activity)
        ).filter_by(
            activity_id=survey.activity_id,
            passport_type_id=survey.passport_type_id
        ).all()
    else:
        passports = Passport.query.options(
            joinedload(Passport.user),
            joinedload(Passport.activity)
        ).filter_by(
            activity_id=survey.activity_id
        ).all()
    
    # Debug information
    all_passports_count = Passport.query.filter_by(activity_id=survey.activity_id).count()
    print(f"DEBUG: Survey '{survey.name}' (ID:{survey.id}) for Activity ID:{survey.activity_id}")
    print(f"DEBUG: Found {len(passports)} eligible passports, {all_passports_count} total passports for this activity")
    print(f"DEBUG: Survey passport_type_id: {survey.passport_type_id}")
    
    if not passports:
        flash(f"No participants found for survey '{survey.name}' in activity {survey.activity_id}. Found {all_passports_count} total passports for this activity.", "warning")
        return redirect(url_for("list_surveys"))
    
    # Check if this is a resend request
    resend_all = request.form.get('resend_all') == 'true'
    print(f"DEBUG: Resend all invitations: {resend_all}")
    
    # Parse questions to get count for email
    try:
        questions_data = json.loads(survey.template.questions)
        question_count = len(questions_data.get('questions', []))
    except:
        question_count = 0
    
    sent_count = 0
    already_invited = 0
    failed_count = 0
    failed_emails = []

    for passport in passports:
        # Check if user already has a response token for this survey
        existing_response = SurveyResponse.query.filter_by(
            survey_id=survey_id,
            user_id=passport.user_id
        ).first()
        
        if not existing_response or resend_all:
            # Create response record with unique token (or resend to existing)
            if existing_response and resend_all:
                # Update existing record's invitation timestamp
                response = existing_response
                response.invited_dt = datetime.now(timezone.utc)
            else:
                # Create new response record
                response = SurveyResponse(
                    survey_id=survey_id,
                    user_id=passport.user_id,
                    passport_id=passport.id,
                    response_token=generate_response_token(),
                    invited_dt=datetime.now(timezone.utc),
                    created_dt=datetime.now(timezone.utc)
                )
                db.session.add(response)
            
            # Send email invitation
            try:
                log(f"🔵 Preparing to send survey invitation to {passport.user.email}")
                survey_url = url_for('take_survey', survey_token=survey.survey_token,
                                   _external=True) + f"?token={response.response_token}"
                log(f"🔵 Survey URL created: {survey_url}")

                # Use activity-specific email templates
                from utils import get_email_context, get_setting
                print(f"🔵 get_email_context and get_setting imported")

                # Build logo URL in request context (url_for needs request context)
                if survey.activity and survey.activity.logo_filename:
                    activity_logo_url = url_for('static', filename=f'uploads/logos/{survey.activity.logo_filename}')
                else:
                    org_logo = get_setting('LOGO_FILENAME', 'logo.png')
                    activity_logo_url = url_for('static', filename=f'uploads/{org_logo}')

                # Build base context
                base_context = {
                    'user_name': passport.user.name or 'Participant',
                    'activity': survey.activity,  # Add activity object for Jinja2 template rendering
                    'activity_name': survey.activity.name,
                    'survey_name': survey.name,
                    'survey_url': survey_url,
                    'question_count': question_count,
                    'organization_name': get_setting('ORG_NAME', 'Fondation LHGI'),
                    'organization_address': get_setting('ORG_ADDRESS', ''),
                    'support_email': get_setting('SUPPORT_EMAIL', 'support@minipass.me'),
                    'activity_logo_url': activity_logo_url  # Add logo URL to base context
                }

                # Get email context using activity-specific templates
                email_context = get_email_context(survey.activity, 'survey_invitation', base_context)

                # CRITICAL FIX: Render Jinja2 variables in customized template strings
                # The customized templates contain Jinja2 variables like {{ activity_name }} that need to be rendered
                from jinja2 import Template as JinjaTemplate

                # Build rendering context with all available variables
                render_context = {
                    'user_name': passport.user.name or 'Participant',
                    'activity_name': survey.activity.name,
                    'activity': survey.activity,  # For accessing activity properties
                    'survey_name': survey.name,
                    'survey_url': survey_url,
                    'question_count': question_count,
                    'organization_name': get_setting('ORG_NAME', 'Fondation LHGI'),
                    'organization_address': get_setting('ORG_ADDRESS', ''),
                    'support_email': get_setting('SUPPORT_EMAIL', 'support@minipass.me'),
                }

                # Render subject, title, intro_text, and conclusion_text if they contain Jinja2 variables
                subject_template = email_context.get('subject', f"{survey.name} - Your Feedback Requested")
                title_template = email_context.get('title', 'We\'d Love Your Feedback!')
                intro_template = email_context.get('intro_text', '<p>Thank you for participating in our activity! We hope you had a great experience and would love to hear your thoughts.</p>')
                conclusion_template = email_context.get('conclusion_text', '<p>Thank you for helping us create better experiences!</p>')

                subject = JinjaTemplate(subject_template).render(**render_context)
                rendered_title = JinjaTemplate(title_template).render(**render_context)
                rendered_intro = JinjaTemplate(intro_template).render(**render_context)
                rendered_conclusion = JinjaTemplate(conclusion_template).render(**render_context)

                template_name = 'survey_invitation'  # Match the template folder name

                # Note: inline_images and logo loading is handled automatically by send_email_async()

                context = {
                    'user_name': passport.user.name or 'Participant',
                    'activity_name': survey.activity.name,
                    'survey_name': survey.name,
                    'survey_url': survey_url,
                    'question_count': question_count,
                    'organization_name': get_setting('ORG_NAME', 'Fondation LHGI'),
                    'organization_address': get_setting('ORG_ADDRESS', ''),
                    'support_email': get_setting('SUPPORT_EMAIL', 'support@minipass.me'),
                    'unsubscribe_url': f"https://minipass.me/unsubscribe?email={passport.user.email}",
                    'privacy_url': "https://minipass.me/privacy",
                    # Survey email template variables - now RENDERED (Jinja2 variables already processed)
                    'title': rendered_title,
                    'intro_text': rendered_intro,
                    'conclusion_text': rendered_conclusion,
                    # CRITICAL: Flag to prevent send_email_async from re-applying get_email_context()
                    '_skip_email_context': True
                }
                
                print(f"🔵 About to call send_email_async()")
                print(f"🔵 Template: {template_name}")
                print(f"🔵 Subject: {subject}")
                print(f"🔵 To: {passport.user.email}")
                print(f"🔵 Context keys: {list(context.keys())}")

                send_email_async(
                    app=current_app._get_current_object(),
                    user=passport.user,
                    activity=survey.activity,  # Pass activity to use customized email templates
                    subject=subject,
                    to_email=passport.user.email,
                    template_name=template_name,
                    context=context
                )

                print(f"send_email_async() called successfully for {passport.user.email}")
                sent_count += 1
                
            except Exception as e:
                # Log error but continue with other invitations
                import traceback
                import io
                log(f"Failed to send survey invitation to {passport.user.email}")
                log(f"Error: {e}")
                log(f"Traceback:")
                tb_output = io.StringIO()
                traceback.print_exc(file=tb_output)
                log(tb_output.getvalue())
                failed_count += 1
                failed_emails.append(passport.user.email)
                
        elif existing_response and not existing_response.invited_dt:
            # User exists but hasn't been invited yet (maybe created manually)
            existing_response.invited_dt = datetime.now(timezone.utc)
            
            # Send email invitation
            try:
                survey_url = url_for('take_survey', survey_token=survey.survey_token, 
                                   _external=True) + f"?token={existing_response.response_token}"
                
                # Use activity-specific email templates
                from utils import get_email_context

                # Build logo URL in request context (url_for needs request context)
                if survey.activity and survey.activity.logo_filename:
                    activity_logo_url = url_for('static', filename=f'uploads/logos/{survey.activity.logo_filename}')
                else:
                    org_logo = get_setting('LOGO_FILENAME', 'logo.png')
                    activity_logo_url = url_for('static', filename=f'uploads/{org_logo}')

                # Build base context
                base_context = {
                    'user_name': passport.user.name or 'Participant',
                    'activity': survey.activity,  # Add activity object for Jinja2 template rendering
                    'activity_name': survey.activity.name,
                    'survey_name': survey.name,
                    'survey_url': survey_url,
                    'question_count': question_count,
                    'organization_name': get_setting('ORG_NAME', 'Fondation LHGI'),
                    'organization_address': get_setting('ORG_ADDRESS', ''),
                    'support_email': get_setting('SUPPORT_EMAIL', 'support@minipass.me'),
                    'activity_logo_url': activity_logo_url  # Add logo URL to base context
                }

                # Get email context using activity-specific templates
                email_context = get_email_context(survey.activity, 'survey_invitation', base_context)

                # CRITICAL FIX: Render Jinja2 variables in customized template strings
                # The customized templates contain Jinja2 variables like {{ activity_name }} that need to be rendered
                from jinja2 import Template as JinjaTemplate

                # Build rendering context with all available variables
                render_context = {
                    'user_name': passport.user.name or 'Participant',
                    'activity_name': survey.activity.name,
                    'activity': survey.activity,  # For accessing activity properties
                    'survey_name': survey.name,
                    'survey_url': survey_url,
                    'question_count': question_count,
                    'organization_name': get_setting('ORG_NAME', 'Fondation LHGI'),
                    'organization_address': get_setting('ORG_ADDRESS', ''),
                    'support_email': get_setting('SUPPORT_EMAIL', 'support@minipass.me'),
                }

                # Render subject, title, intro_text, and conclusion_text if they contain Jinja2 variables
                subject_template = email_context.get('subject', f"{survey.name} - Your Feedback Requested")
                title_template = email_context.get('title', 'We\'d Love Your Feedback!')
                intro_template = email_context.get('intro_text', '<p>Thank you for participating in our activity! We hope you had a great experience and would love to hear your thoughts.</p>')
                conclusion_template = email_context.get('conclusion_text', '<p>Thank you for helping us create better experiences!</p>')

                subject = JinjaTemplate(subject_template).render(**render_context)
                rendered_title = JinjaTemplate(title_template).render(**render_context)
                rendered_intro = JinjaTemplate(intro_template).render(**render_context)
                rendered_conclusion = JinjaTemplate(conclusion_template).render(**render_context)

                template_name = 'survey_invitation'  # Match the template folder name

                # Note: inline_images and logo loading is handled automatically by send_email_async()

                context = {
                    'user_name': passport.user.name or 'Participant',
                    'activity_name': survey.activity.name,
                    'survey_name': survey.name,
                    'survey_url': survey_url,
                    'question_count': question_count,
                    'organization_name': get_setting('ORG_NAME', 'Fondation LHGI'),
                    'organization_address': get_setting('ORG_ADDRESS', ''),
                    'support_email': get_setting('SUPPORT_EMAIL', 'support@minipass.me'),
                    'unsubscribe_url': f"https://minipass.me/unsubscribe?email={passport.user.email}",
                    'privacy_url': "https://minipass.me/privacy",
                    # Survey email template variables - now RENDERED (Jinja2 variables already processed)
                    'title': rendered_title,
                    'intro_text': rendered_intro,
                    'conclusion_text': rendered_conclusion,
                    # CRITICAL: Flag to prevent send_email_async from re-applying get_email_context()
                    '_skip_email_context': True
                }
                
                print(f"🔵 About to call send_email_async()")
                print(f"🔵 Template: {template_name}")
                print(f"🔵 Subject: {subject}")
                print(f"🔵 To: {passport.user.email}")
                print(f"🔵 Context keys: {list(context.keys())}")

                send_email_async(
                    app=current_app._get_current_object(),
                    user=passport.user,
                    activity=survey.activity,  # Pass activity to use customized email templates
                    subject=subject,
                    to_email=passport.user.email,
                    template_name=template_name,
                    context=context
                )

                print(f"send_email_async() called successfully for {passport.user.email}")
                sent_count += 1
                
            except Exception as e:
                import traceback
                print(f"Failed to send survey invitation to {passport.user.email}")
                print(f"Error: {e}")
                print(f"Traceback:")
                traceback.print_exc()
                failed_count += 1
                failed_emails.append(passport.user.email)

        else:
            already_invited += 1
    
    db.session.commit()

    # Smart messaging based on results
    if failed_count > 0 and sent_count == 0:
        # All emails failed
        failed_sample = ', '.join(failed_emails[:3])
        if len(failed_emails) > 3:
            failed_sample += f" (and {len(failed_emails) - 3} more)"
        flash(f"Error: Failed to send all {failed_count} invitations. Failed emails: {failed_sample}", "error")
    elif failed_count > 0:
        # Some emails failed
        failed_sample = ', '.join(failed_emails[:3])
        if len(failed_emails) > 3:
            failed_sample += f" (and {len(failed_emails) - 3} more)"
        flash(f"Partial success: Sent to {sent_count} participants, but {failed_count} failed. Failed emails: {failed_sample}", "warning")
    elif already_invited > 0:
        flash(f"Survey invitations sent to {sent_count} participants. {already_invited} were already invited.", "success")
    else:
        flash(f"Survey invitations sent to {sent_count} participants", "success")

    return redirect(url_for("list_surveys"))


@app.route("/survey/<int:survey_id>/export")
def export_survey_results(survey_id):
    if "admin" not in session:
        return redirect(url_for("login"))
    
    try:
        # Get survey and its responses
        survey = Survey.query.get_or_404(survey_id)
        responses = SurveyResponse.query.filter_by(survey_id=survey_id, completed=True).all()
        
        if not responses:
            flash("No completed responses found for this survey", "info")
            return redirect(url_for("survey_results", survey_id=survey_id))
        
        # Get survey questions from template
        import json
        import csv
        template_data = json.loads(survey.template.questions)
        
        # Handle both old and new template formats
        if isinstance(template_data, list):
            template_questions = template_data  # Old format: direct array
        else:
            template_questions = template_data.get('questions', [])  # New format: wrapped in object
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'Response ID', 'User Name', 'User Email', 'Passport ID',
            'Started Date', 'Completed Date', 'IP Address'
        ]
        
        # Add question headers
        for question in template_questions:
            headers.append(f"Q{question['id']}: {question['question']}")
        
        writer.writerow(headers)
        
        # Write response data
        for response in responses:
            response_data = json.loads(response.responses) if response.responses else {}
            
            row = [
                response.id,
                response.user.name if response.user else 'N/A',
                response.user.email if response.user else 'N/A',
                response.passport_id or 'N/A',
                response.started_dt.strftime('%Y-%m-%d %H:%M:%S') if response.started_dt else 'N/A',
                response.completed_dt.strftime('%Y-%m-%d %H:%M:%S') if response.completed_dt else 'N/A',
                response.ip_address or 'N/A'
            ]
            
            # Add answer data for each question
            for question in template_questions:
                question_id = str(question['id'])
                answer = response_data.get(question_id, 'No response')
                
                # Format answer based on question type
                if question['type'] == 'rating':
                    if isinstance(answer, (int, float)):
                        row.append(f"{answer}/{question.get('max_rating', 5)}")
                    else:
                        row.append(answer)
                elif question['type'] == 'multiple_choice':
                    if isinstance(answer, list):
                        row.append('; '.join(answer))
                    else:
                        row.append(answer)
                else:
                    row.append(str(answer) if answer else 'No response')
            
            writer.writerow(row)
        
        # Create response
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename
        safe_survey_name = re.sub(r'[^\w\s-]', '', survey.name).strip()
        safe_survey_name = re.sub(r'[-\s]+', '-', safe_survey_name)
        filename = f"survey-{survey_id}-{safe_survey_name}-{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Return CSV file
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        print(f"Export error: {str(e)}")
        flash("Error exporting survey results", "error")
        return redirect(url_for("survey_results", survey_id=survey_id))


@app.route("/close-survey/<int:survey_id>", methods=["POST"])
def close_survey(survey_id):
    if "admin" not in session:
        return redirect(url_for("login"))
    
    survey = Survey.query.get_or_404(survey_id)
    survey.status = 'closed'
    
    try:
        db.session.commit()
        flash(f"Survey '{survey.name}' has been closed", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error closing survey", "error")
    
    return redirect(url_for("list_surveys"))


@app.route("/reopen-survey/<int:survey_id>", methods=["POST"])
def reopen_survey(survey_id):
    if "admin" not in session:
        return redirect(url_for("login"))
    
    survey = Survey.query.get_or_404(survey_id)
    survey.status = 'active'
    
    try:
        db.session.commit()
        flash(f"Survey '{survey.name}' has been reopened", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error reopening survey", "error")
    
    return redirect(url_for("list_surveys"))


@app.route("/delete-survey/<int:survey_id>", methods=["POST"])
def delete_survey(survey_id):
    if "admin" not in session:
        return redirect(url_for("login"))
    
    survey = Survey.query.get_or_404(survey_id)
    
    # Delete all responses first
    SurveyResponse.query.filter_by(survey_id=survey_id).delete()
    
    try:
        db.session.delete(survey)
        db.session.commit()
        flash(f"Survey '{survey.name}' deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting survey", "error")
    
    return redirect(url_for("list_surveys"))


# Duplicate endpoints removed - using the ones defined earlier in the file


# NOTE: Default survey templates are created on first admin login, not on startup
# This prevents deleted templates from resurrecting on every app restart
with app.app_context():
    # Initialize scheduler after app setup
    try:
        initialize_background_tasks()
    except Exception as e:
        print(f"Warning: Could not initialize background tasks: {str(e)}")

@app.route("/test-payment-bot-now")
def test_payment_bot_now():
    """SIMPLE payment bot test - just visit this URL"""
    if "admin" not in session:
        return "Must be logged in as admin", 401
    
    try:
        print("🔧 SIMPLE payment bot test started!")
        from utils import match_gmail_payments_to_passes
        
        result = match_gmail_payments_to_passes()
        
        if result and isinstance(result, dict):
            message = f"Payment bot completed! {result.get('matched', 0)} payments matched."
        else:
            message = "Payment bot completed! No new payments found."
            
        print(f"Payment bot result: {message}")
        return f"<h1>{message}</h1><p><strong>Check your dashboard logs for details.</strong></p><p><a href='/admin/unified-settings'>← Back to Settings</a></p>"
        
    except Exception as e:
        error_msg = f"Payment bot failed: {str(e)}"
        print(error_msg)
        return f"<h1>{error_msg}</h1><p><a href='/admin/unified-settings'>← Back to Settings</a></p>"


@app.route("/update-payment-notes")
def update_payment_notes():
    """Update existing NO_MATCH payment records with detailed, accurate notes"""
    if "admin" not in session:
        return "Must be logged in as admin", 401

    try:
        print("🔧 Starting retroactive payment notes update...")
        import unicodedata
        from rapidfuzz import fuzz

        def normalize_name(text):
            """Remove accents and normalize text for better matching"""
            normalized = unicodedata.normalize('NFD', text)
            without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
            return without_accents.lower().strip()

        # Get all NO_MATCH payments
        no_match_payments = EbankPayment.query.filter_by(result='NO_MATCH').all()
        updated_count = 0
        threshold = 85

        for payment in no_match_payments:
            name = payment.bank_info_name
            amt = payment.bank_info_amt
            email_received_date = payment.email_received_date
            payment_amount = float(amt)

            # Get all unpaid passports with this amount
            all_unpaid = Passport.query.filter_by(paid=False).all()
            unpaid_passports = [p for p in all_unpaid if float(p.sold_amt) == payment_amount]

            new_note = None

            # FIXED: Check unpaid passports FIRST, only check paid if no unpaid match
            if not unpaid_passports:
                # No unpaid passports at this amount
                available_amounts = list(set(float(p.sold_amt) for p in all_unpaid))
                available_amounts.sort()
                amounts_summary = ", ".join([f"${a:.2f}({sum(1 for p in all_unpaid if float(p.sold_amt) == a)})" for a in available_amounts[:5]])
                new_note = f"No unpaid passports for ${payment_amount:.2f}. Payment may have arrived before passport creation. Available unpaid amounts: {amounts_summary}"
            else:
                # There ARE unpaid passports - check if any match the payment name
                normalized_payment_name = normalize_name(name)

                # Try to find matching unpaid passport
                unpaid_match_found = False
                for p in unpaid_passports:
                    if not p.user:
                        continue
                    score = fuzz.ratio(normalized_payment_name, normalize_name(p.user.name))
                    if score >= threshold:  # Use threshold (85%) for matching
                        unpaid_match_found = True
                        # Found a matching unpaid passport - this should have been auto-matched
                        # This means the payment bot hasn't run yet or there was an error
                        new_note = f"UNPAID MATCH AVAILABLE: {p.user.name} (${payment_amount:.2f}, Passport #{p.id}, Score: {score}%) - Run payment bot to auto-match"
                        break

                # If no unpaid match, check if this might be a duplicate payment for already-paid passport
                if not unpaid_match_found:
                    all_paid = Passport.query.filter_by(paid=True).all()
                    paid_passports_same_amount = [p for p in all_paid if float(p.sold_amt) == payment_amount]

                    matching_paid_passport = None
                    for p in paid_passports_same_amount:
                        if not p.user:
                            continue
                        normalized_passport_name = normalize_name(p.user.name)
                        score = fuzz.ratio(normalized_payment_name, normalized_passport_name)
                        if score >= 95:  # Strict matching for paid passports
                            matching_paid_passport = p
                            break

                    if matching_paid_passport:
                        # Found matching PAID passport - likely duplicate payment
                        paid_by = matching_paid_passport.marked_paid_by or "unknown admin"
                        paid_date_str = matching_paid_passport.paid_date.strftime("%Y-%m-%d %H:%M") if matching_paid_passport.paid_date else "unknown date"

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

                        new_note = f"MATCH FOUND: {matching_paid_passport.user.name} (${payment_amount:.2f}, Passport #{matching_paid_passport.id}) - Already marked PAID by {paid_by} on {paid_date_str}{time_diff_info}"
                    else:
                        # Truly no match - create detailed note
                        all_candidates = []
                        for p in unpaid_passports:
                            if not p.user:
                                continue
                            score = fuzz.ratio(normalized_payment_name, normalize_name(p.user.name))
                            if score >= 50:
                                all_candidates.append((p.user.name, score))

                        all_candidates.sort(key=lambda x: x[1], reverse=True)
                        top_candidates = all_candidates[:3]

                        note_parts = [f"No match found for '{name}' (${amt})."]
                        note_parts.append(f"Found {len(unpaid_passports)} unpaid passport(s) for ${amt}, but")

                        if top_candidates:
                            candidate_strs = [f"{cname} ({score:.0f}%)" for cname, score in top_candidates]
                            note_parts.append(f"all names below {threshold}% threshold. Closest: {', '.join(candidate_strs)}.")
                        else:
                            note_parts.append(f"no names above 50% similarity.")
                            if unpaid_passports:
                                example_names = [p.user.name for p in unpaid_passports[:3] if p.user]
                                if example_names:
                                    note_parts.append(f"Available names: {', '.join(example_names[:3])}")

                        new_note = " ".join(note_parts)

            # Update the record if note changed
            if new_note and new_note != payment.note:
                payment.note = new_note
                updated_count += 1

        db.session.commit()

        message = f"Updated {updated_count} out of {len(no_match_payments)} NO_MATCH payment records with detailed notes!"
        print(message)
        return f"<h1>{message}</h1><p><strong>Refresh your payment matches page to see the new detailed reasons.</strong></p><p><a href='/payment-bot-matches'>→ View Payment Matches</a></p>"

    except Exception as e:
        error_msg = f"Update failed: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return f"<h1>{error_msg}</h1><p><a href='/payment-bot-matches'>← Back</a></p>"


# ================================
# 📧 EMAIL TEMPLATE CUSTOMIZATION ROUTES
# ================================

@app.route("/activity/<int:activity_id>/email-templates")
def email_template_customization(activity_id):
    """Display email template customization interface"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    from models import Activity
    
    activity = Activity.query.get_or_404(activity_id)
    
    # Email template types we support
    template_types = {
        'newPass': 'New Pass Created',
        'paymentReceived': 'Payment Received',
        'latePayment': 'Late Payment Reminder',
        'signup': 'Signup Confirmation',
        'signup_payment_first': 'Signup Confirmation (Pay First)',
        'redeemPass': 'Pass Redeemed',
        'survey_invitation': 'Survey Invitation'
    }
    
    # Get existing customizations or initialize empty
    current_templates = activity.email_templates or {}
    
    # Import and merge with default values
    from utils_email_defaults import get_default_email_templates
    defaults = get_default_email_templates()
    
    # For each template type, merge defaults with current values
    templates_with_defaults = {}
    for template_key in template_types:
        template_defaults = defaults.get(template_key, {})
        template_current = current_templates.get(template_key, {})
        
        # Merge: use current values if they exist, otherwise use defaults
        templates_with_defaults[template_key] = {
            'subject': template_current.get('subject') or template_defaults.get('subject', ''),
            'title': template_current.get('title') or template_defaults.get('title', ''), 
            'intro_text': template_current.get('intro_text') or template_defaults.get('intro_text', ''),
            'conclusion_text': template_current.get('conclusion_text') or template_defaults.get('conclusion_text', ''),
            # Keep other fields as-is
            **{k: v for k, v in template_current.items() if k not in ['subject', 'title', 'intro_text', 'conclusion_text']}
        }
    
    # Get organization logo filename for fallback
    org_logo_filename = get_setting('LOGO_FILENAME', 'logo.png')

    # Check if the org logo file actually exists on disk
    org_logo_path = os.path.join('static', 'uploads', org_logo_filename) if org_logo_filename else ''
    org_logo_exists = bool(org_logo_filename) and os.path.exists(org_logo_path)

    # Generate placeholder data URI for template if no real logo
    placeholder_logo_data_uri = None
    if not org_logo_exists:
        try:
            org_name = get_setting('ORG_NAME', 'Minipass')
            from utils import generate_placeholder_logo_image
            buf = generate_placeholder_logo_image(org_name, size=120)
            placeholder_logo_data_uri = 'data:image/png;base64,' + base64.b64encode(buf.read()).decode('utf-8')
        except Exception:
            pass

    # Check if user has explicitly uploaded a custom owner logo via the template editor
    has_custom_owner_logo = False
    if activity.email_templates:
        for tpl_data in activity.email_templates.values():
            if isinstance(tpl_data, dict) and tpl_data.get('activity_logo'):
                has_custom_owner_logo = True
                break

    return render_template("email_template_customization.html",
                         activity=activity,
                         template_types=template_types,
                         current_templates=templates_with_defaults,
                         org_logo_filename=org_logo_filename,
                         org_logo_exists=org_logo_exists,
                         placeholder_logo_data_uri=placeholder_logo_data_uri,
                         has_custom_owner_logo=has_custom_owner_logo)


# Removed obsolete thumbnail generation route - now using Tabler placeholders instead


@app.route("/activity/<int:activity_id>/email-templates/save", methods=["POST"])
def save_email_templates(activity_id):
    """Save email template customizations - supports both individual and bulk saves"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    from models import Activity
    from werkzeug.utils import secure_filename
    from utils import ContentSanitizer
    import json
    import os
    import bleach
    
    activity = Activity.query.get_or_404(activity_id)
    
    template_types = ['newPass', 'paymentReceived', 'latePayment', 'signup', 'signup_payment_first', 'redeemPass', 'survey_invitation']
    
    # Initialize email_templates as empty dict if None
    if activity.email_templates is None:
        activity.email_templates = {}
    
    # Check if this is an individual template save (AJAX request)
    single_template = request.form.get('single_template')
    is_individual_save = single_template is not None
    
    # Template name mapping for responses
    template_names = {
        'newPass': 'New Pass Created',
        'paymentReceived': 'Payment Received',
        'latePayment': 'Late Payment Reminder',
        'signup': 'Signup Confirmation',
        'signup_payment_first': 'Signup Confirmation (Pay First)',
        'redeemPass': 'Pass Redeemed',
        'survey_invitation': 'Survey Invitation'
    }
    
    # If individual save, validate the template type
    if is_individual_save and single_template not in template_types:
        return jsonify({
            'success': False,
            'message': 'Invalid template type',
            'template_type': single_template
        }), 400
    
    # Determine which templates to process
    templates_to_process = [single_template] if is_individual_save else template_types
    
    # Track activity-wide images that need to be processed only once  
    owner_logo_processed = False
    
    try:
        # Handle template-specific hero image uploads
        hero_files_uploaded = []
        
        # Process hero image uploads for each template type
        for template_type in templates_to_process:
            hero_file = request.files.get(f'{template_type}_hero_image')
            if hero_file and hero_file.filename:
                try:
                    # Use template-specific filename
                    hero_filename = f"{activity_id}_{template_type}_hero.png"
                    upload_path = os.path.join('static', 'uploads', hero_filename)
                    
                    # Ensure uploads directory exists
                    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                    
                    # Read the uploaded image data
                    hero_file_data = hero_file.read()
                    
                    # Resize the image to match template dimensions
                    from utils import resize_hero_image
                    resized_image_data, resize_message = resize_hero_image(hero_file_data, template_type)
                    
                    if resized_image_data:
                        # Save the resized image
                        with open(upload_path, 'wb') as f:
                            f.write(resized_image_data)
                        hero_files_uploaded.append((template_type, hero_filename))
                        print(f"Hero image resized and saved for {template_type}: {hero_filename} - {resize_message}")
                    else:
                        # Fall back to original if resize fails
                        hero_file.seek(0)  # Reset file pointer
                        hero_file.save(upload_path)
                        hero_files_uploaded.append((template_type, hero_filename))
                        print(f"Hero image saved without resizing for {template_type}: {hero_filename} - {resize_message}")
                    
                except Exception as e:
                    flash(f"Error uploading hero image for {template_type}: {str(e)}", "error")
        
        # Handle activity-wide owner logo upload (shared across all templates)
        owner_logo_file = None
        
        # Look for owner logo upload from relevant template type(s)
        for template_type in templates_to_process:
            if not owner_logo_processed:
                owner_logo_file = request.files.get(f'{template_type}_owner_logo')
                if owner_logo_file and owner_logo_file.filename:
                    owner_logo_processed = True
                    break
        
        # Process owner logo if uploaded
        owner_logo_filename = None
        if owner_logo_file and owner_logo_file.filename:
            try:
                # Use activity-specific filename that overwrites existing
                owner_logo_filename = f"{activity_id}_owner_logo.png"
                upload_path = os.path.join('static', 'uploads', owner_logo_filename)
                
                # Ensure uploads directory exists
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                
                # Save file (overwrites if exists)
                owner_logo_file.save(upload_path)
                
            except Exception as e:
                flash(f"Error uploading owner logo: {str(e)}", "error")
                owner_logo_filename = None
        
        # Process selected template type(s)
        for template_type in templates_to_process:
            # Get existing template data or create new
            if template_type in activity.email_templates:
                template_data = activity.email_templates[template_type].copy()
            else:
                template_data = {}
            
            # Get form fields and sanitize them
            subject = ContentSanitizer.sanitize_html(request.form.get(f'{template_type}_subject', '').strip())
            title = ContentSanitizer.sanitize_html(request.form.get(f'{template_type}_title', '').strip())
            intro_text = ContentSanitizer.sanitize_html(request.form.get(f'{template_type}_intro_text', '').strip())
            conclusion_text = ContentSanitizer.sanitize_html(request.form.get(f'{template_type}_conclusion_text', '').strip())
            
            # Remove HTML tags from subject and title (plain text fields)
            subject = bleach.clean(subject, tags=[], strip=True) if subject else ''
            title = bleach.clean(title, tags=[], strip=True) if title else ''
            
            # Update values (preserve existing if new is empty)
            if subject:
                template_data['subject'] = subject
            if title:
                template_data['title'] = title
            if intro_text:
                template_data['intro_text'] = intro_text
            if conclusion_text:
                template_data['conclusion_text'] = conclusion_text

            # Handle show_qr_code toggle (only for templates with QR codes)
            if template_type in ['newPass', 'paymentReceived', 'redeemPass', 'latePayment']:
                # Checkbox: 'on' if checked, empty/missing if unchecked
                form_value = request.form.get(f'{template_type}_show_qr_code')
                show_qr_code = form_value == 'on'
                template_data['show_qr_code'] = show_qr_code
                print(f"🔍 DEBUG SAVE: {template_type}_show_qr_code form value = '{form_value}'")
                print(f"🔍 DEBUG SAVE: show_qr_code = {show_qr_code}")
                print(f"🔍 DEBUG SAVE: template_data = {template_data}")

            # Update image references if files were uploaded
            # Check for template-specific hero image
            for uploaded_template, uploaded_hero in hero_files_uploaded:
                if uploaded_template == template_type:
                    template_data['hero_image'] = uploaded_hero
                    break
            
            # Update activity-wide owner logo if uploaded
            if owner_logo_filename:
                template_data['activity_logo'] = owner_logo_filename
            
            # Always save template_data to preserve all fields
            activity.email_templates[template_type] = template_data
        
        # Mark the attribute as modified for SQLAlchemy JSON field
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(activity, 'email_templates')
        
        db.session.commit()

        # AUTO-COMPILE survey_invitation template after save
        if is_individual_save and single_template == 'survey_invitation':
            try:
                import subprocess
                compile_script = os.path.join('templates', 'email_templates', 'compileEmailTemplate.py')
                result = subprocess.run(
                    ['python', compile_script, 'survey_invitation'],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.path.dirname(compile_script)
                )
                if result.returncode != 0:
                    print(f"Warning: Survey template compilation failed: {result.stderr}")
                else:
                    print(f"Survey invitation template compiled successfully after save")
            except Exception as e:
                print(f"Warning: Could not auto-compile survey template: {e}")

        # Return appropriate response based on request type
        if is_individual_save:
            # Flash message for consistent UX
            flash('Email template saved successfully!', 'success')
            return jsonify({
                'success': True,
                'message': 'Template saved successfully',
                'template_type': single_template,
                'template_name': template_names.get(single_template, single_template)
            })
        else:
            flash("Email templates saved successfully!", "success")
        
    except Exception as e:
        db.session.rollback()
        error_message = f"Error saving email templates: {str(e)}"
        
        if is_individual_save:
            return jsonify({
                'success': False,
                'message': error_message,
                'template_type': single_template if single_template else 'unknown'
            }), 500
        else:
            flash(f"{error_message}", "error")
    
    # Only redirect for bulk saves (form submissions)
    if not is_individual_save:
        return redirect(url_for('email_template_customization', activity_id=activity_id))


@app.route("/activity/<int:activity_id>/email-templates/reset", methods=["POST"])
def reset_email_template(activity_id):
    """Reset a specific email template to default values"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    from models import Activity
    import json
    
    try:
        activity = Activity.query.get_or_404(activity_id)
        
        # Get the template type from request
        data = request.get_json()
        if not data or 'template_type' not in data:
            return jsonify({
                'success': False,
                'message': 'Template type is required'
            }), 400
        
        template_type = data['template_type']
        
        # Valid template types
        valid_templates = ['newPass', 'paymentReceived', 'latePayment', 'signup', 'signup_payment_first', 'redeemPass', 'survey_invitation']
        if template_type not in valid_templates:
            return jsonify({
                'success': False,
                'message': 'Invalid template type'
            }), 400
        
        # Initialize email_templates if it doesn't exist
        if activity.email_templates is None:
            activity.email_templates = {}
        
        # Clear all custom values for this template (reset to defaults)
        if template_type in activity.email_templates:
            template_data = activity.email_templates[template_type]
            
            # Clear the customizable fields while preserving any system fields
            # Note: show_qr_code is included so it resets to default (True = show QR)
            fields_to_reset = ['subject', 'title', 'intro_text', 'conclusion_text', 'hero_image', 'activity_logo', 'show_qr_code']
            for field in fields_to_reset:
                if field in template_data:
                    del template_data[field]
            
            # If template data is now empty, remove the entire template entry
            if not template_data:
                del activity.email_templates[template_type]
            else:
                activity.email_templates[template_type] = template_data
        
        # CRITICAL FIX: Delete the physical hero image file when resetting
        import os
        import shutil
        hero_file_path = f"static/uploads/{activity_id}_{template_type}_hero.png"
        if os.path.exists(hero_file_path):
            try:
                os.remove(hero_file_path)
                print(f"Deleted custom hero image file: {hero_file_path}")
            except Exception as e:
                print(f"Could not delete hero image file {hero_file_path}: {e}")
        
        # Also delete owner logo file when resetting if this is the first template (contains global settings)
        owner_logo_path = f"static/uploads/{activity_id}_owner_logo.png"  
        if template_type == 'newPass' and os.path.exists(owner_logo_path):
            try:
                os.remove(owner_logo_path)
                print(f"Deleted custom owner logo file: {owner_logo_path}")
            except Exception as e:
                print(f"Could not delete owner logo file {owner_logo_path}: {e}")
        
        # NEW: Restore original compiled template files 
        original_dir = f"templates/email_templates/{template_type}_original"
        compiled_dir = f"templates/email_templates/{template_type}_compiled"
        
        if os.path.exists(original_dir):
            try:
                # Copy original files back to compiled directory
                if os.path.exists(compiled_dir):
                    shutil.rmtree(compiled_dir)
                shutil.copytree(original_dir, compiled_dir)
                print(f"Restored original template files: {original_dir} → {compiled_dir}")
            except Exception as e:
                print(f"Could not restore original template files: {e}")
        else:
            print(f"Original template directory not found: {original_dir}")
        
        # Mark the attribute as modified for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(activity, 'email_templates')
        
        db.session.commit()

        # Flash message for consistent UX
        flash('Template reset to defaults successfully!', 'success')

        return jsonify({
            'success': True,
            'message': f'Template "{template_type}" has been reset to default values'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error resetting template: {str(e)}'
        }), 500


@app.route("/admin/clear-template-cache", methods=["POST"])
def clear_template_cache():
    """Clear the hero image cache after recompiling templates"""
    if "admin" not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    from utils import clear_hero_image_cache
    clear_hero_image_cache()

    return jsonify({
        'success': True,
        'message': 'Template hero image cache cleared successfully'
    })


@app.route("/activity/<int:activity_id>/email-preview")
def email_preview(activity_id):
    """Preview email template using compiled template with email blocks and real images"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    from models import Activity
    from utils import get_email_context, safe_template, generate_qr_code_image, get_setting
    from flask import render_template
    from datetime import datetime
    import os
    import json
    import base64

    activity = Activity.query.get_or_404(activity_id)
    template_type = request.args.get('type', 'newPass')
    
    # Create sample context data for preview
    base_context = {
        'user_name': 'John Doe',
        'user_email': 'john.doe@example.com',
        'activity_name': activity.name,
        'pass_code': 'SAMPLE123',
        'amount': '$50.00'
    }
    
    # Add special context for survey_invitation
    if template_type == 'survey_invitation':
        base_context['survey_name'] = 'Customer Satisfaction Survey'
        base_context['survey_url'] = 'https://example.com/survey/sample'
        base_context['question_count'] = 8
        base_context['organization_name'] = get_setting('ORG_NAME', 'Fondation LHGI')
        base_context['organization_address'] = get_setting('ORG_ADDRESS', '')
        base_context['support_email'] = get_setting('SUPPORT_EMAIL', 'support@minipass.me')
        # These will be overridden by get_email_context if customized
        base_context['title'] = 'We\'d Love Your Feedback!'
        base_context['intro'] = 'Thank you for participating in our activity! We hope you had a great experience and would love to hear your thoughts.'
        base_context['conclusion'] = 'Thank you for helping us create better experiences!'

    # Add special context for signup_payment_first template
    elif template_type == 'signup_payment_first':
        base_context['needs_signup_code'] = True  # Show the signup code section in preview
        base_context['signup_code'] = 'MP-INS-0000001'
        base_context['requested_amount'] = '$50.00'
        display_email = get_setting("DISPLAY_PAYMENT_EMAIL")
        base_context['payment_email'] = display_email if display_email else get_setting('MAIL_USERNAME', 'paiement@minipass.me')
        base_context['organization_name'] = get_setting('ORG_NAME', 'Fondation LHGI')
        # Activity object for location display
        base_context['activity'] = activity

    # Add email blocks for templates that need them
    elif template_type in ['newPass', 'paymentReceived', 'redeemPass', 'latePayment']:
        # Create sample pass data using proper class structure
        class PassData:
            def __init__(self):
                self.activity = type('obj', (object,), {
                    'name': activity.name,
                    'id': activity.id
                })()
                self.user = type('obj', (object,), {
                    'name': 'John Doe',
                    'email': 'john.doe@example.com',
                    'phone_number': '555-0123'
                })()
                self.pass_type = type('obj', (object,), {
                    'name': 'Sample Pass',
                    'price': 50.00
                })()
                self.created_dt = datetime.now()
                self.sold_amt = 50.00
                self.paid = True
                self.pass_code = 'SAMPLE123'
                self.remaining_activities = 5
                self.uses_remaining = 5

        pass_data = PassData()

        # Render email blocks
        base_context['owner_html'] = render_template(
            "email_blocks/owner_card_inline.html",
            pass_data=pass_data
        )

        # Add history for ALL templates that need it (not just redeemPass)
        history = [
            {'date': '2025-01-09', 'action': 'Pass Created'},
            {'date': '2025-01-10', 'action': 'Payment Received'}
        ]
        if template_type == 'redeemPass':
            history.append({'date': '2025-01-11', 'action': 'Pass Redeemed'})

        base_context['history_html'] = render_template(
            "email_blocks/history_table_inline.html",
            history=history
        )
    
    # Get merged context with activity customizations (preserves email blocks)
    context = get_email_context(activity, template_type, base_context)

    # Get show_qr_code setting from activity's email templates (default True)
    show_qr_code = True
    if activity.email_templates and template_type in activity.email_templates:
        show_qr_code = activity.email_templates[template_type].get('show_qr_code', True)
    context['show_qr_code'] = show_qr_code

    # Get the compiled template path
    template_path = safe_template(template_type)

    try:
        # Render the compiled template with the merged context
        rendered_html = render_template(template_path, **context)
        
        # Load inline images and convert to data URIs for browser display
        compiled_folder = template_path.replace('/index.html', '')
        json_path = os.path.join('templates', compiled_folder, 'inline_images.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                inline_images_data = json.load(f)
                
                # Use the proper hero image utility function to determine current hero
                from utils import get_activity_hero_image
                hero_data, is_custom_hero, is_template_default = get_activity_hero_image(activity, template_type)
                has_custom_hero = hero_data is not None and is_custom_hero
                
                print(f"EMAIL TEMPLATE: activity={activity.id}, template_type={template_type}")
                print(f"EMAIL TEMPLATE: Custom hero found: {has_custom_hero}, is_custom: {is_custom_hero}")

                # Replace cid: references with data: URIs
                for img_id, base64_data in inline_images_data.items():
                    # Skip hero-related images ONLY if we have a custom hero image
                    expected_hero_cid = HERO_CID_MAP.get(template_type, f'hero_{template_type}')
                    if (img_id == expected_hero_cid and has_custom_hero):
                        print(f"EMAIL TEMPLATE: Skipping template hero '{img_id}' because custom hero exists")
                        continue
                        
                    # Determine image type (most are PNG)
                    mime_type = 'image/png'
                    if img_id in ['facebook', 'instagram']:
                        mime_type = 'image/png'
                    
                    # Replace cid:image_id with data URI
                    cid_ref = f'cid:{img_id}'
                    data_uri = f'data:{mime_type};base64,{base64_data}'
                    rendered_html = rendered_html.replace(cid_ref, data_uri)
                    print(f"EMAIL TEMPLATE: Replaced {cid_ref} with template image")
                
                # Now handle custom hero image if it exists
                if has_custom_hero:
                    hero_base64 = base64.b64encode(hero_data).decode('utf-8')
                    expected_hero_cid = HERO_CID_MAP.get(template_type, f'hero_{template_type}')
                    cid_ref = f'cid:{expected_hero_cid}'
                    data_uri = f'data:image/png;base64,{hero_base64}'
                    rendered_html = rendered_html.replace(cid_ref, data_uri)
                    print(f"EMAIL TEMPLATE: Replaced {cid_ref} with CUSTOM HERO image")

        # Add logo image as data URI (same resolution as email send in utils.py)
        logo_path = None
        # Check for activity-specific owner logo first (custom upload via template editor)
        activity_logo_path = os.path.join('static', 'uploads', f'{activity.id}_owner_logo.png')
        if os.path.exists(activity_logo_path):
            logo_path = activity_logo_path
        if not logo_path:
            # Use organization logo from settings as fallback
            from utils import get_setting
            org_logo = get_setting('LOGO_FILENAME', 'logo.png')
            logo_path = os.path.join('static', 'uploads', org_logo)

        if logo_path and os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('utf-8')
                rendered_html = rendered_html.replace('cid:logo', f'data:image/png;base64,{logo_base64}')
                rendered_html = rendered_html.replace('cid:logo_image', f'data:image/png;base64,{logo_base64}')
        else:
            # Generate placeholder logo when no real logo exists
            from utils import generate_placeholder_logo_image
            org_name = get_setting('ORG_NAME', 'Minipass')
            try:
                placeholder_buf = generate_placeholder_logo_image(org_name)
                logo_base64 = base64.b64encode(placeholder_buf.read()).decode('utf-8')
                rendered_html = rendered_html.replace('cid:logo', f'data:image/png;base64,{logo_base64}')
                rendered_html = rendered_html.replace('cid:logo_image', f'data:image/png;base64,{logo_base64}')
            except Exception:
                pass


        # Generate sample QR code for preview (only if enabled)
        # Get show_qr_code setting from activity's email templates (default True)
        preview_show_qr = True
        if activity.email_templates and template_type in activity.email_templates:
            preview_show_qr = activity.email_templates[template_type].get('show_qr_code', True)
        if preview_show_qr:
            qr_code_data = generate_qr_code_image('SAMPLE123')
            if qr_code_data:
                qr_base64 = base64.b64encode(qr_code_data.read()).decode('utf-8')
                rendered_html = rendered_html.replace('cid:qr_code', f'data:image/png;base64,{qr_base64}')

        # Add a preview banner to distinguish from actual emails
        preview_banner = """
        <div style="background: #ffeaa7; color: #2d3436; padding: 10px; text-align: center; font-weight: bold; border-bottom: 2px solid #fdcb6e;">
            📧 EMAIL PREVIEW - This shows how your customized template will look
        </div>
        """
        
        # Insert the banner at the beginning of the body
        if '<body>' in rendered_html:
            rendered_html = rendered_html.replace('<body>', f'<body>{preview_banner}')
        else:
            # Fallback if no body tag found
            rendered_html = preview_banner + rendered_html
        
        return rendered_html
        
    except Exception as e:
        # Fallback to error message if template rendering fails
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Preview Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ background: #ff7675; color: white; padding: 20px; border-radius: 8px; }}
                .template-info {{ background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>❌ Preview Error</h2>
                <p>Could not render template: {str(e)}</p>
            </div>
            <div class="template-info">
                <h3>Template Info:</h3>
                <p><strong>Template Type:</strong> {template_type}</p>
                <p><strong>Template Path:</strong> {template_path}</p>
                <p><strong>Activity:</strong> {activity.name}</p>
                <p><strong>Context Keys:</strong> {', '.join(context.keys())}</p>
            </div>
        </body>
        </html>
        """
        return error_html


# Removed obsolete email-thumbnail-preview route - now using Tabler placeholders instead


@app.route('/activity/<int:activity_id>/email-preview-live', methods=['POST'])
def email_preview_live(activity_id):
    """Generate live email preview without saving to database"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    from models import Activity
    from utils import get_email_context, safe_template, generate_qr_code_image, ContentSanitizer, get_setting
    from flask import render_template
    from datetime import datetime
    import os
    import json
    import base64
    import bleach

    activity = Activity.query.get_or_404(activity_id)

    # Get template type from request
    template_type = request.form.get('template_type') or request.args.get('type', 'newPass')
    device_mode = request.form.get('device', 'desktop')  # desktop or mobile

    # Create sample context data for preview
    base_context = {
        'user_name': 'John Doe',
        'user_email': 'john.doe@example.com',
        'activity_name': activity.name,
        'activity': activity,  # Full activity object for templates that need it (e.g., activity.location_address_formatted)
        'pass_code': 'SAMPLE123',
        'amount': '$50.00',
        'question_count': 8,  # For survey_invitation template
        'survey_url': 'https://example.com/survey/sample'  # For survey_invitation template
    }
    
    # Add email blocks for templates that need them
    if template_type in ['newPass', 'paymentReceived', 'redeemPass', 'latePayment']:
        # Create sample pass data using proper class structure
        class PassData:
            def __init__(self):
                self.activity = type('obj', (object,), {
                    'name': activity.name,
                    'id': activity.id,
                    'location_address_formatted': activity.location_address_formatted  # For templates that show location
                })()
                self.user = type('obj', (object,), {
                    'name': 'John Doe',
                    'email': 'john.doe@example.com',
                    'phone_number': '555-0123'
                })()
                self.pass_type = type('obj', (object,), {
                    'name': 'Sample Pass',
                    'price': 50.00
                })()
                self.created_dt = datetime.now()
                self.sold_amt = 50.00
                self.paid = True
                self.pass_code = 'SAMPLE123'
                self.remaining_activities = 5
                self.uses_remaining = 5

        pass_data = PassData()

        # CRITICAL: Add pass_data to base_context so templates can access it
        base_context['pass_data'] = pass_data
        print(f"PREVIEW: Added pass_data to context for {template_type}")

        # Render email blocks
        base_context['owner_html'] = render_template(
            "email_blocks/owner_card_inline.html",
            pass_data=pass_data
        )

        # Add history for ALL templates that need it
        history = [
            {'date': '2025-01-09', 'action': 'Pass Created'},
            {'date': '2025-01-10', 'action': 'Payment Received'}
        ]
        if template_type == 'redeemPass':
            history.append({'date': '2025-01-11', 'action': 'Pass Redeemed'})

        base_context['history_html'] = render_template(
            "email_blocks/history_table_inline.html",
            history=history
        )

    # Add special context for signup_payment_first template
    elif template_type == 'signup_payment_first':
        base_context['needs_signup_code'] = True  # Show the signup code section in preview
        base_context['signup_code'] = 'MP-INS-0000001'
        base_context['requested_amount'] = '$50.00'
        display_email = get_setting("DISPLAY_PAYMENT_EMAIL")
        base_context['payment_email'] = display_email if display_email else get_setting('MAIL_USERNAME', 'paiement@minipass.me')
        base_context['organization_name'] = get_setting('ORG_NAME', 'Fondation LHGI')

    # Create temporary customizations from form data without saving to database
    live_customizations = {}

    # Handle show_qr_code toggle from form data (for templates that have QR codes)
    if template_type in ['newPass', 'paymentReceived', 'redeemPass', 'latePayment']:
        show_qr_form_key = f'{template_type}_show_qr_code'
        # Checkbox: 'on' if checked, empty/missing if unchecked
        show_qr_code = request.form.get(show_qr_form_key) == 'on'
        live_customizations['show_qr_code'] = show_qr_code

    # Extract and sanitize customizations from form data for current template type
    form_fields = ['subject', 'title', 'intro_text', 'conclusion_text', 'cta_text', 'cta_url', 'custom_message']
    for field in form_fields:
        form_key = f'{template_type}_{field}'
        value = request.form.get(form_key, '').strip()
        if value:  # Only add non-empty values
            # Apply appropriate sanitization based on field type
            if field == 'cta_url':
                value = ContentSanitizer.validate_url(value)
            elif field in ['subject', 'title', 'cta_text']:
                # Plain text fields - strip all HTML
                value = bleach.clean(value, tags=[], strip=True)
            else:
                # Rich text fields - sanitize HTML
                value = ContentSanitizer.sanitize_html(value)
            
            if value:  # Only add if still has content after sanitization
                live_customizations[field] = value
    
    # Create a temporary activity object with live customizations
    # We'll modify the context generation to use these live customizations
    temp_email_templates = activity.email_templates.copy() if activity.email_templates else {}

    # Merge live customizations with existing template (don't replace entirely)
    existing_template = temp_email_templates.get(template_type, {})
    merged_template = existing_template.copy() if existing_template else {}
    merged_template.update(live_customizations)  # Only override fields that were changed
    temp_email_templates[template_type] = merged_template

    # Store original templates and temporarily replace them
    original_templates = activity.email_templates
    activity.email_templates = temp_email_templates
    
    try:
        # Get merged context with live customizations
        context = get_email_context(activity, template_type, base_context)

        # Get show_qr_code setting from merged template (default True)
        show_qr_code = True
        if template_type in ['newPass', 'paymentReceived', 'redeemPass', 'latePayment']:
            show_qr_code = merged_template.get('show_qr_code', True)
        context['show_qr_code'] = show_qr_code

        # DEBUG: Log preview values
        print(f"🔍 DEBUG PREVIEW: template_type = {template_type}")
        print(f"🔍 DEBUG PREVIEW: live_customizations = {live_customizations}")
        print(f"🔍 DEBUG PREVIEW: merged_template = {merged_template}")
        print(f"🔍 DEBUG PREVIEW: show_qr_code = {show_qr_code}")
        print(f"🔍 DEBUG PREVIEW: context['show_qr_code'] = {context.get('show_qr_code')}")

        # Get the compiled template path
        template_path = safe_template(template_type)
        
        # Render the compiled template with the merged context
        rendered_html = render_template(template_path, **context)
        
        # Handle uploaded hero image from form data BEFORE processing default images
        uploaded_hero_data = None
        hero_file_key = f'{template_type}_hero_image'
        if hero_file_key in request.files:
            hero_file = request.files[hero_file_key]
            if hero_file and hero_file.filename:
                try:
                    # Read uploaded file data directly without saving to disk
                    hero_file.seek(0)  # Reset file pointer
                    uploaded_hero_data = hero_file.read()
                except Exception as e:
                    print(f"Error reading uploaded hero file: {e}")
        
        # Load inline images and convert to data URIs for browser display
        compiled_folder = template_path.replace('/index.html', '')
        json_path = os.path.join('templates', compiled_folder, 'inline_images.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                inline_images_data = json.load(f)
                
                # Use the proper hero image utility function to determine current hero
                from utils import get_activity_hero_image
                hero_data, is_custom_hero, is_template_default = get_activity_hero_image(activity, template_type)
                has_custom_hero = hero_data is not None and is_custom_hero
                has_uploaded_hero = uploaded_hero_data is not None
                
                print(f"EMAIL LIVE PREVIEW: activity={activity.id}, template_type={template_type}")
                print(f"EMAIL LIVE PREVIEW: Custom hero found: {has_custom_hero}, uploaded hero: {has_uploaded_hero}")

                # Replace cid: references with data: URIs
                for img_id, base64_data in inline_images_data.items():
                    # Skip hero-related images if we have a custom hero OR uploaded hero
                    expected_hero_cid = HERO_CID_MAP.get(template_type, f'hero_{template_type}')
                    if (img_id == expected_hero_cid and (has_custom_hero or has_uploaded_hero)):
                        print(f"EMAIL LIVE PREVIEW: Skipping template hero '{img_id}' because custom/uploaded hero exists")
                        continue
                        
                    # Determine image type (most are PNG)
                    mime_type = 'image/png'
                    if img_id in ['facebook', 'instagram']:
                        mime_type = 'image/png'
                    
                    # Replace cid:image_id with data URI
                    cid_ref = f'cid:{img_id}'
                    data_uri = f'data:{mime_type};base64,{base64_data}'
                    rendered_html = rendered_html.replace(cid_ref, data_uri)
                    print(f"EMAIL LIVE PREVIEW: Replaced {cid_ref} with template image")
                
                # Handle hero image replacement - prioritize uploaded hero over custom hero
                if has_uploaded_hero:
                    hero_base64 = base64.b64encode(uploaded_hero_data).decode('utf-8')
                    expected_hero_cid = HERO_CID_MAP.get(template_type, f'hero_{template_type}')
                    cid_ref = f'cid:{expected_hero_cid}'
                    data_uri = f'data:image/png;base64,{hero_base64}'
                    rendered_html = rendered_html.replace(cid_ref, data_uri)
                    print(f"EMAIL LIVE PREVIEW: Replaced {cid_ref} with UPLOADED HERO image")
                elif has_custom_hero:
                    hero_base64 = base64.b64encode(hero_data).decode('utf-8')
                    expected_hero_cid = HERO_CID_MAP.get(template_type, f'hero_{template_type}')
                    cid_ref = f'cid:{expected_hero_cid}'
                    data_uri = f'data:image/png;base64,{hero_base64}'
                    rendered_html = rendered_html.replace(cid_ref, data_uri)
                    print(f"EMAIL LIVE PREVIEW: Replaced {cid_ref} with SAVED CUSTOM HERO image")

        # Add logo image as data URI (same resolution as email send in utils.py)
        logo_path = None
        # Check for activity-specific owner logo first (custom upload via template editor)
        activity_logo_path = os.path.join('static', 'uploads', f'{activity.id}_owner_logo.png')
        if os.path.exists(activity_logo_path):
            logo_path = activity_logo_path
        if not logo_path:
            # Use organization logo from settings as fallback
            from utils import get_setting
            org_logo = get_setting('LOGO_FILENAME', 'logo.png')
            logo_path = os.path.join('static', 'uploads', org_logo)

        if logo_path and os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('utf-8')
                rendered_html = rendered_html.replace('cid:logo', f'data:image/png;base64,{logo_base64}')
                rendered_html = rendered_html.replace('cid:logo_image', f'data:image/png;base64,{logo_base64}')
        else:
            # Generate placeholder logo when no real logo exists
            from utils import generate_placeholder_logo_image
            org_name = get_setting('ORG_NAME', 'Minipass')
            try:
                placeholder_buf = generate_placeholder_logo_image(org_name)
                logo_base64 = base64.b64encode(placeholder_buf.read()).decode('utf-8')
                rendered_html = rendered_html.replace('cid:logo', f'data:image/png;base64,{logo_base64}')
                rendered_html = rendered_html.replace('cid:logo_image', f'data:image/png;base64,{logo_base64}')
            except Exception:
                pass

        # The uploaded hero image is now handled above in the main image processing loop
        # This ensures it works with auto-detected CID references

        # Generate sample QR code for preview (only if enabled)
        if show_qr_code:
            qr_code_data = generate_qr_code_image('SAMPLE123')
            if qr_code_data:
                qr_base64 = base64.b64encode(qr_code_data.read()).decode('utf-8')
                rendered_html = rendered_html.replace('cid:qr_code', f'data:image/png;base64,{qr_base64}')

        # Add a live preview banner to distinguish from saved templates
        preview_banner = """
        <div style="background: #74b9ff; color: #2d3436; padding: 10px; text-align: center; font-weight: bold; border-bottom: 2px solid #0984e3;">
            🔴 LIVE PREVIEW - Changes not saved to database
        </div>
        """
        
        # Insert the banner at the beginning of the body
        if '<body>' in rendered_html:
            rendered_html = rendered_html.replace('<body>', f'<body>{preview_banner}')
        else:
            # Fallback if no body tag found
            rendered_html = preview_banner + rendered_html
        
        # Apply device-specific styling if mobile mode
        if device_mode == 'mobile':
            mobile_wrapper = """
            <div style="width: 375px; margin: 0 auto; border: 2px solid #ddd; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="background: #333; color: white; padding: 5px; text-align: center; font-size: 12px;">📱 Mobile Preview</div>
                <div style="max-width: 100%; overflow-x: auto;">
            """
            mobile_wrapper_end = "</div></div>"
            rendered_html = mobile_wrapper + rendered_html + mobile_wrapper_end
        
        return rendered_html
        
    except Exception as e:
        # Fallback to error message if template rendering fails
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Live Preview Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ background: #e74c3c; color: white; padding: 20px; border-radius: 8px; }}
                .template-info {{ background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>❌ Live Preview Error</h2>
                <p>Could not render live preview: {str(e)}</p>
            </div>
            <div class="template-info">
                <h3>Debug Info:</h3>
                <p><strong>Template Type:</strong> {template_type}</p>
                <p><strong>Activity:</strong> {activity.name}</p>
                <p><strong>Device Mode:</strong> {device_mode}</p>
                <p><strong>Live Customizations:</strong> {', '.join(live_customizations.keys()) if live_customizations else 'None'}</p>
            </div>
        </body>
        </html>
        """
        return error_html
        
    finally:
        # Always restore original templates
        activity.email_templates = original_templates


@app.route('/activity/<int:activity_id>/hero-image/<template_type>')
def get_hero_image(activity_id, template_type):
    """Get the current hero image for a specific template type"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    from models import Activity
    from utils import get_activity_hero_image
    from flask import Response
    import io
    
    activity = Activity.query.get_or_404(activity_id)
    
    # Get hero image data using existing utility function
    hero_data, is_custom, is_template_default = get_activity_hero_image(activity, template_type)
    
    if hero_data:
        # Return the image data as a response
        return Response(
            io.BytesIO(hero_data),
            mimetype='image/png',
            headers={'Cache-Control': 'no-cache, no-store, must-revalidate'}
        )
    else:
        # Return default hero image
        import os
        default_path = os.path.join('static', 'uploads', 'defaults', 'default_hero.png')
        if os.path.exists(default_path):
            with open(default_path, 'rb') as f:
                return Response(
                    f.read(),
                    mimetype='image/png',
                    headers={'Cache-Control': 'no-cache, no-store, must-revalidate'}
                )
        else:
            # Return a 1x1 transparent PNG as absolute fallback
            import base64
            transparent_png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==')
            return Response(
                transparent_png,
                mimetype='image/png',
                headers={'Cache-Control': 'no-cache, no-store, must-revalidate'}
            )


@app.route("/activity/<int:activity_id>/email-test", methods=["POST"])
def test_email_template(activity_id):
    """Send test email to kdresdell@gmail.com using compiled template with email blocks"""
    print("\n" + "="*80)
    print("🔥 TEST_EMAIL_TEMPLATE ROUTE CALLED - USING COMPILED TEMPLATES")
    print("="*80)
    print(f"Activity ID: {activity_id}")
    print(f"Method: {request.method}")
    print(f"Form data: {dict(request.form)}")
    print(f"Session admin: {'admin' in session}")
    
    if "admin" not in session:
        print("NOT LOGGED IN - REDIRECTING")
        return redirect(url_for("login"))
    
    from models import Activity
    from utils import send_email, get_email_context, safe_template, get_setting, generate_qr_code_image
    from flask import render_template
    from datetime import datetime
    import os
    import sys
    import json
    
    print("Admin authenticated, proceeding...")
    
    try:
        activity = Activity.query.get_or_404(activity_id)
        template_type = request.form.get('template_type', 'newPass')
        # Use logged-in admin's email, fallback to form input or default
        test_email = request.form.get('test_email') or session.get('admin', 'kdresdell@gmail.com')
        
        print(f"Activity: {activity.name}")
        print(f"Template type: {template_type}")
        
        # Create base context with email blocks (if template needs them)
        base_context = {
            'user_name': 'Test User',
            'user_email': test_email,
            'activity_name': activity.name,
            'activity': activity,  # Full activity object for templates
            'pass_code': 'TEST123',
            'amount': '$25.00',
            'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add special context for survey_invitation
        if template_type == 'survey_invitation':
            base_context['survey_name'] = 'Test Satisfaction Survey'
            base_context['survey_url'] = 'https://example.com/survey/test123'
            base_context['question_count'] = 8
            base_context['organization_name'] = get_setting('ORG_NAME', 'Fondation LHGI')
            base_context['organization_address'] = get_setting('ORG_ADDRESS', '')
            base_context['support_email'] = get_setting('SUPPORT_EMAIL', 'support@minipass.me')
            # These will be overridden by get_email_context if customized
            base_context['title'] = 'We\'d Love Your Feedback!'
            base_context['intro'] = 'Thank you for participating in our activity! We hope you had a great experience and would love to hear your thoughts.'
            base_context['conclusion'] = 'Thank you for helping us create better experiences!'

        # Add email blocks for templates that need them
        elif template_type in ['newPass', 'paymentReceived', 'redeemPass', 'latePayment']:
            # Create test pass data for email blocks
            # Using a simple class to provide dot notation access
            class PassData:
                def __init__(self):
                    self.activity = type('obj', (object,), {
                        'name': activity.name,
                        'id': activity.id,
                        'location_address_formatted': activity.location_address_formatted  # For templates that show location
                    })()
                    self.user = type('obj', (object,), {
                        'name': 'Test User',
                        'email': test_email,
                        'phone_number': '555-0123'
                    })()
                    self.pass_type = type('obj', (object,), {
                        'name': 'Test Pass',
                        'price': 25.00
                    })()
                    self.created_dt = datetime.now()
                    self.sold_amt = 25.00
                    self.paid = True
                    self.pass_code = 'TEST123'
                    self.remaining_activities = 3
                    self.uses_remaining = 3

            pass_data = PassData()

            # CRITICAL: Add pass_data to base_context so templates can access it
            base_context['pass_data'] = pass_data
            print(f"TEST EMAIL: Added pass_data to context for {template_type}")

            # Render email blocks
            base_context['owner_html'] = render_template(
                "email_blocks/owner_card_inline.html",
                pass_data=pass_data
            )

            # Add history for templates that need it
            if template_type in ['redeemPass', 'latePayment']:
                history = [
                    {'date': '2025-01-09', 'action': 'Pass Created'},
                    {'date': '2025-01-10', 'action': 'Payment Received'},
                    {'date': '2025-01-11', 'action': 'Pass Redeemed'}
                ]
                base_context['history_html'] = render_template(
                    "email_blocks/history_table_inline.html",
                    history=history
                )
            
            print(f"Added email blocks for {template_type}")
            print(f"   owner_html: {len(base_context.get('owner_html', ''))} chars")
            print(f"   history_html: {len(base_context.get('history_html', ''))} chars")

        # Add special context for signup_payment_first template
        elif template_type == 'signup_payment_first':
            base_context['needs_signup_code'] = True  # Show the signup code section
            base_context['signup_code'] = 'MP-INS-0000001'
            base_context['requested_amount'] = '$25.00'
            display_email = get_setting("DISPLAY_PAYMENT_EMAIL")
            base_context['payment_email'] = display_email if display_email else get_setting('MAIL_USERNAME', 'paiement@minipass.me')
            base_context['organization_name'] = get_setting('ORG_NAME', 'Fondation LHGI')

        # Get merged context with customizations (preserves email blocks)
        context = get_email_context(activity, template_type, base_context)
        
        # Use custom subject if available
        subject = context.get('subject', f"Test: {template_type} - {activity.name}")
        
        print(f"\n🎯 USING COMPILED TEMPLATE:")
        print(f"   Subject: {subject}")
        print(f"   To: kdresdell@gmail.com")
        print(f"   Template: {template_type}")
        print(f"   Context keys: {list(context.keys())}")
        print(f"   Has blocks: owner_html={('owner_html' in context)}, history_html={('history_html' in context)}")
        
        # Get the compiled template path
        template_path = safe_template(template_type)
        print(f"   Template path: {template_path}")
        
        # Load inline images for compiled template
        compiled_folder = template_path.replace('/index.html', '')
        json_path = os.path.join('templates', compiled_folder, 'inline_images.json')
        inline_images = {}
        
        # Use the proper hero image utility function to determine current hero
        from utils import get_activity_hero_image
        hero_data, is_custom_hero, is_template_default = get_activity_hero_image(activity, template_type)
        has_custom_hero = hero_data is not None and is_custom_hero
        
        print(f"TEST EMAIL: Custom hero found: {has_custom_hero}, is_custom: {is_custom_hero}")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                inline_images_data = json.load(f)
                # Convert base64 strings to bytes
                import base64

                for img_id, base64_data in inline_images_data.items():
                    try:
                        # Skip hero-related images if we have a custom hero image
                        expected_hero_cid = HERO_CID_MAP.get(template_type, f'hero_{template_type}')
                        if (img_id == expected_hero_cid and has_custom_hero):
                            print(f"TEST EMAIL: Skipping template hero '{img_id}' because custom hero exists")
                            continue
                            
                        # The JSON contains base64-encoded image data directly
                        inline_images[img_id] = base64.b64decode(base64_data)
                        print(f"   Loaded inline image: {img_id} ({len(inline_images[img_id])} bytes)")
                    except Exception as e:
                        print(f"   ⚠️ Failed to decode image {img_id}: {e}")
        
        # Add logo image (same resolution as email send in utils.py)
        logo_path = None
        # Check for activity-specific owner logo first (custom upload via template editor)
        activity_logo_path = os.path.join('static', 'uploads', f'{activity.id}_owner_logo.png')
        if os.path.exists(activity_logo_path):
            logo_path = activity_logo_path
        if not logo_path:
            # Use organization logo from settings as fallback
            org_logo = get_setting('LOGO_FILENAME', 'logo.png')
            logo_path = os.path.join('static', 'uploads', org_logo)
        if not logo_path or not os.path.exists(logo_path):
            # Try placeholder before minipass fallback
            from utils import generate_placeholder_logo_image
            org_name = get_setting('ORG_NAME', 'Minipass')
            try:
                placeholder_buf = generate_placeholder_logo_image(org_name)
                inline_images['logo'] = placeholder_buf.read()
                logo_path = None  # Skip file-based loading below
                print(f"   Added placeholder logo for '{org_name}'")
            except Exception:
                logo_path = 'static/minipass_logo.png'
        if logo_path and os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                inline_images['logo'] = logo_data
                print(f"   Added logo: {logo_path} ({len(logo_data)} bytes)")
        
        # Add custom hero image if it exists
        if has_custom_hero:
            expected_hero_cid = HERO_CID_MAP.get(template_type, f'hero_{template_type}')
            inline_images[expected_hero_cid] = hero_data
            print(f"TEST EMAIL: Added custom hero image for CID '{expected_hero_cid}' ({len(hero_data)} bytes)")

        # Generate QR code for test email
        qr_code_data = generate_qr_code_image('TEST123')
        if qr_code_data:
            inline_images['qr_code'] = qr_code_data.read()
            print(f"   Added QR code: {len(inline_images['qr_code'])} bytes")

        print("\n🚀 CALLING send_email() with compiled template...")
        sys.stdout.flush()
        
        # Send using compiled template
        result = send_email(
            subject=subject,
            to_email=test_email,
            template_name=template_path,
            context=context,
            inline_images=inline_images if inline_images else None
        )
        
        print(f"\n✅ send_email() RETURNED: {result}")
        
        flash(f"Test email sent using compiled template to {test_email}", "success")
        
        # Log it for debugging
        print(f"\n📬 TEST EMAIL SENT: {subject} to {test_email}")
        print(f"📬 Template: {template_path}")
        print(f"📬 Return value: {result}")
        print("="*80 + "\n")
        sys.stdout.flush()
        
        return jsonify({'success': True, 'message': f'Test email sent successfully to {test_email}'})
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"\n❌ ERROR SENDING TEST EMAIL:")
        print(error_detail)
        print("="*80 + "\n")
        sys.stdout.flush()  # Force flush output
        return jsonify({'success': False, 'message': str(e)})


# ================================
# 🖼 ACTIVITY LOGO UPLOAD ROUTES
# ================================

def get_activity_logo_url(activity):
    """Get logo URL for activity with fallback to default logo"""
    if activity and activity.logo_filename:
        return url_for('static', filename=f'uploads/logos/{activity.logo_filename}')
    return url_for('static', filename='minipass_logo.png')


@app.route('/activity/<int:activity_id>/upload-logo', methods=['POST'])
def upload_activity_logo(activity_id):
    """Handle logo upload for activities"""
    if "admin" not in session:
        return jsonify({"success": False, "error": "Not authorized"}), 401
    
    from models import Activity
    from werkzeug.utils import secure_filename
    import os
    
    activity = Activity.query.get_or_404(activity_id)
    
    # Check if logo file was uploaded
    if 'logo_file' not in request.files:
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    logo_file = request.files['logo_file']
    
    # Check if a file was actually selected
    if logo_file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    # Validate file type
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if not allowed_file(logo_file.filename):
        return jsonify({"success": False, "error": "Invalid file type. Please use PNG, JPG, JPEG, or GIF."}), 400
    
    try:
        # Create logos directory if it doesn't exist
        logos_dir = os.path.join('static', 'uploads', 'logos')
        os.makedirs(logos_dir, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        filename = secure_filename(logo_file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"activity_{activity_id}_{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        logo_path = os.path.join(logos_dir, unique_filename)
        
        # Delete old logo if exists
        if activity.logo_filename:
            old_logo_path = os.path.join(logos_dir, activity.logo_filename)
            if os.path.exists(old_logo_path):
                os.remove(old_logo_path)
                print(f"Deleted old logo: {old_logo_path}")
        
        # Save new logo
        logo_file.save(logo_path)
        
        # Validate file size (max 5MB)
        if os.path.getsize(logo_path) > 5 * 1024 * 1024:  # 5MB limit
            os.remove(logo_path)
            return jsonify({"success": False, "error": "File too large. Maximum size is 5MB."}), 400
        
        # Update activity with new logo filename
        activity.logo_filename = unique_filename
        db.session.commit()
        
        # Return success response with logo URL
        logo_url = get_activity_logo_url(activity)
        
        return jsonify({
            "success": True, 
            "message": "Logo uploaded successfully!",
            "logo_url": logo_url
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Upload failed: {str(e)}"}), 500


@app.route('/activity/<int:activity_id>/delete-logo', methods=['POST'])
def delete_activity_logo(activity_id):
    """Delete activity logo and revert to default"""
    if "admin" not in session:
        return jsonify({"success": False, "error": "Not authorized"}), 401
    
    from models import Activity
    import os
    
    activity = Activity.query.get_or_404(activity_id)
    
    try:
        # Delete logo file if exists
        if activity.logo_filename:
            logo_path = os.path.join('static', 'uploads', 'logos', activity.logo_filename)
            if os.path.exists(logo_path):
                os.remove(logo_path)
                print(f"Deleted logo file: {logo_path}")
            
            # Clear logo filename from database
            activity.logo_filename = None
            db.session.commit()
        
        # Return default logo URL
        default_logo_url = url_for('static', filename='minipass_logo.png')
        
        return jsonify({
            "success": True, 
            "message": "Logo deleted successfully!",
            "logo_url": default_logo_url
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Delete failed: {str(e)}"}), 500


@app.route('/unsubscribe', methods=['GET', 'POST'])
@csrf.exempt
def unsubscribe():
    """Handle email unsubscribe requests"""
    from models import User
    import hashlib
    
    if request.method == 'GET':
        email = request.args.get('email', '')
        token = request.args.get('token', '')
        
        # Simple unsubscribe form
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Unsubscribe - Minipass</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
                       max-width: 500px; margin: 50px auto; padding: 20px; }}
                .form {{ background: #f8f9fa; padding: 30px; border-radius: 8px; }}
                input, button {{ width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; 
                                border-radius: 4px; box-sizing: border-box; }}
                button {{ background: #dc3545; color: white; cursor: pointer; }}
                button:hover {{ background: #c82333; }}
                .success {{ color: #28a745; }} .error {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="form">
                <h2>Unsubscribe from Minipass Emails</h2>
                <p>Enter your email address to opt out of future emails:</p>
                <form method="POST">
                    <input type="email" name="email" placeholder="your@email.com" value="{email}" required>
                    <input type="hidden" name="token" value="{token}">
                    <button type="submit">Unsubscribe</button>
                </form>
                <p><small>This will stop all promotional emails. You may still receive transactional emails related to your purchases.</small></p>
            </div>
        </body>
        </html>
        '''
    
    elif request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        token = request.form.get('token', '')
        
        if not email:
            return "Email address is required", 400
        
        try:
            # Find user and set opt-out
            user = User.query.filter_by(email=email).first()
            if user:
                user.email_opt_out = True
                db.session.commit()
                message = f"Successfully unsubscribed {email} from future emails."
            else:
                # Even if user not found, show success message for privacy
                message = f"Successfully unsubscribed {email} from future emails."
            
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Unsubscribed - Minipass</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
                           max-width: 500px; margin: 50px auto; padding: 20px; }}
                    .success {{ background: #d4edda; padding: 30px; border-radius: 8px; 
                              color: #155724; border: 1px solid #c3e6cb; }}
                </style>
            </head>
            <body>
                <div class="success">
                    <h2>✅ Unsubscribed Successfully</h2>
                    <p>{message}</p>
                    <p>If you need to resubscribe in the future, please contact support@minipass.me</p>
                </div>
            </body>
            </html>
            '''
            
        except Exception as e:
            print(f"Unsubscribe error: {e}")
            return "An error occurred. Please try again later.", 500


@app.route('/admin/subscription', methods=['GET', 'POST'])
def admin_subscription():
    """Subscription management page for admin"""
    if "admin" not in session:
        return redirect(url_for("login"))

    # Load subscription info from file
    subscription_file = os.path.join('instance', 'subscription.json')
    subscription_info = None
    error_message = None
    success_message = None

    try:
        if os.path.exists(subscription_file):
            with open(subscription_file, 'r') as f:
                subscription_info = json.load(f)
        else:
            error_message = "Subscription information not found. This may be a legacy deployment."
    except Exception as e:
        error_message = f"Error loading subscription info: {str(e)}"

    # Handle POST request (cancellation)
    if request.method == 'POST' and subscription_info:
        action = request.form.get('action')

        if action == 'cancel':
            try:
                stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                subscription_id = subscription_info.get('stripe_subscription_id')

                if not subscription_id:
                    flash("Subscription ID not found. Unable to cancel.", "error")
                    return redirect(url_for('admin_subscription'))

                # Cancel subscription at period end
                updated_subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )

                # Update the JSON file to reflect cancellation
                subscription_info['cancel_at_period_end'] = True
                subscription_info['cancelled_at'] = datetime.now().isoformat()

                with open(subscription_file, 'w') as f:
                    json.dump(subscription_info, f, indent=2)

                flash("Subscription cancelled successfully. Access will continue until the end of your billing period.", "success")
                return redirect(url_for('admin_subscription'))

            except stripe.error.StripeError as e:
                flash(f"Stripe error: {str(e)}", "error")
                return redirect(url_for('admin_subscription'))
            except Exception as e:
                flash(f"Error cancelling subscription: {str(e)}", "error")
                return redirect(url_for('admin_subscription'))

    # Render subscription management page
    return render_template('admin/subscription.html',
                         subscription_info=subscription_info,
                         error_message=error_message,
                         success_message=success_message)


@app.route('/privacy', methods=['GET'])
def privacy():
    """Privacy Policy page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Privacy Policy - Foundation LHGI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
                max-width: 800px; 
                margin: 40px auto; 
                padding: 20px; 
                line-height: 1.6;
                color: #333;
            }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .container { background: #f8f9fa; padding: 30px; border-radius: 8px; }
            .contact { background: #e3f2fd; padding: 20px; border-radius: 6px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Privacy Policy</h1>
            <p><strong>Foundation LHGI</strong> is committed to protecting your privacy.</p>
            
            <h2>Information We Collect</h2>
            <p>We collect information you provide when you:</p>
            <ul>
                <li>Sign up for activities</li>
                <li>Create an account</li>
                <li>Make payments</li>
                <li>Contact us for support</li>
            </ul>
            
            <h2>How We Use Your Information</h2>
            <p>We use your information to:</p>
            <ul>
                <li>Process registrations and payments</li>
                <li>Send activity confirmations and updates</li>
                <li>Provide customer support</li>
                <li>Improve our services</li>
            </ul>
            
            <h2>Email Communications</h2>
            <p>We may send you emails related to:</p>
            <ul>
                <li>Activity confirmations</li>
                <li>Payment receipts</li>
                <li>Account updates</li>
                <li>Service announcements</li>
            </ul>
            <p>You can unsubscribe from promotional emails at any time using the unsubscribe link in our emails.</p>
            
            <h2>Data Security</h2>
            <p>We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.</p>
            
            <div class="contact">
                <h2>Contact Us</h2>
                <p>If you have questions about this privacy policy, please contact us at:</p>
                <p><strong>Email:</strong> lhgi@minipass.me</p>
                <p><strong>Address:</strong> 821 rue des Sables, Rimouski, QC G5L 6Y7</p>
            </div>
            
            <p><small>Last updated: September 2025</small></p>
        </div>
    </body>
    </html>
    '''


if __name__ == "__main__":
    port = 5000
    print(f"🚀 Running on port {port}")
    app.run(host='0.0.0.0', debug=True, port=port)
