# 📦 Core Python Modules
import os
import io
import re
import uuid
import json
import base64
import socket
import hashlib
import bcrypt
import stripe
import qrcode
import subprocess
import logging
import traceback
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# 🌐 Flask Core
from flask import (
    Flask, render_template, render_template_string, request, redirect,
    url_for, session, flash, get_flashed_messages, jsonify, current_app, make_response, Response
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
from models import db, Admin, Pass, Redemption, Setting, EbankPayment, ReminderLog, EmailLog
from models import Activity, User, Signup, Passport, PassportType, AdminActionLog, Organization
from models import SurveyTemplate, Survey, SurveyResponse
from models import ChatConversation, ChatMessage, QueryLog, ChatUsage


# ⚙️ Config
from config import Config

# 🔒 Security Decorators
from decorators import rate_limit, admin_required, log_api_call, cache_response

# 🎯 KPI Card Component
from components.kpi_card import generate_kpi_card, generate_dashboard_cards

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
    get_kpi_stats,
    notify_pass_event,
    notify_signup_event,
    generate_pass_code,
    generate_survey_token,
    generate_response_token
)

# 🧠 Data Tools
from collections import defaultdict

# ✅ Old chatbot imports removed - using new chatbot_v2 blueprint instead


# ✅ Pass the full datetime object
from utils import send_email, generate_qr_code_image, get_pass_history_data, get_setting
from flask import render_template, render_template_string, url_for

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

import requests
from flask import send_from_directory


from flask import render_template, request, redirect, url_for, session, flash
from datetime import datetime
from models import Signup, Activity, User, db


from models import Admin, Activity, Passport, User, db
from utils import get_setting, notify_pass_event

from models import Passport, User, AdminActionLog, Activity
import time



from flask import render_template, request, redirect, url_for, flash
from models import db, Activity, Income
from datetime import datetime


from models import Expense
import os
import uuid
from datetime import datetime as dt




db_path = os.path.join("instance", "minipass.db")
print(f"📦 Using database → {db_path}")



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'activity_images')





app.config.from_object(Config)

# ✅ Initialize database
db.init_app(app)




migrate = Migrate(app, db)


#if not os.path.exists(db_path):
#    print(f"❌ {db_path} is missing!")
#    exit(1)


print(f"📂 Connected DB path: {app.config['SQLALCHEMY_DATABASE_URI']}")


UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Set up logging
logger = logging.getLogger(__name__)

csrf = CSRFProtect(app)
app.config["SECRET_KEY"] = "MY_SECRET_KEY_FOR_NOW"

app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour

# 🤖 Register Chatbot Blueprint - Using simplified version
try:
    from chatbot_v2.routes_simple import chatbot_bp
    app.register_blueprint(chatbot_bp)
    print("✅ Simplified chatbot registered successfully")
    
    # Register Settings API Blueprint
    from api.settings import settings_api
    app.register_blueprint(settings_api)
    print("✅ Settings API registered successfully")
    
    
    # List routes to verify
    for rule in app.url_map.iter_rules():
        if 'chatbot' in rule.rule:
            print(f"  🗗 {rule.rule} -> {rule.endpoint}")
    
    # Exempt chatbot API from CSRF for testing
    csrf.exempt(chatbot_bp)
    print("✅ Chatbot API exempted from CSRF")
    
    # Add test notification route
    @app.route("/test-notifications")
    def test_notifications():
        """Test page for SSE notifications"""
        if "admin" not in session:
            return redirect(url_for("login"))
        return render_template("test_notifications.html")
except Exception as e:
    print(f"❌ Simple Chatbot registration failed: {e}")
    import traceback
    traceback.print_exc()

import hashlib

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
                # Payment bot setup
                if get_setting("ENABLE_EMAIL_PAYMENT_BOT", "False") == "True":
                    print("🟢 Email Payment Bot is ENABLED. Scheduling job every 30 minutes.")
                    def run_payment_bot():
                        with app.app_context():
                            match_gmail_payments_to_passes()
                    
                    scheduler.add_job(run_payment_bot, trigger="interval", minutes=30, id="email_payment_bot")
                else:
                    print("⚪ Email Payment Bot is DISABLED. No job scheduled.")
                
                # Unpaid reminders setup
                scheduler.add_job(func=lambda: send_unpaid_reminders(app), trigger="interval", days=1, id="unpaid_reminders")
                
                # Start the scheduler
                scheduler.start()
                print("✅ Scheduler initialized and started successfully (master worker).")
                
            except OperationalError as e:
                print("⚠️ DB not ready yet (probably during initial setup), skipping scheduler setup.")
            except Exception as e:
                print(f"❌ Error initializing scheduler: {e}")
    
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
    
    # Calculate pending signups count for sidebar badge
    pending_signups_count = 0
    active_passport_count = 0
    current_admin = None
    
    try:
        if "admin" in session:  # Only calculate if admin is logged in
            pending_signups_count = Signup.query.filter_by(status='pending').count()
            # Calculate active passports (uses_remaining > 0)
            active_passport_count = Passport.query.filter(Passport.uses_remaining > 0).count()
            # Get current admin info for personalization
            current_admin = Admin.query.filter_by(email=session.get("admin")).first()
    except Exception:
        # If there's any database error, default to 0
        pending_signups_count = 0
        active_passport_count = 0
        current_admin = None
    
    return {
        'now': datetime.now(timezone.utc),
        'ORG_NAME': get_setting("ORG_NAME", "Ligue hockey Gagnon Image"),
        'git_branch': get_git_branch(),
        'csrf_token': generate_csrf,  # returns the raw CSRF token
        'pending_signups_count': pending_signups_count,
        'active_passport_count': active_passport_count,
        'current_admin': current_admin  # Add current admin for template personalization
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

    from models import EmailLog, Pass
    from utils import send_email_async
    from datetime import datetime

    failed_logs = EmailLog.query.filter_by(result="FAILED").all()
    retried = 0

    # 🔁 Replace with your email for testing
    override_email = "kdresdell@gmail.com"
    #testing_mode = True
    testing_mode = False

    for log in failed_logs:
        pass_obj = Pass.query.filter_by(pass_code=log.pass_code).first()
        if not pass_obj:
            continue  # Skip if no matching pass

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
            created_date=context.get("created_date", datetime.utcnow().strftime("%Y-%m-%d")),
            remaining_games=context.get("remaining_games", 0),
            special_message=context.get("special_message", None),
            admin_email=session.get("admin")
        )

        retried += 1

    flash(f"📤 Retried {retried} failed email(s) — sent to {override_email}.", "info")
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
    if "admin" not in session:
        return redirect(url_for("login"))

    activities = Activity.query.all()
    return render_template("index.html", activities=activities)




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

    from utils import get_kpi_stats, get_all_activity_logs
    from models import Activity, Signup, Passport, db
    from sqlalchemy.sql import func
    from datetime import datetime
    
    # Try to use the new KPICard component for all dashboard cards, fallback to original
    try:
        from components.kpi_card import generate_kpi_card
        revenue_card_data = generate_kpi_card('revenue')
        active_passports_card_data = generate_kpi_card('active_passports')
        passports_created_card_data = generate_kpi_card('passports_created')
        pending_signups_card_data = generate_kpi_card('pending_signups')
    except Exception as e:
        print(f"Failed to use KPICard component: {e}")
        revenue_card_data = None
        active_passports_card_data = None
        passports_created_card_data = None
        pending_signups_card_data = None

    kpi_data = get_kpi_stats()
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
        active_passports = [p for p in paid_passports if p.uses_remaining > 0]

        # Revenue
        paid_amount = round(sum(p.sold_amt for p in paid_passports), 2)
        unpaid_amount = round(sum(p.sold_amt for p in unpaid_passports), 2)

        # Optional: Days left
        if a.end_date:
            days_left = max((a.end_date - datetime.utcnow()).days, 0)
        else:
            days_left = "N/A"

        # Get passport type information for this activity
        passport_types = PassportType.query.filter_by(activity_id=a.id).all()
        total_sessions = sum(pt.sessions_included or 0 for pt in passport_types) if passport_types else 0
        total_target_revenue = sum(pt.target_revenue or 0 for pt in passport_types) if passport_types else 0.0
        
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
            "goal_revenue": total_target_revenue,
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

    return render_template(
        "dashboard.html",
        activities=activity_cards,
        kpi_data=kpi_data,
        passport_stats=passport_stats,
        signup_stats=signup_stats,
        active_passport_count=active_passport_count,
        logs=all_logs,
        revenue_card=revenue_card_data,  # Add the new revenue card data
        active_passports_card=active_passports_card_data,  # Add active passports card
        passports_created_card=passports_created_card_data,  # Add passports created card
        pending_signups_card=pending_signups_card_data  # Add pending signups card
    )




@app.route("/admin/signup/mark-paid/<int:signup_id>", methods=["POST"])
def mark_signup_paid(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
        return redirect(url_for("list_signups"))

    signup.paid = True
    signup.paid_at = datetime.utcnow()
    db.session.commit()
    
    # Emit SSE notification for signup payment
    # SSE notifications removed for leaner performance

    flash(f"✅ Marked {signup.user.name}'s signup as paid.", "success")
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
                         current_filters={
                             'q': q,
                             'activity_id': activity_id,
                             'payment_status': payment_status,
                             'status': signup_status,
                             'start_date': start_date,
                             'end_date': end_date
                         })


@app.route("/signups/bulk-action", methods=["POST"])
def bulk_signup_action():
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Signup, User, Activity
    
    action = request.form.get('action')
    selected_ids = request.form.getlist('selected_signups')
    
    if not selected_ids:
        flash("❌ No signups selected.", "error")
        return redirect(url_for("list_signups"))
    
    try:
        selected_ids = [int(id) for id in selected_ids]
        signups = Signup.query.filter(Signup.id.in_(selected_ids)).all()
        
        if not signups:
            flash("❌ No valid signups found.", "error")
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
            
            flash(f"✅ {count} signups marked as paid.", "success")
            
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
            
            flash(f"✅ Payment reminders sent to {count} signups.", "success")
            
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
            
            flash(f"✅ {count} signups approved.", "success")
            
        elif action == 'delete':
            count = len(signups)
            signup_info = [f"{s.user.name} - {s.activity.name}" for s in signups]
            
            for signup in signups:
                db.session.delete(signup)
            
            db.session.commit()
            
            # Log admin action
            db.session.add(AdminActionLog(
                admin_email=admin_email,
                action=f"Deleted {count} signups: {', '.join(signup_info[:5])}{'...' if len(signup_info) > 5 else ''}"
            ))
            db.session.commit()
            
            flash(f"✅ {count} signups deleted.", "success")
            
        else:
            flash("❌ Invalid action.", "error")
            
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error processing bulk action: {str(e)}", "error")
    
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
        flash("❌ Signup not found.", "error")
        return redirect(url_for("list_signups"))

    from models import Passport

    # Check if a passport already exists
    existing_passport = Passport.query.filter_by(user_id=signup.user_id, activity_id=signup.activity_id).first()
    if existing_passport:
        flash("⚠️ A passport for this user and activity already exists.", "warning")
        return redirect(url_for("list_signups"))

    # Get passport type from signup or fallback to first one for this activity
    passport_type = None
    if signup.passport_type_id:
        passport_type = PassportType.query.get(signup.passport_type_id)
    else:
        passport_type = PassportType.query.filter_by(activity_id=signup.activity_id).first()
    
    # Create new passport
    new_passport = Passport(
        pass_code=f"MP{datetime.utcnow().timestamp():.0f}",
        user_id=signup.user_id,
        activity_id=signup.activity_id,
        passport_type_id=passport_type.id if passport_type else None,
        passport_type_name=passport_type.name if passport_type else None,  # Preserve type name
        sold_amt=passport_type.price_per_user if passport_type else 0.0,
        uses_remaining=passport_type.sessions_included if passport_type else 1,
        created_dt=datetime.utcnow(),
        paid=signup.paid,
        notes=f"Created from signup {signup.id}"
    )
    db.session.add(new_passport)
    db.session.commit()

    flash("✅ Passport created from signup!", "success")
    return redirect(url_for("list_signups"))



@app.route("/admin/signup/edit/<int:signup_id>", methods=["GET", "POST"])
def edit_signup(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
        return redirect(url_for("list_signups"))

    if request.method == "POST":
        signup.subject = request.form.get("subject", "").strip()
        signup.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("✅ Signup updated.", "success")
        return redirect(url_for("list_signups"))

    return render_template("edit_signup.html", signup=signup)



@app.route("/signup/status/<int:signup_id>", methods=["POST"])
def update_signup_status(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
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

        flash(f"✅ Signup marked as {status}.", "success")
    else:
        flash("❌ Invalid status.", "error")

    return redirect(url_for("list_signups"))




@app.route("/signup/approve-create-pass/<int:signup_id>")
def approve_and_create_pass(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
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
        passport_type = PassportType.query.get(signup.passport_type_id)
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

    # ✅ Step 4: Log admin action
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
        from models import Activity, PassportType, AdminActionLog, db
        import os
        import uuid

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")

        start_date = datetime.strptime(start_date_raw, "%Y-%m-%d") if start_date_raw else None
        end_date = datetime.strptime(end_date_raw, "%Y-%m-%d") if end_date_raw else None

        name = request.form.get("name", "").strip()
        activity_type = request.form.get("type", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "active")

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

        # Create the activity
        new_activity = Activity(
            name=name,
            type=activity_type,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            created_by=session.get("admin"),
            image_filename=image_filename,
        )

        db.session.add(new_activity)
        db.session.flush()  # Get the activity ID

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
                    type=passport_data.get('type', 'permanent'),
                    price_per_user=float(passport_data.get('price_per_user', 0.0)),
                    sessions_included=int(passport_data.get('sessions_included', 1)),
                    target_revenue=float(passport_data.get('target_revenue', 0.0)),
                    payment_instructions=passport_data.get('payment_instructions', '').strip(),
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

        flash(f"✅ Activity created successfully with {len(passport_types_data)} passport types!", "success")
        return redirect(url_for("edit_activity", activity_id=new_activity.id))

    # ✅ GET request
    return render_template("activity_form.html", activity=None)


@app.route("/edit-activity/<int:activity_id>", methods=["GET", "POST"])
def edit_activity(activity_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    activity = db.session.get(Activity, activity_id)

    if not activity:
        flash("❌ Activity not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        import os
        import uuid

        activity.name = request.form.get("name", "").strip()
        activity.type = request.form.get("type", "").strip()
        activity.description = request.form.get("description", "").strip()
        activity.status = request.form.get("status", "active")

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")

        activity.start_date = datetime.strptime(start_date_raw, "%Y-%m-%d") if start_date_raw else None
        activity.end_date = datetime.strptime(end_date_raw, "%Y-%m-%d") if end_date_raw else None

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
                    passport_type.type = passport_data.get('type', 'permanent')
                    passport_type.price_per_user = float(passport_data.get('price_per_user', 0.0))
                    passport_type.sessions_included = int(passport_data.get('sessions_included', 1))
                    passport_type.target_revenue = float(passport_data.get('target_revenue', 0.0))
                    passport_type.payment_instructions = passport_data.get('payment_instructions', '').strip()
                    
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
                        type=passport_data.get('type', 'permanent'),
                        price_per_user=float(passport_data.get('price_per_user', 0.0)),
                        sessions_included=int(passport_data.get('sessions_included', 1)),
                        target_revenue=float(passport_data.get('target_revenue', 0.0)),
                        payment_instructions=passport_data.get('payment_instructions', '').strip(),
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

        flash(f"✅ Activity updated successfully! Created: {passport_types_created}, Updated: {passport_types_updated}, Archived: {passport_types_archived} passport types.", "success")
        return redirect(url_for("edit_activity", activity_id=activity.id))

    # 🧮 Add financial summary data (shown at bottom of form)
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
        "total_expenses": total_expenses,
        "net_income": net_income
    }

    # Get passport types for this activity
    passport_types_objects = PassportType.query.filter_by(activity_id=activity.id).all()
    
    # Convert to dictionaries for JSON serialization
    passport_types = []
    for pt in passport_types_objects:
        passport_types.append({
            'id': pt.id,
            'name': pt.name,
            'type': pt.type,
            'price_per_user': pt.price_per_user,
            'sessions_included': pt.sessions_included,
            'target_revenue': pt.target_revenue,
            'payment_instructions': pt.payment_instructions or ''
        })
    
    return render_template("activity_form.html", activity=activity, passport_types=passport_types, summary=summary)




@app.route("/signup/<int:activity_id>", methods=["GET", "POST"])
def signup(activity_id):
    activity = db.session.get(Activity, activity_id)
    if not activity:
        flash("❌ Activity not found.", "error")
        return redirect(url_for("dashboard"))

    # Get passport type if specified
    passport_type_id = request.args.get('passport_type_id')
    selected_passport_type = None
    if passport_type_id:
        selected_passport_type = PassportType.query.get(passport_type_id)
    
    # Get all passport types for this activity
    passport_types = PassportType.query.filter_by(activity_id=activity.id, status='active').all()

    # ✅ Corrected settings loading
    settings = {s.key: s.value for s in Setting.query.all()}

    if request.method == "POST":
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
            passport_type = PassportType.query.get(selected_passport_type_id)
        
        signup = Signup(
            user_id=user.id,
            activity_id=activity.id,
            passport_type_id=selected_passport_type_id if selected_passport_type_id else None,
            subject=f"Signup for {activity.name}" + (f" - {passport_type.name}" if passport_type else ""),
            description=request.form.get("notes", "").strip(),
            form_data="",
        )
        db.session.add(signup)
        db.session.commit()

        from utils import notify_signup_event
        notify_signup_event(app, signup=signup, activity=activity)
        
        # SSE notifications removed for leaner performance

        flash("✅ Signup submitted!", "success")
        return redirect(url_for("signup_thank_you", signup_id=signup.id))

    return render_template("signup_form.html", activity=activity, settings=settings, 
                         passport_types=passport_types, selected_passport_type=selected_passport_type)


@app.route("/signup/thank-you/<int:signup_id>")
def signup_thank_you(signup_id):
    """Thank you page after successful signup"""
    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
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
                flash(f"✅ Test completed! {result.get('matched', 0)} payments matched.", "success")
            else:
                flash("✅ Test completed! No new payments found.", "info")
                
        except Exception as e:
            print(f"❌ Payment bot test error: {e}")
            flash(f"❌ Test failed: {str(e)}", "error")
        
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
        
        flash("✅ Email Payment Bot settings saved successfully!", "success")
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
    
    # Get payment email address from settings (hardcoded fallback for safety)
    payment_email = get_setting("PAYMENT_EMAIL_ADDRESS", "lhgi@minipass.me")
    
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
        print("❌ Unauthorized - no admin in session")
        return jsonify({"error": "Unauthorized"}), 401
    
    from utils import match_gmail_payments_to_passes, get_setting, log_admin_action
    
    # Check if payment bot is enabled
    if get_setting("ENABLE_EMAIL_PAYMENT_BOT", "False") != "True":
        return jsonify({"error": "Payment bot is not enabled in settings"}), 400
    
    try:
        # Log the action first
        log_admin_action(f"Manual payment bot check triggered by {session.get('admin', 'Unknown')}")
        
        # Run the email checking function
        result = match_gmail_payments_to_passes()
        
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
                # Update existing admin
                if password and password != "********":
                    existing.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
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
            "EMAIL_FOOTER_TEXT": REMOVED_FIELD_DEFAULTS['email_footer_text'],
            "ORG_NAME": request.form.get("ORG_NAME", "").strip(),
            "CALL_BACK_DAYS": request.form.get("CALL_BACK_DAYS", "0").strip()
        }

        for key, value in extra_settings.items():
            existing = Setting.query.filter_by(key=key).first()
            if existing:
                existing.value = value
            else:
                db.session.add(Setting(key=key, value=value))

        # 🤖 Step 5: Email Payment Bot Config
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
            print("❌ Failed to save activity list:", e)

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

            flash("✅ Logo uploaded successfully!", "success")

        # ✅ Step 8: Save email notification templates (including signup and survey_invitation)
        for event in ["pass_created", "pass_redeemed", "payment_received", "payment_late", "signup", "survey_invitation"]:
            for key in ["SUBJECT", "TITLE", "INTRO", "CONCLUSION", "THEME"]:
                full_key = f"{key}_{event}"
                value = request.form.get(full_key, "").strip()
                if value:
                    existing = Setting.query.filter_by(key=full_key).first()
                    if existing:
                        existing.value = value
                    else:
                        db.session.add(Setting(key=full_key, value=value))

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
    print("🗂️ Available backups in static/backups/:", os.listdir("static/backups"))

    template_base = os.path.join("templates", "email_templates")
    email_templates = []

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

    return render_template(
        "setup.html",
        settings=settings,
        admins=admins,
        backup_file=backup_file,
        backup_files=backup_files,
        email_templates=email_templates
    )


# ================================
# 📧 ORGANIZATION EMAIL MANAGEMENT
# ================================

@app.route("/admin/organizations")
def list_organizations():
    """List all organizations with their email configurations"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    organizations = Organization.query.all()
    return jsonify({
        'organizations': [{
            'id': org.id,
            'name': org.name,
            'domain': org.domain,
            'full_email': org.full_email_address,
            'email_enabled': org.email_enabled,
            'is_active': org.is_active,
            'mail_server': org.mail_server,
            'mail_username': org.mail_username,
            'sender_name': org.mail_sender_name,
            'created_at': org.created_at.isoformat() if org.created_at else None,
            'updated_at': org.updated_at.isoformat() if org.updated_at else None
        } for org in organizations]
    })


@app.route("/admin/organizations/create", methods=["POST"])
def create_organization():
    """Create a new organization with email configuration"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    try:
        from utils import create_organization_email_config
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'domain', 'mail_server', 'mail_username', 'mail_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create organization
        org = create_organization_email_config(
            name=data['name'],
            domain=data['domain'],
            mail_server=data['mail_server'],
            mail_username=data['mail_username'],
            mail_password=data['mail_password'],
            mail_sender_name=data.get('mail_sender_name'),
            mail_port=int(data.get('mail_port', 587)),
            mail_use_tls=data.get('mail_use_tls', True),
            created_by=session.get('admin')
        )
        
        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Organization '{org.name}' created with email configuration"
        ))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Organization created successfully',
            'organization_id': org.id
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to create organization: {str(e)}'}), 500


@app.route("/admin/organizations/<int:org_id>/update", methods=["PUT"])
def update_organization(org_id):
    """Update organization email configuration"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    try:
        from utils import update_organization_email_config
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add updated_by to the data
        data['updated_by'] = session.get('admin')
        
        # Update organization
        org = update_organization_email_config(org_id, **data)
        
        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Organization '{org.name}' email configuration updated"
        ))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Organization updated successfully'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to update organization: {str(e)}'}), 500


@app.route("/admin/organizations/<int:org_id>/test", methods=["POST"])
def test_organization_email(org_id):
    """Test organization email configuration"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    try:
        from utils import test_organization_email_config
        
        success, message = test_organization_email_config(org_id)
        
        # Log admin action
        org = Organization.query.get(org_id)
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Email configuration test for '{org.name if org else 'Unknown'}': {message}"
        ))
        db.session.commit()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': f'Test failed: {str(e)}'}), 500


@app.route("/admin/organizations/<int:org_id>/toggle", methods=["POST"])
def toggle_organization_email(org_id):
    """Toggle organization email enabled status"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    try:
        org = Organization.query.get_or_404(org_id)
        org.email_enabled = not org.email_enabled
        org.updated_by = session.get('admin')
        org.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        status = "enabled" if org.email_enabled else "disabled"
        
        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Organization '{org.name}' email {status}"
        ))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Organization email {status}',
            'email_enabled': org.email_enabled
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to toggle organization: {str(e)}'}), 500


@app.route("/admin/organizations/<int:org_id>/delete", methods=["DELETE"])
def delete_organization(org_id):
    """Delete organization (soft delete by marking as inactive)"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    try:
        org = Organization.query.get_or_404(org_id)
        org_name = org.name
        
        # Soft delete - just mark as inactive
        org.is_active = False
        org.email_enabled = False
        org.updated_by = session.get('admin')
        org.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Organization '{org_name}' deactivated"
        ))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Organization deactivated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete organization: {str(e)}'}), 500


# Test route for quickly creating LHGI organization
@app.route("/admin/create-test-org", methods=["POST"])
def create_test_org():
    """Create test organization for LHGI (development/testing purposes)"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    try:
        from utils import create_organization_email_config
        
        # Check if LHGI already exists
        existing = Organization.query.filter_by(domain='lhgi').first()
        if existing:
            return jsonify({'error': 'LHGI organization already exists'}), 400
        
        # Create LHGI organization with test credentials
        org = create_organization_email_config(
            name="LHGI",
            domain="lhgi",
            mail_server="mail.minipass.me",
            mail_username="lhgi@minipass.me",
            mail_password="monsterinc00",
            mail_sender_name="LHGI",
            mail_port=587,
            mail_use_tls=True,
            created_by=session.get('admin')
        )
        
        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Test organization 'LHGI' created"
        ))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'LHGI test organization created successfully',
            'organization_id': org.id
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to create test organization: {str(e)}'}), 500


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
                flash(f"✅ Payment bot test completed. {result.get('matched', 0)} payments matched.", "success")
            else:
                flash("✅ Payment bot test completed. No new payments found.", "info")
                
        except Exception as e:
            print(f"❌ Payment bot test error: {e}")
            flash(f"❌ Payment bot test failed: {str(e)}", "error")
        
        return redirect(url_for("unified_settings"))
    
    if request.method == "POST":
        # Check if this is a manual payment bot trigger
        if request.form.get("action") == "test_payment_bot":
            try:
                from utils import match_gmail_payments_to_passes, log_admin_action
                print("🔧 Manual payment bot trigger activated!")
                
                log_admin_action(f"Manual payment bot test by {session.get('admin', 'Unknown')}")
                result = match_gmail_payments_to_passes()
                
                if result and isinstance(result, dict):
                    flash(f"✅ Payment bot test completed. {result.get('matched', 0)} payments matched.", "success")
                else:
                    flash("✅ Payment bot test completed. No new payments found.", "info")
                    
            except Exception as e:
                print(f"❌ Payment bot test error: {e}")
                flash(f"❌ Payment bot test failed: {str(e)}", "error")
            
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
            
            # Step 2: Logo Upload
            logo_filename = None  # Track uploaded logo for response
            logo_file = request.files.get("ORG_LOGO_FILE")
            if logo_file and logo_file.filename:
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
                "GMAIL_LABEL_FOLDER_PROCESSED": REMOVED_FIELD_DEFAULTS['gmail_label_folder_processed']
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
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Return JSON response for AJAX requests
                response_data = {"success": True, "message": "All settings saved successfully!"}
                if logo_filename:
                    response_data["logo_url"] = url_for('static', filename=f'uploads/{logo_filename}')
                return jsonify(response_data)
            else:
                # Traditional form submission - use flash and redirect
                flash("✅ All settings saved successfully!", "success")
                return redirect(url_for("unified_settings"))
            
        except Exception as e:
            db.session.rollback()
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Return JSON error response for AJAX requests
                return jsonify({"success": False, "error": f"Error saving settings: {str(e)}"}), 400
            else:
                # Traditional form submission - use flash and redirect
                flash(f"❌ Error saving settings: {str(e)}", "error")
                return redirect(url_for("unified_settings"))
    
    # GET request - load all settings
    settings = {s.key: s.value for s in Setting.query.all()}
    
    return render_template("unified_settings.html", settings=settings)


# Alternative route name to match template url_for reference
@app.route("/admin/save-unified-settings", methods=["POST"])
def save_unified_settings():
    """Alternative endpoint name to match template url_for reference"""
    return unified_settings()


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
        flash("🧨 All app data erased successfully, except Admins and Settings.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error erasing data: {e}")
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
        print("📦 Generating backup:", zip_filename)

        tmp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(tmp_dir, zip_filename)

        with ZipFile(zip_path, "w") as zipf:
            zipf.write(db_path, arcname=db_filename)

        final_path = os.path.join("static", "backups", zip_filename)
        os.makedirs(os.path.dirname(final_path), exist_ok=True)

        print(f"🛠 Moving zip from {zip_path} → {final_path}")
        shutil.move(zip_path, final_path)
        print(f"✅ Backup saved to: {final_path}")

        flash(f"📦 Backup created: {zip_filename}", "success")
    except Exception as e:
        print("❌ Backup failed:", str(e))
        flash("❌ Backup failed. Check logs.", "danger")

    return redirect(url_for("setup", backup_file=zip_filename))




@app.route("/users.json")
def users_json():
    from models import User

    users = (
        db.session.query(User.name, User.email, User.phone_number)
        .distinct()
        .all()
    )

    result = [
        {"name": u[0], "email": u[1], "phone": u[2]}
        for u in users if u[0]  # ✅ Filter out empty names
    ]

    print("📦 Sending user cache JSON:", result)
    return jsonify(result)







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
            print("❌ No admin found with that email.")
        else:
            print(f"✅ Admin found: {admin.email}")
            print(f"🔐 Stored hash (type): {type(admin.password_hash)}")
            print(f"🔐 Stored hash (value): {admin.password_hash}")

            try:
                stored_hash = admin.password_hash
                if isinstance(stored_hash, bytes):
                    stored_hash = stored_hash.decode()

                if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                    print("✅ Password matched.")
                    session["admin"] = email
                    return redirect(url_for("dashboard"))
                else:
                    print("❌ Password does NOT match.")
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
        flash("❌ Passport not found!", "error")
        return redirect(url_for("dashboard"))

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
            admin_email=session.get("admin"),
            timestamp=now_utc
        )

        flash(f"✅ Passport {passport.pass_code} redeemed via QR scan!", "success")
    else:
        flash("❌ No uses left on this passport!", "error")

    return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))






@app.route("/edit-passport/<int:passport_id>", methods=["GET", "POST"])
def edit_passport(passport_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Passport, Activity

    passport = db.session.get(Passport, passport_id)
    if not passport:
        flash("❌ Passport not found.", "error")
        return redirect(url_for("dashboard2"))

    if request.method == "POST":
        passport.sold_amt = float(request.form.get("sold_amt", passport.sold_amt))
        passport.uses_remaining = int(request.form.get("uses_remaining", passport.uses_remaining))
        passport.paid = "paid_ind" in request.form
        passport.notes = request.form.get("notes", passport.notes).strip()
        
        # Handle passport type update
        passport_type_id = request.form.get("passport_type_id")
        if passport_type_id and passport_type_id != "":
            passport.passport_type_id = int(passport_type_id)
            # Update passport type name
            from models import PassportType
            passport_type = PassportType.query.get(passport.passport_type_id)
            if passport_type:
                passport.passport_type_name = passport_type.name
        else:
            passport.passport_type_id = None
            passport.passport_type_name = None

        db.session.commit()
        flash("Passport updated successfully.", "success")
        return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))

    # 🟢 FIX: fetch activities and pass to template
    activity_list = Activity.query.order_by(Activity.name).all()
    
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




@app.route("/activities")
def list_activities():
    if "admin" not in session:
        return redirect(url_for("login"))

    # Get filter parameters
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    activity_type = request.args.get("type", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    
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
    
    # Calculate statistics for each activity
    for activity in activities:
        activity.signup_count = len([p for p in activity.passports if p.paid])
        activity.total_revenue = sum(p.sold_amt for p in activity.passports if p.paid)
        activity.passport_types_count = len(activity.passport_types)
        activity.active_passports_count = len([p for p in activity.passports if p.paid and p.uses_remaining > 0])
    
    # Get unique activity types for filter dropdown
    activity_types = db.session.query(Activity.type).distinct().filter(Activity.type.isnot(None)).all()
    activity_types = [t[0] for t in activity_types if t[0]]
    
    return render_template("activities.html", 
                         activities=activities, 
                         activity_types=activity_types,
                         current_filters={
                             'q': q,
                             'status': status,
                             'type': activity_type,
                             'start_date': start_date,
                             'end_date': end_date
                         })


@app.route("/surveys")
def list_surveys():
    if "admin" not in session:
        return redirect(url_for("login"))

    # Get filter parameters
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    activity_id = request.args.get("activity", "")
    template_id = request.args.get("template", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    
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

    surveys = query.all()
    
    # Get activities and templates for filter dropdowns
    activities = Activity.query.filter_by(status='active').order_by(Activity.name).all()
    survey_templates = SurveyTemplate.query.order_by(SurveyTemplate.name).all()
    
    # Calculate KPI statistics
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
        'total_surveys': total_surveys,
        'active_surveys': active_surveys,
        'inactive_surveys': inactive_surveys,
        'total_invitations': total_invitations,
        'total_responses': completed_responses,  # Keep this for compatibility
        'completed_responses': completed_responses,
        'avg_completion_rate': avg_completion_rate
    }
    
    return render_template("surveys.html", 
                         surveys=surveys, 
                         activities=activities,
                         survey_templates=survey_templates,
                         statistics=statistics,
                         current_filters={
                             'q': q,
                             'status': status,
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
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    min_amount = request.args.get("min_amount", "")
    max_amount = request.args.get("max_amount", "")
    
    # Base query with eager loading for performance
    query = Passport.query.options(
        db.joinedload(Passport.user),
        db.joinedload(Passport.activity),
        db.joinedload(Passport.passport_type)
    ).order_by(Passport.created_dt.desc())

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
    
    # Calculate statistics
    total_passports = len(passports)
    paid_passports = len([p for p in passports if p.paid])
    unpaid_passports = total_passports - paid_passports
    active_passports = len([p for p in passports if p.uses_remaining > 0])
    total_revenue = sum(p.sold_amt for p in passports if p.paid)
    pending_revenue = sum(p.sold_amt for p in passports if not p.paid)
    
    statistics = {
        'total_passports': total_passports,
        'paid_passports': paid_passports,
        'unpaid_passports': unpaid_passports,
        'active_passports': active_passports,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue
    }
    
    return render_template("passports.html", 
                         passports=passports, 
                         activities=activities,
                         statistics=statistics,
                         current_filters={
                             'q': q,
                             'activity': activity_id,
                             'payment_status': payment_status,
                             'start_date': start_date,
                             'end_date': end_date,
                             'min_amount': min_amount,
                             'max_amount': max_amount
                         })


@app.route("/passports/bulk-action", methods=["POST"])
def passports_bulk_action():
    if "admin" not in session:
        return redirect(url_for("login"))
    
    action = request.form.get("action")
    # Handle both parameter names for backward compatibility
    passport_ids = request.form.getlist("passport_ids[]") or request.form.getlist("selected_passports")
    
    if not passport_ids:
        flash("❌ No passports selected.", "error")
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
        
        flash(f"✅ Marked {count} passports as paid.", "success")
    
    elif action == "send_reminders":
        count = 0
        for passport in passports:
            if not passport.paid:
                # Send payment reminder email
                notify_pass_event(
                    app=current_app._get_current_object(),
                    event_type="payment_late",
                    pass_data=passport,
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
        
        flash(f"📧 Sent payment reminders to {count} unpaid passports.", "success")
    
    elif action == "delete":
        count = len(passports)
        for passport in passports:
            db.session.delete(passport)
        
        db.session.commit()
        
        # Log admin action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Bulk deleted {count} passports by {session.get('admin', 'unknown')}"
        ))
        db.session.commit()
        
        flash(f"🗑️ Deleted {count} passports.", "success")
    
    else:
        flash("❌ Invalid bulk action.", "error")
    
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
    income = Income.query.get(income_id) if income_id else None

    income_categories = [
        "Ticket Sales", "Sponsorship", "Donations",
        "Vendor Fees", "Service Income", "Merchandise Sales", "Other"
    ]

    if request.method == "POST":
        if income:
            # Update existing income
            income.category = request.form.get("category")
            income.amount = request.form.get("amount", type=float)
            income.note = request.form.get("note")
            income.date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")
        else:
            # Create new income
            income = Income(
                activity_id=activity.id,
                category=request.form.get("category"),
                amount=request.form.get("amount", type=float),
                note=request.form.get("note"),
                date=datetime.strptime(request.form.get("date"), "%Y-%m-%d"),
                created_by="admin"
            )
            db.session.add(income)

        # Handle file upload
        receipt_file = request.files.get("receipt")
        if receipt_file and receipt_file.filename:
            ext = os.path.splitext(receipt_file.filename)[1]
            filename = f"income_{uuid.uuid4().hex}{ext}"
            path = os.path.join(app.static_folder, "uploads/receipts", filename)
            receipt_file.save(path)
            income.receipt_filename = filename

        db.session.commit()
        flash("Income saved.", "success")
        
        # Check if we should return to activity form
        return_to = request.args.get('return_to')
        if return_to == 'activity_form':
            return redirect(url_for("activity_form", activity_id=activity.id))
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
    expense = Expense.query.get(expense_id) if expense_id else None

    expense_categories = [
        "Cost of Goods Sold", "Staff", "Venue", "Equipment Rental",
        "Insurance", "Marketing", "Travel", "Supplies", "Other"
    ]

    if request.method == "POST":
        if expense:
            # Update
            expense.category = request.form.get("category")
            expense.amount = request.form.get("amount", type=float)
            expense.description = request.form.get("description")
            expense.date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")
        else:
            # Create new
            expense = Expense(
                activity_id=activity.id,
                category=request.form.get("category"),
                amount=request.form.get("amount", type=float),
                description=request.form.get("description"),
                date=datetime.strptime(request.form.get("date"), "%Y-%m-%d"),
                created_by="admin"
            )
            db.session.add(expense)

        # Upload receipt
        receipt_file = request.files.get("receipt")
        if receipt_file and receipt_file.filename:
            ext = os.path.splitext(receipt_file.filename)[1]
            filename = f"expense_{uuid.uuid4().hex}{ext}"
            path = os.path.join(app.static_folder, "uploads/receipts", filename)
            receipt_file.save(path)
            expense.receipt_filename = filename

        db.session.commit()
        flash("Expense saved.", "success")
        
        # Check if we should return to activity form
        return_to = request.form.get('return_to') or request.args.get('return_to')
        if return_to == 'activity_form':
            return redirect(url_for("activity_form", activity_id=activity.id))
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
    db.session.delete(income)
    db.session.commit()
    flash("Income deleted.", "success")
    
    # Check if we should return to activity form
    return_to = request.args.get('return_to')
    if return_to == 'activity_form':
        return redirect(url_for("activity_form", activity_id=activity_id))
    else:
        return redirect(url_for("activity_income", activity_id=activity_id))


@app.route("/admin/delete-expense/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    activity_id = expense.activity_id
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "success")
    
    # Check if we should return to activity form
    return_to = request.args.get('return_to')
    if return_to == 'activity_form':
        return redirect(url_for("activity_form", activity_id=activity_id))
    else:
        return redirect(url_for("activity_expenses", activity_id=activity_id))




@app.route("/admin/activity", methods=["GET", "POST"])
@app.route("/admin/activity/<int:activity_id>", methods=["GET", "POST"])
def activity_form(activity_id=None):
    activity = Activity.query.get(activity_id) if activity_id else None
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
            activity.start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
        except:
            activity.start_date = None

        try:
            activity.end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d")
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
                'type': pt.type,
                'price_per_user': pt.price_per_user,
                'sessions_included': pt.sessions_included,
                'target_revenue': pt.target_revenue,
                'payment_instructions': pt.payment_instructions or ''
            })
    else:
        passport_types = []
    
    return render_template("activity_form.html",
                           activity=activity,
                           passport_types=passport_types,
                           summary=summary)








@app.route("/delete-activity/<int:activity_id>", methods=["POST"])
def delete_activity(activity_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    activity = db.session.get(Activity, activity_id)
    if not activity:
        flash("❌ Activity not found.", "error")
        return redirect(url_for("list_activities"))

    db.session.delete(activity)
    db.session.commit()
    flash("✅ Activity deleted successfully.", "success")
    return redirect(url_for("list_activities"))







@app.route("/activity-dashboard/<int:activity_id>")
def activity_dashboard(activity_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Activity, Signup, Passport, Survey, SurveyResponse, AdminActionLog, Expense, Income
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_, func
    from datetime import datetime, timezone, timedelta

    activity = Activity.query.get(activity_id)
    if not activity:
        flash("❌ Activity not found", "error")
        return redirect(url_for("dashboard2"))

    # Get filter and search parameters from request
    passport_filter = request.args.get('passport_filter', 'all')
    signup_filter = request.args.get('signup_filter', 'all')
    q = request.args.get('q', '').strip()  # Add search parameter support

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
    if passport_filter == 'unpaid':
        passports_query = passports_query.filter_by(paid=False)
    elif passport_filter == 'paid':
        passports_query = passports_query.filter_by(paid=True)
    elif passport_filter == 'active':
        passports_query = passports_query.filter(Passport.uses_remaining > 0)
    else:  # 'all' - show unpaid OR with uses remaining
        passports_query = passports_query.filter(
            or_(
                Passport.uses_remaining > 0,
                Passport.paid == False
            )
        )
    
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

    # Use the enhanced get_kpi_stats function with activity filtering
    from utils import get_kpi_stats
    kpi_stats = get_kpi_stats(activity_id=activity_id)
    
    # Get the 7-day KPI data by default (this will be the initial view)
    current_kpi = kpi_stats.get('7d', {})
    
    # Calculate additional activity-specific metrics
    now = datetime.now(timezone.utc)
    three_days_ago = now - timedelta(days=3)
    
    # Get all passports and signups for this activity for additional calculations and counts
    all_passports = Passport.query.filter_by(activity_id=activity_id).all()
    all_signups = Signup.query.filter_by(activity_id=activity_id).all()
    
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
    
    # Activity log entries (recent activity)
    try:
        activity_logs = (
            AdminActionLog.query
            .filter(AdminActionLog.action.contains(activity.name))
            .order_by(AdminActionLog.timestamp.desc())
            .limit(10)
            .all()
        )
    except:
        activity_logs = []

    # KPI data structure for the dashboard template
    kpi_data = {
        'revenue': {
            'total': current_kpi.get('revenue', 0),
            'change_7d': current_kpi.get('revenue_change', 0),
            'trend': 'up' if current_kpi.get('revenue_change', 0) > 0 else 'down' if current_kpi.get('revenue_change', 0) < 0 else 'stable',
            'percentage': current_kpi.get('revenue_change', 0),
            'trend_data': current_kpi.get('revenue_trend', [])
        },
        'active_users': {
            'total': current_kpi.get('active_users', 0),
            'change_7d': current_kpi.get('passport_change', 0),
            'trend': 'up' if current_kpi.get('passport_change', 0) > 0 else 'down' if current_kpi.get('passport_change', 0) < 0 else 'stable',
            'percentage': current_kpi.get('passport_change', 0),
            'trend_data': current_kpi.get('active_users_trend', [])
        },
        'unpaid_passports': {
            'total': unpaid_count,
            'overdue': overdue_count,
            'trend': 'down' if overdue_count == 0 else 'up',
            'percentage': overdue_count,
            'trend_data': [unpaid_count] * 7  # Simple placeholder for now
        },
        'profit': {
            'total': profit,
            'margin': profit_margin,
            'trend': 'up' if profit > 0 else 'down' if profit < 0 else 'stable',
            'percentage': profit_margin,
            'trend_data': current_kpi.get('revenue_trend', [])  # Use revenue trend for now
        }
    }
    
    # Store the full KPI stats for JavaScript access
    kpi_data['all_periods'] = kpi_stats
    
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
        dashboard_stats=dashboard_stats,
        activity_logs=activity_logs,
        current_datetime=datetime.now()
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
            if period not in [7, 30, 90]:
                period = 7  # Default fallback
        except (ValueError, TypeError):
            period = 7
        
        # Validate activity exists and user has access
        from models import Activity
        activity = db.session.execute(
            text("SELECT id, name FROM activity WHERE id = :activity_id AND active = 1"),
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
    from utils import get_kpi_stats
    import math
    
    try:
        # Secure database query using parameterized query
        activity = db.session.execute(
            text("SELECT * FROM activity WHERE id = :activity_id AND active = 1"),
            {"activity_id": activity_id}
        ).fetchone()
        
        if not activity:
            return jsonify({
                "success": False, 
                "error": "Activity not found",
                "code": "ACTIVITY_NOT_FOUND"
            }), 404
        
        # Use the enhanced get_kpi_stats function with activity filtering
        kpi_stats = get_kpi_stats(activity_id=activity_id)
        
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
        passport_filter = escape(str(request.args.get('passport_filter', 'all'))).strip()[:20]
        signup_filter = escape(str(request.args.get('signup_filter', 'all'))).strip()[:20]
        search_query = escape(str(request.args.get('q', ''))).strip()[:100]
        
        # Validate filter values
        valid_passport_filters = ['all', 'paid', 'unpaid']
        valid_signup_filters = ['all', 'paid', 'unpaid', 'pending']
        
        if passport_filter not in valid_passport_filters:
            passport_filter = 'all'
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
            text("SELECT id, name FROM activity WHERE id = :activity_id AND active = 1"),
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
        elif passport_filter == 'paid':
            passports_query = passports_query.filter_by(paid=True)
        elif passport_filter == 'active':
            passports_query = passports_query.filter(Passport.uses_remaining > 0)
        else:  # 'all' - show unpaid OR with uses remaining
            passports_query = passports_query.filter(
                or_(
                    Passport.uses_remaining > 0,
                    Passport.paid == False
                )
            )
        
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
            'all': len([p for p in all_passports if not p.paid or p.uses_remaining > 0]),
            'unpaid': len([p for p in all_passports if not p.paid]),
            'paid': len([p for p in all_passports if p.paid]),
            'active': len([p for p in all_passports if p.uses_remaining > 0])
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
    from utils import get_kpi_stats
    import math
    
    try:
        # Get global KPI stats with error handling
        kpi_stats = get_kpi_stats()
        
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

        # ✅ Always create a new user (even if same email is reused)
        user = User(name=user_name, email=user_email, phone_number=phone_number)
        db.session.add(user)
        db.session.flush()  # Assign user.id

        # ✅ Get passport type name if passport_type_id is provided
        passport_type_name = None
        if passport_type_id:
            from models import PassportType
            passport_type = PassportType.query.get(passport_type_id)
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
            created_dt=datetime.now(timezone.utc),  # fresh datetime
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
            admin_email=session.get("admin"),
            timestamp=now_utc
        )

        flash("✅ Passport created and confirmation email sent.", "success")
        return redirect(url_for("dashboard"))

    # 👉 GET METHOD
    default_amt = get_setting("DEFAULT_PASS_AMOUNT", "50")
    default_qt = get_setting("DEFAULT_SESSION_QT", "4")
    activity_list = Activity.query.order_by(Activity.name).all()
    
    # Get activity_id from URL parameters if provided
    selected_activity_id = request.args.get('activity_id', type=int)
    
    # Load passport types for the selected activity or all activities
    from models import PassportType
    if selected_activity_id:
        passport_types = PassportType.query.filter_by(activity_id=selected_activity_id, status='active').all()
    else:
        passport_types = PassportType.query.filter_by(status='active').all()

    return render_template(
        "passport_form.html",
        passport=None,
        default_amt=default_amt,
        default_qt=default_qt,
        activity_list=activity_list,
        passport_types=passport_types,
        selected_activity_id=selected_activity_id
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
        flash("❌ Passport not found!", "error")
        return redirect(url_for("dashboard"))

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
            admin_email=session.get("admin"),
            timestamp=now_utc
        )

        flash(f"Session redeemed! {passport.uses_remaining} uses left.", "success")
    else:
        flash("❌ No uses left on this passport!", "error")

    return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))




@app.route("/mark-passport-paid/<int:passport_id>", methods=["POST"])
def mark_passport_paid(passport_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Passport, AdminActionLog
    import time
    from datetime import datetime, timezone, timedelta

    passport = db.session.get(Passport, passport_id)
    if not passport:
        flash("❌ Passport not found!", "error")
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
        admin_email=session.get("admin"),
        timestamp=now_utc
    )
    
    # SSE notifications removed for leaner performance

    flash(f" Passport {passport.pass_code} marked as paid. Email sent.", "success")
    return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))


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
        log_admin_action(
            admin_email=session.get("admin", "system"),
            action=f"Archived passport type: {passport_type.name} (ID: {passport_type_id})"
        )
        
        return jsonify({
            "success": True,
            "message": f"Passport type '{passport_type.name}' has been archived successfully."
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
            flash("❌ Missing required fields", "error")
            return redirect(url_for("activity_dashboard", activity_id=activity_id))
        
        # Verify activity exists
        activity = Activity.query.get_or_404(activity_id)
        
        # Get template from database or use hardcoded fallback
        if template_id.isdigit():
            # Numeric template ID - get from database
            template = SurveyTemplate.query.get(int(template_id))
            if not template:
                flash("❌ Invalid survey template", "error")
                return redirect(url_for("activity_dashboard", activity_id=activity_id))
        else:
            # String template ID - get hardcoded template
            template_questions = get_survey_template_questions(template_id)
            if not template_questions:
                flash("❌ Invalid survey template", "error")
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
        
        flash(f"✅ Survey '{survey_name}' created successfully!", "success")
        return redirect(url_for("activity_dashboard", activity_id=activity_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error creating survey: {str(e)}", "error")
        return redirect(url_for("activity_dashboard", activity_id=activity_id))


@app.route("/create-quick-survey", methods=["POST"])
def create_quick_survey():
    """Create a quick survey using the default Post-Activity Feedback template"""
    if "admin" not in session:
        return redirect(url_for("login"))
    
    try:
        activity_id = request.form.get("activity_id")
        survey_name = request.form.get("survey_name", "").strip()
        
        if not activity_id or not survey_name:
            flash("❌ Activity and survey name are required", "error")
            return redirect(url_for("activity_dashboard", activity_id=activity_id or 1))
        
        # Verify activity exists
        activity = Activity.query.get(activity_id)
        if not activity:
            flash("❌ Activity not found", "error")
            return redirect(url_for("dashboard"))
        
        # Get or create the default template
        default_template = create_default_survey_template()
        if not default_template:
            flash("❌ Error creating default survey template", "error")
            return redirect(url_for("activity_dashboard", activity_id=activity_id))
        
        # Generate unique survey token
        survey_token = generate_survey_token()
        
        # Create the survey
        survey = Survey(
            activity_id=activity_id,
            template_id=default_template.id,
            name=survey_name,
            description=f"Post-activity feedback survey for {activity.name}",
            survey_token=survey_token,
            status="active"
        )
        
        db.session.add(survey)
        db.session.commit()
        
        # Log the action
        log_admin_action(f"Created quick survey '{survey_name}' for activity '{activity.name}' using default template")
        
        flash(f"✅ Quick survey '{survey_name}' created successfully using default template", "success")
        return redirect(url_for("survey_results", survey_id=survey.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error creating quick survey: {str(e)}", "error")
        return redirect(url_for("activity_dashboard", activity_id=activity_id))


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
        flash(f"❌ Error loading survey: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/survey/<survey_token>/submit", methods=["POST"])
def submit_survey_response(survey_token):
    """Submit survey response"""
    try:
        survey = Survey.query.filter_by(survey_token=survey_token).first_or_404()
        
        if survey.status != "active":
            flash("❌ This survey is no longer accepting responses", "error")
            return redirect(url_for("take_survey", survey_token=survey_token))
        
        # Collect responses
        responses = {}
        template_questions = json.loads(survey.template.questions)
        
        for question in template_questions.get("questions", []):
            question_id = str(question["id"])
            response_value = request.form.get(f"question_{question_id}")
            
            if question.get("required", False) and not response_value:
                flash(f"❌ Please answer question: {question['question']}", "error")
                return redirect(url_for("take_survey", survey_token=survey_token))
            
            if response_value:
                responses[question_id] = response_value
        
        # Create survey response
        response_token = generate_response_token()
        
        # Get user ID from session or create anonymous user
        user_id = session.get("user_id")
        if not user_id:
            # For anonymous responses, try to find or create a user
            # For now, we'll use a default anonymous user ID or create one
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
            response_token=response_token,
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
        flash(f"❌ Error submitting survey: {str(e)}", "error")
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
        print(f"✅ Default survey template '{template_name}' created successfully")
        return template
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating default survey template: {str(e)}")
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
    
    # Base query
    query = SurveyTemplate.query.order_by(SurveyTemplate.created_dt.desc())
    
    # Apply search filter
    if q:
        query = query.filter(
            db.or_(
                SurveyTemplate.name.ilike(f"%{q}%"),
                SurveyTemplate.description.ilike(f"%{q}%")
            )
        )
    
    templates = query.all()
    
    # Calculate usage statistics for each template
    for template in templates:
        template.usage_count = Survey.query.filter_by(template_id=template.id).count()
        # Parse questions to get count
        try:
            questions_data = json.loads(template.questions)
            template.question_count = len(questions_data.get('questions', []))
        except:
            template.question_count = 0
    
    return render_template("survey_templates.html", 
                         templates=templates,
                         current_filters={'q': q})


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
            return redirect(url_for("edit_survey_template", template_id=template_id))
        
        template.questions = json.dumps({"questions": questions})
        
        try:
            db.session.commit()
            flash(f"Survey template '{template.name}' updated successfully", "success")
            return redirect(url_for("list_survey_templates"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating survey template", "error")
    
    # Parse questions for editing
    try:
        questions_data = json.loads(template.questions)
        template.parsed_questions = questions_data.get('questions', [])
    except:
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
            if response.responses and question_id in response.responses:
                analysis[question_id]['responses'].append(response.responses[question_id])
        
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


@app.route("/survey/<int:survey_id>/send-invitations", methods=["POST"])
def send_survey_invitations(survey_id):
    if "admin" not in session:
        return redirect(url_for("login"))
    
    survey = Survey.query.get_or_404(survey_id)
    
    # For surveys, include all participants (paid and unpaid)
    if survey.passport_type_id:
        passports = Passport.query.filter_by(
            activity_id=survey.activity_id,
            passport_type_id=survey.passport_type_id
        ).all()
    else:
        passports = Passport.query.filter_by(
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
                survey_url = url_for('take_survey', survey_token=survey.survey_token, 
                                   _external=True) + f"?token={response.response_token}"
                
                # Use template system from setup page
                subject = get_setting('SUBJECT_survey_invitation', f"{survey.name} - Your Feedback Requested")
                template_name = get_setting('THEME_survey_invitation', 'email_survey_invitation.html')
                
                context = {
                    'user_name': passport.user.name or 'Participant',
                    'activity_name': survey.activity.name,
                    'survey_name': survey.name,
                    'survey_url': survey_url,
                    'question_count': question_count,
                    'organization_name': get_setting('ORG_NAME', 'Minipass'),
                    'organization_address': get_setting('ORG_ADDRESS', ''),
                    'support_email': get_setting('SUPPORT_EMAIL', 'support@minipass.me'),
                    'title': get_setting('TITLE_survey_invitation', 'We\'d Love Your Feedback!'),
                    'intro': get_setting('INTRO_survey_invitation', 'Thank you for participating in our activity! We hope you had a great experience and would love to hear your thoughts.'),
                    'conclusion': get_setting('CONCLUSION_survey_invitation', 'Thank you for helping us create better experiences!')
                }
                
                send_email_async(
                    app=current_app._get_current_object(),
                    subject=subject,
                    to_email=passport.user.email,
                    template_name=template_name,
                    context=context
                )
                
                sent_count += 1
                
            except Exception as e:
                # Log error but continue with other invitations
                print(f"Failed to send email to {passport.user.email}: {e}")
                flash(f"Warning: Failed to send email to {passport.user.email}", "warning")
                
        elif existing_response and not existing_response.invited_dt:
            # User exists but hasn't been invited yet (maybe created manually)
            existing_response.invited_dt = datetime.now(timezone.utc)
            
            # Send email invitation
            try:
                survey_url = url_for('take_survey', survey_token=survey.survey_token, 
                                   _external=True) + f"?token={existing_response.response_token}"
                
                # Use template system from setup page
                subject = get_setting('SUBJECT_survey_invitation', f"{survey.name} - Your Feedback Requested")
                template_name = get_setting('THEME_survey_invitation', 'email_survey_invitation.html')
                
                context = {
                    'user_name': passport.user.name or 'Participant',
                    'activity_name': survey.activity.name,
                    'survey_name': survey.name,
                    'survey_url': survey_url,
                    'question_count': question_count,
                    'organization_name': get_setting('ORG_NAME', 'Minipass'),
                    'organization_address': get_setting('ORG_ADDRESS', ''),
                    'support_email': get_setting('SUPPORT_EMAIL', 'support@minipass.me'),
                    'title': get_setting('TITLE_survey_invitation', 'We\'d Love Your Feedback!'),
                    'intro': get_setting('INTRO_survey_invitation', 'Thank you for participating in our activity! We hope you had a great experience and would love to hear your thoughts.'),
                    'conclusion': get_setting('CONCLUSION_survey_invitation', 'Thank you for helping us create better experiences!')
                }
                
                send_email_async(
                    app=current_app._get_current_object(),
                    subject=subject,
                    to_email=passport.user.email,
                    template_name=template_name,
                    context=context
                )
                
                sent_count += 1
                
            except Exception as e:
                print(f"Failed to send email to {passport.user.email}: {e}")
                flash(f"Warning: Failed to send email to {passport.user.email}", "warning")
                
        else:
            already_invited += 1
    
    db.session.commit()
    
    if already_invited > 0:
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
            headers.append(f"Q{question['id']}: {question['text']}")
        
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


@app.route("/survey/<int:survey_id>/close", methods=["POST"])
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


@app.route("/survey/<int:survey_id>/reopen", methods=["POST"])
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


@app.route("/test/sse")
def test_sse_page():
    """Serve the SSE test page for admin users"""
    if "admin" not in session:
        flash("Admin access required.", "error")
        return redirect(url_for("login"))
    
    return send_from_directory("test/html", "sse_test.html")


@app.route("/test/notification-endpoints")
def test_notification_endpoints_page():
    """Serve the notification endpoints test page for admin users"""
    if "admin" not in session:
        flash("Admin access required.", "error")
        return redirect(url_for("login"))
    
    return send_from_directory("test/html", "notification_endpoints_test.html")


# New KPI Card API endpoint for standardized components
@app.route("/api/kpi-card/<card_type>")
def get_kpi_card_api(card_type):
    """API endpoint for fetching individual KPI card data using the new component"""
    if "admin" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    # Get period parameter
    period = request.args.get('period', '7d')
    
    # Validate period
    valid_periods = ['7d', '30d', '90d', 'all']
    if period not in valid_periods:
        period = '7d'
    
    # Validate card type
    valid_card_types = ['revenue', 'active_users', 'active_passports', 
                        'passports_created', 'pending_signups', 
                        'unpaid_passports', 'profit']
    
    if card_type not in valid_card_types:
        return jsonify({
            "success": False,
            "error": f"Invalid card type: {card_type}"
        }), 400
    
    try:
        from components.kpi_card import generate_kpi_card
        
        # Generate card data with the specified period
        card_data = generate_kpi_card(card_type, period=period)
        
        if card_data:
            return jsonify({
                "success": True,
                "card_data": card_data,
                "period": period
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate card data"
            }), 500
            
    except Exception as e:
        print(f"Error in KPI card API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Initialize default survey template on startup
with app.app_context():
    try:
        create_default_survey_template()
    except Exception as e:
        print(f"Warning: Could not initialize default survey template: {str(e)}")
    
    # Initialize scheduler after app setup
    try:
        initialize_background_tasks()
    except Exception as e:
        print(f"Warning: Could not initialize background tasks: {str(e)}")

@app.route("/test-payment-bot-now")
def test_payment_bot_now():
    """SIMPLE payment bot test - just visit this URL"""
    if "admin" not in session:
        return "❌ Must be logged in as admin", 401
    
    try:
        print("🔧 SIMPLE payment bot test started!")
        from utils import match_gmail_payments_to_passes
        
        result = match_gmail_payments_to_passes()
        
        if result and isinstance(result, dict):
            message = f"✅ Payment bot completed! {result.get('matched', 0)} payments matched."
        else:
            message = "✅ Payment bot completed! No new payments found."
            
        print(f"✅ Payment bot result: {message}")
        return f"<h1>{message}</h1><p><strong>Check your dashboard logs for details.</strong></p><p><a href='/admin/unified-settings'>← Back to Settings</a></p>"
        
    except Exception as e:
        error_msg = f"❌ Payment bot failed: {str(e)}"
        print(error_msg)
        return f"<h1>{error_msg}</h1><p><a href='/admin/unified-settings'>← Back to Settings</a></p>"

if __name__ == "__main__":
    port = 8890
    print(f"🚀 Running on port {port}")
    app.run(debug=True, port=port)
