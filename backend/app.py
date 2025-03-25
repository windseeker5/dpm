from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages, jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import bcrypt
import uuid
import qrcode
import io
import base64
from utils import send_email, send_email_async, get_setting, generate_qr_code_image, get_pass_history_data

from werkzeug.utils import secure_filename
from models import db, Admin, Pass, Redemption, Setting  
import os  # ✅ Add this import
from config import Config

from flask import current_app
import stripe




app = Flask(__name__)
app.config.from_object(Config)

# ✅ Initialize database
db.init_app(app)
migrate = Migrate(app, db)


UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# 🔐 Set your secret key (move to config or settings later)
stripe.api_key = "sk_test_51IPFwuGrhkirXbsPv1A0AXD0QUp7WQJ1EyAarZngPje3w9vPPpqpCAm8nNJj4x5dGldbHqwfYJKZzM9dWpj5sh9100W8kXUFqlY"



# ✅ Load settings only if the database is ready
with app.app_context():
    app.config["MAIL_SERVER"] = Config.get_setting(app, "MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(Config.get_setting(app, "MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = Config.get_setting(app, "MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = Config.get_setting(app, "MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = Config.get_setting(app, "MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = Config.get_setting(app, "MAIL_DEFAULT_SENDER", "")




@app.context_processor
def inject_now():
    return {'now': datetime.now()}




@app.route("/create-checkout-session/<int:pass_id>", methods=["POST"])
def create_checkout_session(pass_id):
    hockey_pass = Pass.query.get(pass_id)
    if not hockey_pass:
        return "Invalid pass", 404

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": int(hockey_pass.sold_amt * 100),
                "product_data": {
                    "name": f"Hockey Pass for {hockey_pass.user_name}",
                    "description": f"Pass ID: {hockey_pass.pass_code}",
                },
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=url_for("payment_success", pass_id=hockey_pass.id, _external=True),
        cancel_url=url_for("show_pass", pass_code=hockey_pass.pass_code, _external=True),
    )

    return redirect(session.url, code=303)



@app.route("/payment-success/<int:pass_id>")
def payment_success(pass_id):
    hockey_pass = Pass.query.get(pass_id)
    if hockey_pass:
        hockey_pass.paid_ind = True
        db.session.commit()
        flash("✅ Payment received! Thank you.", "success")
    return redirect(url_for("show_pass", pass_code=hockey_pass.pass_code))
















@app.before_request
def check_first_run():
    if request.endpoint != 'setup' and not Admin.query.first():
        return redirect(url_for('setup'))




@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        # ✅ Handle multiple admin accounts
        admin_emails = request.form.getlist("admin_email[]")
        admin_passwords = request.form.getlist("admin_password[]")

        for email, password in zip(admin_emails, admin_passwords):
            email = email.strip()
            if not email:
                continue  # Skip blank entries

            existing = Admin.query.filter_by(email=email).first()
            if existing:
                if password.strip():  # Only update password if provided
                    existing.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            else:
                if password.strip():  # Only add new if password is given
                    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
                    db.session.add(Admin(email=email, password_hash=hashed))

        # ✅ Email settings
        email_settings = {
            "MAIL_SERVER": request.form.get("mail_server", "").strip(),
            "MAIL_PORT": request.form.get("mail_port", "587").strip(),
            "MAIL_USE_TLS": "mail_use_tls" in request.form,
            "MAIL_USERNAME": request.form.get("mail_username", "").strip(),
            "MAIL_PASSWORD": request.form.get("mail_password", "").strip(),
            "MAIL_DEFAULT_SENDER": request.form.get("mail_default_sender", "").strip()
        }

        for key, value in email_settings.items():
            if key == "MAIL_PASSWORD" and not value:
                continue  # ✅ Do not overwrite password with blank
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
            else:
                db.session.add(Setting(key=key, value=str(value)))

        # ✅ App-level settings
        extra_settings = {
            "DEFAULT_PASS_AMOUNT": request.form.get("default_pass_amount", "50").strip(),
            "DEFAULT_SESSION_QT": request.form.get("default_session_qt", "4").strip(),
            "EMAIL_INFO_TEXT": request.form.get("email_info_text", "").strip(),
            "EMAIL_FOOTER_TEXT": request.form.get("email_footer_text", "").strip()
        }

        for key, value in extra_settings.items():
            existing = Setting.query.filter_by(key=key).first()
            if existing:
                existing.value = value
            else:
                db.session.add(Setting(key=key, value=value))

        # ✅ Handle logo upload
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        logo_file = request.files.get("logo")
        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            logo_file.save(logo_path)

            # Save the logo filename in settings
            existing = Setting.query.filter_by(key="LOGO_FILENAME").first()
            if existing:
                existing.value = filename
            else:
                db.session.add(Setting(key="LOGO_FILENAME", value=filename))

            flash("✅ Logo uploaded successfully!", "success")

        db.session.commit()

        # ✅ Optional debug info
        print("[SETUP] Admins configured:", admin_emails)
        print("[SETUP] Settings saved:", list(email_settings.keys()) + list(extra_settings.keys()))

        flash("✅ Setup completed successfully!", "success")
        return redirect(url_for("dashboard"))

    # GET request
    settings = {s.key: s.value for s in Setting.query.all()}
    admins = Admin.query.all()
    return render_template("setup.html", settings=settings, admins=admins)







@app.route("/")
def home():
    return "Flask app is running!"





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
        email = request.form["email"]
        password = request.form["password"]

        with app.app_context():
            admin = Admin.query.filter_by(email=email).first()

        if admin and bcrypt.checkpw(password.encode(), admin.password_hash):  # ✅ FIXED
            session["admin"] = email
            return redirect(url_for("dashboard"))

        flash("Invalid login!", "error")
        return redirect(url_for("login"))

    return render_template("login.html")






@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    # ✅ Show passes that are either ACTIVE or UNPAID
    passes = Pass.query.filter(
        (Pass.games_remaining > 0) | (Pass.paid_ind == 0)
    ).all()

    return render_template("dashboard.html", passes=passes)






@app.route("/create-pass", methods=["GET", "POST"])
def create_pass():
    if "admin" not in session:
        return redirect(url_for("login"))


    if request.method == "POST":
        user_name = request.form["user_name"]
        user_email = request.form["user_email"]
        phone_number = request.form.get("phone_number", "(581)222-3333")
        sold_amt = float(request.form.get("sold_amt", 50))
        sessions_qt = int(request.form.get("sessionsQt", 4))
        paid_ind = 1 if "paid_ind" in request.form else 0
        pass_code = str(uuid.uuid4())[:16]


        # ✅ Get current admin ID
        current_admin = Admin.query.filter_by(email=session["admin"]).first()

        new_pass = Pass(
            pass_code=pass_code,
            user_name=user_name,
            user_email=user_email,
            phone_number=phone_number,
            sold_amt=sold_amt,
            games_remaining=sessions_qt,
            paid_ind=bool(paid_ind),
            created_by=current_admin.id if current_admin else None
        )


        db.session.add(new_pass)
        db.session.commit()

        send_email_async(
            current_app._get_current_object(),
            user_email=user_email,
            subject="🎟️ Your Hockey Pass is Ready!",
            user_name=user_name,
            pass_code=pass_code,
            created_date=new_pass.pass_created_dt.strftime('%Y-%m-%d'),
            remaining_games=new_pass.games_remaining
        )

        flash("Pass created successfully! ASYNC Email sent.", "success")
        return redirect(url_for("dashboard"))

    # ✅ This part is new — it loads defaults for the form
    default_amt = get_setting("DEFAULT_PASS_AMOUNT", "50")
    default_qt = get_setting("DEFAULT_SESSION_QT", "4")

    return render_template("create_pass.html", default_amt=default_amt, default_qt=default_qt)







@app.route("/pass/<pass_code>")
def show_pass(pass_code):
    hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
    if not hockey_pass:
        return "Pass not found", 404

    qr_image_io = generate_qr_code_image(pass_code)
    qr_data = base64.b64encode(qr_image_io.read()).decode()

    history = get_pass_history_data(pass_code)
    is_admin = "admin" in session

    return render_template("pass.html", hockey_pass=hockey_pass, qr_data=qr_data, history=history, is_admin=is_admin)











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

        now = datetime.now()
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
                current_app._get_current_object(),  # Required for background context
                user_email=hockey_pass.user_email,
                subject="🏒 Game Redeemed - Pass Update",
                user_name=hockey_pass.user_name,
                pass_code=hockey_pass.pass_code,
                created_date=hockey_pass.pass_created_dt.strftime('%Y-%m-%d'),
                remaining_games=hockey_pass.games_remaining,
                special_message=special_message
            )

            flash(f"Game redeemed! {hockey_pass.games_remaining} games left. ASYNC Email sent.", "success")
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
        db.session.commit()

        # ✅ Send confirmation email
        send_email_async(
            current_app._get_current_object(),
            user_email=hockey_pass.user_email,
            subject="✅ Payment Received for Your Hockey Pass",
            user_name=hockey_pass.user_name,
            pass_code=hockey_pass.pass_code,
            created_date=hockey_pass.pass_created_dt.strftime('%Y-%m-%d'),
            remaining_games=hockey_pass.games_remaining,
            special_message="We've received your payment. Your pass is now active. Thank you!"
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




if __name__ == "__main__":
    app.run(debug=True, port=8000)  # Change 8080 to any port you want
