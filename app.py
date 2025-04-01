from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, flash, get_flashed_messages, jsonify

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, func, case, desc

from flask_migrate import Migrate
import bcrypt
import uuid
import qrcode
import io
import base64
from utils import send_email_async, get_setting, generate_qr_code_image, get_pass_history_data

from werkzeug.utils import secure_filename
from models import db, Admin, Pass, Redemption, Setting, EbankPayment, ReminderLog, EmailLog


import os  # ✅ Add this import
from config import Config

from flask import current_app
import stripe
import json

from apscheduler.schedulers.background import BackgroundScheduler
from utils import match_gmail_payments_to_passes, utc_to_local, send_unpaid_reminders

from datetime import datetime, timezone



import os
import socket

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





##
##  All the Scheduler JOB 🟢
##


#scheduler = BackgroundScheduler()
#scheduler.add_job(func=match_gmail_payments_to_passes, trigger="interval", hours=1)
#scheduler.start()


scheduler = BackgroundScheduler()

with app.app_context():
    if Config.get_setting(app,"ENABLE_EMAIL_PAYMENT_BOT", "False") == "True":
        print("🟢 Email Payment Bot is ENABLED. Scheduling job every 15 minutes.")

        def run_payment_bot():
            with app.app_context():
                match_gmail_payments_to_passes()

        scheduler.add_job(run_payment_bot, trigger="interval", minutes=30, id="email_payment_bot")

        scheduler.start()
    else:
        print("⚪ Email Payment Bot is DISABLED. No job scheduled.")




scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: send_unpaid_reminders(app), trigger="interval", days=1)
scheduler.start()







@app.context_processor
def inject_globals():
    return {
        'now': datetime.now(timezone.utc),
        'ORG_NAME': Config.get_setting(app,"ORG_NAME", "Ligue hockey Gagnon Image")
    }




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









@app.route("/export-epayments.csv")
def export_epayments_csv():
    if "admin" not in session:
        return redirect(url_for("login"))
    import csv
    from io import StringIO
    from flask import Response
    from models import EbankPayment

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow([
        "Timestamp", "From", "Bank Name", "Bank Amt",
        "Matched Name", "Matched Amt", "Score", "Paid", "Result", "Subject"
    ])

    for log in EbankPayment.query.order_by(EbankPayment.timestamp.desc()).all():
        writer.writerow([
            log.timestamp, log.from_email, log.bank_info_name, log.bank_info_amt,
            log.matched_name, log.matched_amt, log.name_score,
            "YES" if log.mark_as_paid else "NO", log.result, log.subject
        ])

    output = si.getvalue()
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=ebank_logs.csv"})





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







@app.route("/edit-pass/<pass_code>", methods=["GET", "POST"])
def edit_pass(pass_code):
    if "admin" not in session:
        return redirect(url_for("login"))

    hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
    if not hockey_pass:
        flash("Pass not found", "error")
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

    # Load activities
    activity_list = []
    try:
        activity_json = Config.get_setting(app,"ACTIVITY_LIST", "[]")
        activity_list = json.loads(activity_json)
    except Exception as e:
        print("❌ Failed to load activity list:", e)

    return render_template("edit_pass.html", hockey_pass=hockey_pass, activity_list=activity_list)








@app.route("/setup", methods=["GET", "POST"])
def setup():
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
            "ORG_NAME": request.form.get("org_name", "").strip(),
            "CALL_BACK_DAYS": request.form.get("call_back_days", "0").strip()
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
        logo_file = request.files.get("logo")
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
        flash("✅ Setup completed successfully!", "success")
        return redirect(url_for("dashboard"))

    # GET request — Load existing config
    settings = {s.key: s.value for s in Setting.query.all()}
    admins = Admin.query.all()
    return render_template("setup.html", settings=settings, admins=admins)








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





@app.route("/payments")
def payments():
    if "admin" not in session:
        return redirect(url_for("login"))

    return render_template(
        "log.html",
        ebank_logs=EbankPayment.query.order_by(EbankPayment.timestamp.desc()).all(),
        reminder_logs=ReminderLog.query.order_by(ReminderLog.reminder_sent_at.desc()).all(),
        email_logs=EmailLog.query.order_by(EmailLog.timestamp.desc()).all(),
        passes=Pass.query.order_by(Pass.pass_created_dt.desc()).all(),
        redemptions=Redemption.query.order_by(Redemption.date_used.desc()).all()
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




    return render_template("dashboard.html", passes=passes)




@app.route("/create-pass", methods=["GET", "POST"])
def create_pass():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # 🔐 Admin
        current_admin = Admin.query.filter_by(email=session["admin"]).first()

        # 📋 Form Data
        user_name = request.form.get("user_name", "").strip()
        user_email = request.form.get("user_email", "").strip()
        phone_number = request.form.get("phone_number", "(581)222-3333").strip()
        sold_amt = float(request.form.get("sold_amt", 50))
        sessions_qt = int(request.form.get("sessionsQt", 4))
        paid_ind = 1 if "paid_ind" in request.form else 0
        activity = request.form.get("activity", "").strip()
        pass_code = str(uuid.uuid4())[:16]
        notes = request.form.get("notes", "").strip()



        # 🎟️ Create Pass
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

        # 💾 Save to DB
        db.session.add(new_pass)
        db.session.commit()

        # 📬 Send Pass Email
        send_email_async(
            current_app._get_current_object(),  # 👈 REQUIRED!
            user_email=user_email,
            subject="LHGI 🎟️ Your Digital Pass is Ready",
            user_name=user_name,
            pass_code=pass_code,
            created_date=new_pass.pass_created_dt.strftime('%Y-%m-%d'),
            remaining_games=new_pass.games_remaining
        )

        flash("Pass created successfully! ASYNC Email sent.", "success")
        return redirect(url_for("dashboard"))

    # 📥 GET Request — Render Form with Defaults
    default_amt = Config.get_setting(app,"DEFAULT_PASS_AMOUNT", "50")
    default_qt = Config.get_setting(app,"DEFAULT_SESSION_QT", "4")

    # 🏷 Load Activities for Dropdown
    activity_list = []
    try:
        activity_json = Config.get_setting(app,"ACTIVITY_LIST", "[]")
        activity_list = json.loads(activity_json)
    except Exception as e:
        print("❌ Failed to load activity list:", e)

    return render_template(
        "create_pass.html",
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

            # ✅ Capture admin email from session and store it
            admin_email = session.get("admin", "unknown")
            redemption = Redemption(pass_id=hockey_pass.id, date_used=now, redeemed_by=admin_email)
            db.session.add(redemption)

            db.session.commit()

            # ✅ Prepare special message if the pass is now empty
            special_message = ""
            if hockey_pass.games_remaining == 0:
                special_message = "⚠️ Your pass is now empty and inactive!"

            # ✅ Send confirmation email asynchronously
            send_email_async(
                current_app._get_current_object(),  # 👈 REQUIRED!
                user_email=hockey_pass.user_email,
                subject="LHGI 🏒 Game Redeemed!",
                user_name=hockey_pass.user_name,
                pass_code=hockey_pass.pass_code,
                created_date=hockey_pass.pass_created_dt.strftime('%Y-%m-%d'),
                remaining_games=hockey_pass.games_remaining,
                special_message=special_message
            )

            flash(f"Game redeemed! {hockey_pass.games_remaining} games left.Email sent.", "success")
        else:
            flash("No games left on this pass!", "error")

    return redirect(url_for("dashboard"))



@app.route("/mark-paid/<int:pass_id>", methods=["POST"])
def mark_paid(pass_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    hockey_pass = Pass.query.get(pass_id)
    if hockey_pass:

        hockey_pass.paid_ind = True
        hockey_pass.paid_date = datetime.now(timezone.utc)

        db.session.commit()

        # ✅ Send confirmation email
        send_email_async(
            current_app._get_current_object(),  # 👈 REQUIRED!
            user_email=hockey_pass.user_email,
            subject="LHGI ✅ Payment Received",
            user_name=hockey_pass.user_name,
            pass_code=hockey_pass.pass_code,
            created_date=hockey_pass.pass_created_dt.strftime('%Y-%m-%d'),
            remaining_games=hockey_pass.games_remaining,
            special_message="We've received your payment. Your pass is now active. Thank you!",
            admin_email=session.get("admin") 
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




@app.route("/reports")
def reports():
    from sqlalchemy import extract, func
    if "admin" not in session:
        return redirect(url_for("login"))


    monthly_data = db.session.query(
        extract('year', Pass.pass_created_dt).label('year'),
        extract('month', Pass.pass_created_dt).label('month'),
        func.sum(Pass.sold_amt).label('billed'),
        func.sum(case((Pass.paid_ind == True, Pass.sold_amt), else_=0)).label('earned')
    ).group_by('year', 'month').order_by('year', 'month').all()


    chart_data = [
        {
            "label": f"{int(row.month)}/{int(row.year)}",
            "billed": float(row.billed),
            "earned": float(row.earned)
        } for row in monthly_data
    ]




    # Query: count of passes per admin per month
    creation_data = db.session.query(
        extract('year', Pass.pass_created_dt).label('year'),
        extract('month', Pass.pass_created_dt).label('month'),
        Admin.email,
        func.count(Pass.id)
    ).join(Admin, Admin.id == Pass.created_by)\
    .group_by('year', 'month', Admin.email)\
    .order_by('year', 'month').all()

    # Reorganize data into nested dict: { "Mar 2025": { "admin1@email": count, ... } }
    from collections import defaultdict

    creation_summary = defaultdict(lambda: defaultdict(int))

    for row in creation_data:
        month_str = f"{int(row.month)}/{int(row.year)}"
        creation_summary[month_str][row.email] = row[3]

    # Convert into chart format
    admin_emails = sorted({email for data in creation_summary.values() for email in data})
    creation_chart_data = {
        "labels": sorted(creation_summary.keys(), key=lambda x: (int(x.split("/")[1]), int(x.split("/")[0]))),
        "admins": admin_emails,
        "datasets": [
            {
                "label": email,
                "data": [creation_summary[month].get(email, 0) for month in sorted(creation_summary.keys())],
            } for email in admin_emails
        ]
    }


    # Redemption count per admin per month
    redemption_data = db.session.query(
        extract('year', Redemption.date_used).label('year'),
        extract('month', Redemption.date_used).label('month'),
        Redemption.redeemed_by,
        func.count(Redemption.id)
    ).group_by('year', 'month', Redemption.redeemed_by)\
    .order_by('year', 'month').all()

    # Reorganize into: { "Mar 2025": { "admin@email": count } }
    from collections import defaultdict

    redemption_summary = defaultdict(lambda: defaultdict(int))
    for row in redemption_data:
        month_str = f"{int(row.month)}/{int(row.year)}"
        redemption_summary[month_str][row.redeemed_by] = row[3]

    # Structure for chart
    redeem_admins = sorted({email for data in redemption_summary.values() for email in data})
    redemption_chart_data = {
        "labels": sorted(redemption_summary.keys(), key=lambda x: (int(x.split("/")[1]), int(x.split("/")[0]))),
        "admins": redeem_admins,
        "datasets": [
            {
                "label": email,
                "data": [redemption_summary[month].get(email, 0) for month in sorted(redemption_summary.keys())],
            } for email in redeem_admins
        ]
    }



    return render_template(
        "reports.html",
        chart_data=chart_data,
        creation_chart_data=creation_chart_data,
        redemption_chart_data=redemption_chart_data
    )






if __name__ == "__main__":
    app.run(debug=True, port=8889)

