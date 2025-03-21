from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import bcrypt
import uuid
import qrcode
import io
import base64
from utils import send_email
 
from werkzeug.utils import secure_filename
from models import db, Admin, Pass, Redemption, Setting  

import os  # ✅ Add this import

from config import Config




app = Flask(__name__)
app.config.from_object(Config)

# ✅ Initialize database
db.init_app(app)
migrate = Migrate(app, db)


UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER




# ✅ Load settings only if the database is ready
with app.app_context():
    app.config["MAIL_SERVER"] = Config.get_setting(app, "MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(Config.get_setting(app, "MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = Config.get_setting(app, "MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = Config.get_setting(app, "MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = Config.get_setting(app, "MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = Config.get_setting(app, "MAIL_DEFAULT_SENDER", "")






"""
# ✅ Ensure database is created within an app context ONLY if needed
with app.app_context():
    try:
        db.create_all()  # Only needed for the first-time setup
    except Exception as e:
        print(f"Database error: {e}")

"""




@app.before_request
def check_first_run():
    if request.endpoint != 'setup' and not Admin.query.first():
        return redirect(url_for('setup'))





@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        # Get admin details
        admin_email = request.form["admin_email"]
        admin_password = request.form["admin_password"]
        hashed_password = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt())

        # ✅ Check if admin already exists
        existing_admin = Admin.query.filter_by(email=admin_email).first()
        if not existing_admin:
            new_admin = Admin(email=admin_email, password_hash=hashed_password)
            db.session.add(new_admin)

        # ✅ Get email settings from form
        email_settings = {
            "MAIL_SERVER": request.form["mail_server"],
            "MAIL_PORT": request.form["mail_port"],
            "MAIL_USE_TLS": "mail_use_tls" in request.form,
            "MAIL_USERNAME": request.form["mail_username"],
            "MAIL_PASSWORD": request.form["mail_password"],
            "MAIL_DEFAULT_SENDER": request.form["mail_default_sender"]
        }

        # ✅ Save settings in the Setting table
        for key, value in email_settings.items():
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)  # ✅ Update existing setting
            else:
                db.session.add(Setting(key=key, value=str(value)))  # ✅ Insert new setting

        # ✅ Ensure Upload Folder Exists
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        # ✅ Handle logo upload
        if "logo" in request.files:
            logo_file = request.files["logo"]
            if logo_file and logo_file.filename:
                filename = secure_filename(logo_file.filename)
                logo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                logo_file.save(logo_path)
                flash("✅ Logo uploaded successfully!", "success")

        db.session.commit()  # ✅ Save all changes
        flash("✅ Setup completed successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("setup.html")









@app.route("/")
def home():
    return "Flask app is running!"



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
        sold_amt = float(request.form.get("sold_amt", 50))
        paid_ind = 1 if "paid_ind" in request.form else 0
        pass_code = str(uuid.uuid4())[:16]

        new_pass = Pass(
            pass_code=pass_code,
            user_name=user_name,
            user_email=user_email,
            sold_amt=sold_amt,
            paid_ind=bool(paid_ind)
        )

        db.session.add(new_pass)
        db.session.commit()

        # ✅ Send confirmation email with QR code
        email_sent = send_email(
            user_email=user_email,
            subject="🎟️ Your Hockey Pass is Ready!",
            user_name=user_name,
            pass_code=pass_code,
            created_date=new_pass.pass_created_dt.strftime('%Y-%m-%d'),
            remaining_games=4
        )

        if email_sent:
            flash("✅ Pass created successfully, and email sent!", "success")
        else:
            flash("⚠️ Pass created, but email failed to send. Please check SMTP settings.", "error")

        return redirect(url_for("dashboard"))

    return render_template("create_pass.html")








@app.route("/pass/<pass_code>")
def show_pass(pass_code):
    with app.app_context():
        hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()

    if not hockey_pass:
        return "Pass not found", 404

    # Generate QR code
    qr = qrcode.make(pass_code)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_data = base64.b64encode(buffer.getvalue()).decode()

    return render_template("pass.html", hockey_pass=hockey_pass, qr_data=qr_data)






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

            # ✅ Send email with updated games remaining
            send_email(
                user_email=hockey_pass.user_email,
                subject="🏒 Game Redeemed - Pass Update",
                user_name=hockey_pass.user_name,
                pass_code=pass_code,
                created_date=hockey_pass.pass_created_dt.strftime('%Y-%m-%d'),
                remaining_games=hockey_pass.games_remaining,
                special_message=special_message
            )


            flash(f"Game redeemed! {hockey_pass.games_remaining} games left.", "success")
        else:
            flash("❌ No games left on this pass!", "error")


    return redirect(url_for("dashboard"))





@app.route("/mark-paid/<int:pass_id>", methods=["POST"])
def mark_paid(pass_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    hockey_pass = Pass.query.get(pass_id)
    if hockey_pass:
        hockey_pass.paid_ind = True
        db.session.commit()
        flash(f"Pass {hockey_pass.id} marked as paid.", "success")

    return redirect(url_for("dashboard"))







@app.route("/scan-qr")
def scan_qr():
    return render_template("scan_qr.html")




@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
