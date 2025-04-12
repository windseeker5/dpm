# 📦 Core Python Modules
import os
import io
import uuid
import json
import base64
import socket
import hashlib
import bcrypt
import stripe
import qrcode
from datetime import datetime, timezone

# 🌐 Flask Core
from flask import (
    Flask, render_template, render_template_string, request, redirect,
    url_for, session, flash, get_flashed_messages, jsonify, current_app
)

# 🛠 Flask Extensions
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 🧱 SQLAlchemy Extras
from sqlalchemy import extract, func, case, desc

# 📎 File Handling
from werkzeug.utils import secure_filename

# 🧠 Models
from models import db, Admin, Pass, Redemption, Setting, EbankPayment, ReminderLog, EmailLog

# ⚙️ Config
from config import Config

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
    get_kpi_stats
)



# 🧠 Data Tools
from collections import defaultdict


from chatbot.routes_chatbot import chat_bp







hostname = socket.gethostname()
is_dev = hostname == "archlinux" or "local" in hostname

db_filename = "dev_database.db" if is_dev else "prod_database.db"
db_path = os.path.join("instance", db_filename)

print(f"📦 Using {'DEV' if is_dev else 'PROD'} database → {db_path}")


 

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config.from_object(Config)

# ✅ Initialize database
db.init_app(app)

migrate = Migrate(app, db)


if not os.path.exists(db_path):
    print(f"❌ {db_path} is missing!")
    exit(1)




print(f"📂 Connected DB path: {app.config['SQLALCHEMY_DATABASE_URI']}")




UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ✅ Load settings only if the database is ready
with app.app_context():
    app.config["MAIL_SERVER"] = Config.get_setting(app, "MAIL_SERVER", "smtp.gmail.com")
    #app.config["MAIL_PORT"] = int(Config.get_setting(app, "MAIL_PORT", 587))
    app.config["MAIL_PORT"] = int(Config.get_setting(app, "MAIL_PORT", "587") or 587)
    app.config["MAIL_USE_TLS"] = Config.get_setting(app, "MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = Config.get_setting(app, "MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = Config.get_setting(app, "MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = Config.get_setting(app, "MAIL_DEFAULT_SENDER", "")




app.register_blueprint(chat_bp)             # 👈 Register it




##
##  All the Scheduler JOB 🟢
##


#scheduler = BackgroundScheduler()
#scheduler.add_job(func=match_gmail_payments_to_passes, trigger="interval", hours=1)
#scheduler.start()


scheduler = BackgroundScheduler()
from utils import get_setting  # ✅ at the top of app.py

with app.app_context():
    if get_setting("ENABLE_EMAIL_PAYMENT_BOT", "False") == "True":
        print("🟢 Email Payment Bot is ENABLED. Scheduling job every 30 minutes.")

        def run_payment_bot():
            with app.app_context():
                match_gmail_payments_to_passes()

        scheduler.add_job(run_payment_bot, trigger="interval", minutes=30, id="email_payment_bot")
        scheduler.start()
    else:
        print("⚪ Email Payment Bot is DISABLED. No job scheduled.")




scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: send_unpaid_reminders(app), trigger="interval", days=1)
#scheduler.add_job(func=lambda: send_unpaid_reminders(app), trigger="interval", days=0.001)

scheduler.start()




@app.context_processor
def inject_globals():
    return {
        'now': datetime.now(timezone.utc),
        'ORG_NAME': get_setting("ORG_NAME", "Ligue hockey Gagnon Image")
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








@app.route("/dev-reset-admin")
def dev_reset_admin():
    # Only run this in dev mode! You can restrict it further if needed
    email = "kdresdell@gmail.com"
    new_password = "admin123"
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

    with app.app_context():
        admin = Admin.query.filter_by(email=email).first()
        if admin:
            admin.password_hash = hashed.decode()
            db.session.commit()
            return f"✅ Reset password for {email} to <strong>{new_password}</strong>"
        else:
            return f"❌ Admin with email {email} not found."




from flask import flash

@app.route("/test-alert")
def test_alert():
    flash("🎉 Flash system works!", "success")
    return redirect(url_for("dashboard"))


@app.route("/test-reminders")
def test_reminders():
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import send_unpaid_reminders
    send_unpaid_reminders(app)
    flash("✅ Test run of send_unpaid_reminders() executed. Check logs and emails.", "success")
    return redirect(url_for("dashboard"))





@app.route("/test-email-match")
def test_email_match():
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import match_gmail_payments_to_passes
    match_gmail_payments_to_passes()
    flash("✅ Gmail payment match test executed. Check logs and DB.", "success")
    return redirect(url_for("dashboard"))






@app.route("/setup", methods=["GET", "POST"])
def setup():

    ##
    ##  POST REQUEST 
    ##

    if request.method == "POST":
        # 🔐 Step 1: Admin accounts
        admin_emails = request.form.getlist("admin_email[]")
        admin_passwords = request.form.getlist("admin_password[]")

        for email, password in zip(admin_emails, admin_passwords):
            email = email.strip()
            password = password.strip()
            if not email:
                continue

            existing = Admin.query.filter_by(email=email).first()
            if existing:
                if password and password != "********":
                    # ✅ Only update if real password provided
                    existing.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            else:
                if password and password != "********":
                    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    db.session.add(Admin(email=email, password_hash=hashed))

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
            #"MAIL_PASSWORD": request.form.get("mail_password", "").strip(),
            "MAIL_PASSWORD": request.form.get("mail_password_raw", "").strip(),

            "MAIL_DEFAULT_SENDER": request.form.get("mail_default_sender", "").strip()
        }

        #for key, value in email_settings.items():
        #    if key == "MAIL_PASSWORD" and not value:
        #        continue  # 🚫 Don't overwrite password with blank

        for key, value in email_settings.items():
            if key == "MAIL_PASSWORD" and (not value or value == "********"):
                continue  # 🚫 Don't overwrite with blank or fake password


            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
            else:
                db.session.add(Setting(key=key, value=str(value)))

        # ⚙️ Step 4: App-level settings

        extra_settings = {
            "DEFAULT_PASS_AMOUNT": request.form.get("default_pass_amount", "50").strip(),
            "DEFAULT_SESSION_QT": request.form.get("default_session_qt", "4").strip(),
            "EMAIL_INFO_TEXT": request.form.get("email_info_text", "").strip(),
            "EMAIL_FOOTER_TEXT": request.form.get("email_footer_text", "").strip(),
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
            "GMAIL_LABEL_FOLDER_PROCESSED": request.form.get("gmail_label_folder_processed", "InteractProcessed").strip()
        }

        for key, value in bot_settings.items():
            existing = Setting.query.filter_by(key=key).first()
            if existing:
                existing.value = str(value)
            else:
                db.session.add(Setting(key=key, value=str(value)))

        # 🏷 Step 6: Activity Tags
        activity_raw = request.form.get("activities", "").strip()
        try:
            if activity_raw.startswith("["):
                tag_objects = json.loads(activity_raw)
                activity_list = [
                    tag["value"].strip() if isinstance(tag, dict) and "value" in tag else str(tag).strip()
                    for tag in tag_objects if str(tag).strip()
                ]
            else:
                activity_list = [a.strip() for a in activity_raw.split(",") if a.strip()]

            setting = Setting.query.filter_by(key="ACTIVITY_LIST").first()
            if setting:
                setting.value = json.dumps(activity_list)
            else:
                db.session.add(Setting(key="ACTIVITY_LIST", value=json.dumps(activity_list)))
        except Exception as e:
            print("❌ Failed to parse/save activity list:", e)


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



        # ✅ Finalize changes
        db.session.commit()
        print("[SETUP] Admins configured:", admin_emails)
        print("[SETUP] Settings saved:", list(email_settings.keys()) + list(extra_settings.keys()))


        #flash("✅ Setup completed successfully!", "success")
        #return redirect(url_for("dashboard"))

        flash("✅ Setup completed successfully!", "success")
        return redirect(url_for("setup"))




    ##
    ##  GET request — Load existing config
    ##

    settings = {s.key: s.value for s in Setting.query.all()}
    admins = Admin.query.all()
    backup_file = request.args.get("backup_file")  # 👈 required for link display

    backup_dir = os.path.join("static", "backups")
    backup_files = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".zip")],
        reverse=True
    ) if os.path.exists(backup_dir) else []


    print("📥 Received backup_file from args:", backup_file)
    print("🗂️ Available backups in static/backups/:", os.listdir("static/backups"))

    return render_template(
        "setup.html",
        settings=settings,
        admins=admins,
        backup_file=backup_file,
        backup_files=backup_files
    )




@app.route("/erase-app-data", methods=["POST"])
def erase_app_data():
    if "admin" not in session:
        return redirect(url_for("login"))

    try:
        db.session.query(EbankPayment).delete()
        db.session.query(EmailLog).delete()
        db.session.query(Redemption).delete()
        db.session.query(ReminderLog).delete()
        db.session.query(Pass).delete()

        db.session.commit()
        flash("🧨 All app data erased successfully (passes, redemptions, emails, payments, reminders).", "success")
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
        env = os.environ.get("FLASK_ENV", "dev").lower()
        db_filename = "dev_database.db" if env != "prod" else "prod_database.db"
        db_path = os.path.join("instance", db_filename)

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



        print("✅ Backup saved to:", final_path)
        flash(f"📦 Backup created: {zip_filename}", "success")
    except Exception as e:
        print("❌ Backup failed:", str(e))
        flash("❌ Backup failed. Check logs.", "danger")

    return redirect(url_for("setup", backup_file=zip_filename))






@app.route("/")
def home():
    return redirect(url_for("login"))




@app.route("/users.json")
def users_json():
    users = db.session.query(Pass.user_name, Pass.user_email, Pass.phone_number).distinct().all()

    result = [
        {"name": u[0], "email": u[1], "phone": u[2]}
        for u in users if u[0]  # Filter out empty names
    ]

    print("📦 Sending user cache JSON:", result)  # Debug print in terminal
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

    return render_template("login.html")





@app.route("/reporting")
def reporting():
    from sqlalchemy import func
    from collections import defaultdict

    if "admin" not in session:
        return redirect(url_for("login"))

    # === SEARCH PARAMS ===
    search_epay = request.args.get("search_epay", "").strip().lower()
    search_pass = request.args.get("search_pass", "").strip().lower()
    search_email = request.args.get("search_email", "").strip().lower()

    # === PAGINATION ===
    per_page = 10
    page_epay = int(request.args.get("page_epay", 1))
    page_pass = int(request.args.get("page_pass", 1))
    page_email = int(request.args.get("page_email", 1))

    # === 1. Matched E-Bank Payments ===
    epay_query = EbankPayment.query.filter(EbankPayment.mark_as_paid == True)
    if search_epay:
        epay_query = epay_query.filter(
            func.lower(EbankPayment.subject).like(f"%{search_epay}%") |
            func.lower(EbankPayment.bank_info_name).like(f"%{search_epay}%") |
            func.lower(EbankPayment.from_email).like(f"%{search_epay}%")
        )
    pagination_epay = epay_query.order_by(EbankPayment.timestamp.desc()).paginate(page=page_epay, per_page=per_page, error_out=False)

    # === 2. Pass Log ===
    pass_query = Pass.query
    if search_pass:
        pass_query = pass_query.filter(
            func.lower(Pass.user_name).like(f"%{search_pass}%") |
            func.lower(Pass.user_email).like(f"%{search_pass}%")
        )
    pagination_pass = pass_query.order_by(Pass.pass_created_dt.desc()).paginate(page=page_pass, per_page=per_page, error_out=False)

    # === 3. Email Log ===
    email_query = EmailLog.query
    if search_email:
        email_query = email_query.filter(
            func.lower(EmailLog.to_email).like(f"%{search_email}%") |
            func.lower(EmailLog.subject).like(f"%{search_email}%")
        )
    pagination_email = email_query.order_by(EmailLog.timestamp.desc()).paginate(page=page_email, per_page=per_page, error_out=False)

    # === 4. NEW CHART: SOLD AMOUNT per ACTIVITY per DATE ===
    raw_data = db.session.query(
        Pass.activity,
        func.date(Pass.pass_created_dt),  # extracts just YYYY-MM-DD
        func.sum(Pass.sold_amt)
    ).group_by(Pass.activity, func.date(Pass.pass_created_dt))\
     .order_by(func.date(Pass.pass_created_dt)).all()

    # Structure chart data
    activity_grouped = defaultdict(lambda: defaultdict(float))
    all_dates = set()

    for activity, date_str, total in raw_data:
        activity_grouped[activity][str(date_str)] += float(total or 0)
        all_dates.add(str(date_str))

    sorted_dates = sorted(all_dates)
    activity_chart_data = {
        "labels": sorted_dates,
        "datasets": [
            {
                "label": activity,
                "data": [activity_grouped[activity].get(date, 0) for date in sorted_dates]
            } for activity in activity_grouped
        ]
    }

    return render_template(
        "logs.html",
        ebank_logs=pagination_epay.items,
        pagination_epay=pagination_epay,

        passes=pagination_pass.items,
        pagination_pass=pagination_pass,

        email_logs=pagination_email.items,
        pagination_email=pagination_email,

        search_epay=search_epay,
        search_pass=search_pass,
        search_email=search_email,

        activity_chart_data=activity_chart_data,

        no_wrapper=True
    )




@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    # ✅ Show passes that are either ACTIVE or UNPAID
    #passes = Pass.query.filter(
    #    (Pass.games_remaining > 0) | (Pass.paid_ind == 0)
    #).all()

    passes = Pass.query.filter(
        (Pass.games_remaining > 0) | (Pass.paid_ind == 0)
    ).order_by(desc(Pass.pass_created_dt)).all()



    kpi_data = get_kpi_stats()
    return render_template("dashboard.html", passes=passes, kpi_data=kpi_data)





 



@app.route("/create-pass", methods=["GET", "POST"])
def create_pass():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        current_admin = Admin.query.filter_by(email=session["admin"]).first()

        user_name = request.form.get("user_name", "").strip()
        user_email = request.form.get("user_email", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        sold_amt = float(request.form.get("sold_amt", 50))
        sessions_qt = int(request.form.get("sessionsQt") or request.form.get("games_remaining") or 4)
        paid_ind = 1 if "paid_ind" in request.form else 0
        activity = request.form.get("activity", "").strip()
        pass_code = str(uuid.uuid4())[:16]
        notes = request.form.get("notes", "").strip()

        new_pass = Pass(
            pass_code=pass_code,
            user_name=user_name,
            user_email=user_email,
            phone_number=phone_number,
            sold_amt=sold_amt,
            games_remaining=sessions_qt,
            paid_ind=bool(paid_ind),
            created_by=current_admin.id if current_admin else None,
            activity=activity,
            notes=notes
        )

        db.session.add(new_pass)
        db.session.commit()

        # ✅ Pass the full datetime object
        send_email_async(
            current_app._get_current_object(),
            user_email=user_email,
            subject="LHGI 🎟️ Votre Passe électronique est prête",
            user_name=user_name,
            pass_code=pass_code,
            created_date=new_pass.pass_created_dt,  # ⏱ not a string
            remaining_games=new_pass.games_remaining
        )

        flash("✅ Pass created and email sent.", "success")
        return redirect(url_for("dashboard"))

    default_amt = get_setting("DEFAULT_PASS_AMOUNT", "50")
    default_qt = get_setting("DEFAULT_SESSION_QT", "4")

    try:
        activity_list = json.loads(get_setting("ACTIVITY_LIST", "[]"))
    except:
        activity_list = []

    return render_template(
        "pass_form.html",
        hockey_pass=None,
        default_amt=default_amt,
        default_qt=default_qt,
        activity_list=activity_list
    )

 





@app.route("/pass/<pass_code>")
def show_pass(pass_code):
    hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
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

    # ✅ Render payment instructions with pass context
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



@app.route("/edit-pass/<pass_code>", methods=["GET", "POST"])
def edit_pass(pass_code):
    if "admin" not in session:
        return redirect(url_for("login"))

    hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
    if not hockey_pass:
        flash("❌ Pass not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        hockey_pass.user_name = request.form.get("user_name", "").strip()
        hockey_pass.user_email = request.form.get("user_email", "").strip()
        hockey_pass.phone_number = request.form.get("phone_number", "").strip()
        hockey_pass.sold_amt = float(request.form.get("sold_amt", 50))
        hockey_pass.games_remaining = int(request.form.get("games_remaining", 0))
        hockey_pass.activity = request.form.get("activity", "").strip()
        hockey_pass.notes = request.form.get("notes", "").strip()

        db.session.commit()
        flash("✅ Pass updated successfully!", "success")
        return redirect(url_for("show_pass", pass_code=pass_code))

    try:
        activity_list = json.loads(get_setting("ACTIVITY_LIST", "[]"))
    except:
        activity_list = []

    return render_template(
        "pass_form.html",
        hockey_pass=hockey_pass,
        activity_list=activity_list,
        default_amt=hockey_pass.sold_amt,
        default_qt=hockey_pass.games_remaining
    )








# Store recent redemptions to prevent duplicate scans
recent_redemptions = {}


@app.route("/redeem/<pass_code>", methods=["GET", "POST"])
def redeem_pass(pass_code):
    get_flashed_messages()  # Clear flash queue

    with app.app_context():
        hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()

        if not hockey_pass:
            flash("❌ Pass not found!", "error")
            return redirect(url_for("dashboard"))

        now = datetime.now(timezone.utc)

        if pass_code in recent_redemptions and (now - recent_redemptions[pass_code]).seconds < 5:
            flash("⚠️ This pass was already redeemed. Please wait before scanning again.", "warning")
            return redirect(url_for("dashboard"))

        if hockey_pass.games_remaining > 0:
            hockey_pass.games_remaining -= 1
            db.session.add(hockey_pass)

            admin_email = session.get("admin", "unknown")
            redemption = Redemption(pass_id=hockey_pass.id, date_used=now, redeemed_by=admin_email)
            db.session.add(redemption)
            db.session.commit()

            recent_redemptions[pass_code] = now

            special_message = ""
            if hockey_pass.games_remaining == 0:
                special_message = "⚠️ Your pass is now empty and inactive!"

            send_email_async(
                current_app._get_current_object(),
                user_email=hockey_pass.user_email,
                subject="LHGI 🏒 Activité confirmée!",
                user_name=hockey_pass.user_name,
                pass_code=hockey_pass.pass_code,
                created_date=now,
                remaining_games=hockey_pass.games_remaining,
                special_message=special_message
            )

            flash(f"Game redeemed! {hockey_pass.games_remaining} games left. Email sent.", "success")
        else:
            flash("No games left on this pass!", "error")

    return redirect(url_for("dashboard"))





@app.route("/mark-paid/<int:pass_id>", methods=["POST"])
def mark_paid(pass_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    hockey_pass = Pass.query.get(pass_id)
    if hockey_pass:
        paid_now = datetime.now(timezone.utc)
        hockey_pass.paid_ind = True
        hockey_pass.paid_date = paid_now
        hockey_pass.marked_paid_by = session.get("admin", "unknown")
        db.session.commit()

        # ✅ Pass full datetime
        send_email_async(
            current_app._get_current_object(),
            user_email=hockey_pass.user_email,
            subject="LHGI ✅ Paiement Confirmé",
            user_name=hockey_pass.user_name,
            pass_code=hockey_pass.pass_code,
            created_date=paid_now,
            remaining_games=hockey_pass.games_remaining,
            special_message="We've received your payment. Your pass is now active. Thank you!",
            admin_email=hockey_pass.marked_paid_by
        )

        flash(f"Pass {hockey_pass.id} marked as paid. Email sent.", "success")
    else:
        flash("Pass not found!", "error")

    return redirect(url_for("dashboard"))



 





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

    all_logs = []
    from datetime import timedelta

    offset_step = timedelta(microseconds=1)

    # 1. Pass Created Logs
    created_passes = Pass.query.all()
    for p in created_passes:
        admin = db.session.get(Admin, p.created_by) if p.created_by else None
        all_logs.append({
            "timestamp": p.pass_created_dt + (offset_step * 1),
            "type": "Pass Created",
            "details": f"Created for {p.user_name} by {admin.email if admin else 'Unknown'}"
        })

    # 2. Redemptions
    redemptions = Redemption.query.all()
    for r in redemptions:
        p = db.session.get(Pass, r.pass_id)
        if p:
            all_logs.append({
                "timestamp": r.date_used + (offset_step * 3),
                "type": "Pass Redeemed",
                "details": f"{p.user_name} used 1 activity ({p.activity}) by {r.redeemed_by or 'Unknown'}"
            })

    # 3. Matched Payments
    matched_payments = EbankPayment.query.filter_by(mark_as_paid=True).all()
    for pay in matched_payments:
        p = db.session.get(Pass, pay.matched_pass_id)
        all_logs.append({
            "timestamp": pay.timestamp + (offset_step * 2),
            "type": "Payment Matched",
            "details": f"${pay.bank_info_amt:.2f} matched to {pay.matched_name} ({p.activity if p else 'N/A'})"
        })

    # 4. Manual Paid (Paid with no Ebank match)
    manually_marked_paid = Pass.query.filter(
        Pass.paid_ind == True,
        Pass.paid_date.isnot(None)
    ).all()
    paid_ids = {p.matched_pass_id for p in matched_payments if p.matched_pass_id}
    for p in manually_marked_paid:
        if p.id not in paid_ids:
            admin_email = p.marked_paid_by or "Unknown"
            all_logs.append({
                "timestamp": p.paid_date + (offset_step * 4),
                "type": "Marked Paid",
                "details": f"{p.user_name} marked paid by {admin_email} ({p.activity})"
            })

    # 5. Emails Sent (offset based on subject meaning)
    email_logs = EmailLog.query.all()
    for e in email_logs:
        p = Pass.query.filter_by(pass_code=e.pass_code).first()

        if "Paiement Confirmé" in e.subject:
            offset = 5  # after Marked Paid
        elif "Activité confirmée" in e.subject:
            offset = 4  # after Redemption
        elif "est prête" in e.subject:
            offset = 2  # after Creation
        else:
            offset = 3  # fallback

        all_logs.append({
            "timestamp": e.timestamp + (offset_step * offset),
            "type": "Email Sent",
            "details": f"To {e.to_email} — \"{e.subject}\" ({p.activity if p else 'N/A'})"
        })

    # ✅ Sort by timestamp DESCENDING (latest first)
    all_logs.sort(key=lambda x: x["timestamp"], reverse=True)

    return render_template("activity_log.html", logs=all_logs)





@app.template_filter("utc_to_local")
def jinja_utc_to_local_filter(dt):
    from utils import utc_to_local
    return utc_to_local(dt)


 

if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "dev").lower()
    port = 8889 if env == "prod" else 8890
    print(f"🚀 Running on port {port} (env={env})")
    app.run(debug=(env != "prod"), port=port)
