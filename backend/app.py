from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import bcrypt
import config
import uuid
import qrcode
import io
import base64
from utils import send_email



# ✅ Import models after initializing Flask
from models import db, Admin, Pass, Redemption  

app = Flask(__name__)
app.config.from_object("config.Config")

# ✅ Initialize db and Flask-Migrate in correct order
db.init_app(app)
migrate = Migrate(app, db)  # ✅ Initialize Flask-Migrate AFTER db.init_app(app)



# ✅ Ensure database is created within an app context ONLY if needed
with app.app_context():
    try:
        db.create_all()  # Only needed for the first-time setup
    except Exception as e:
        print(f"Database error: {e}")



@app.route("/")
def home():
    return "Flask app is running!"



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        with app.app_context():  # ✅ Ensure query runs inside app context
            admin = Admin.query.filter_by(email=email).first()

        if admin and bcrypt.checkpw(password.encode(), admin.password_hash.encode()):
            session["admin"] = email
            return redirect(url_for("dashboard"))

        return "Invalid login", 401
    return render_template("login.html")





@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    # ✅ Filter passes with games_remaining > 0
    passes = Pass.query.filter(Pass.games_remaining > 0).all()

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
        send_email(
            user_email=user_email,
            subject="🎟️ Your Hockey Pass is Ready!",
            user_name=user_name,
            pass_code=pass_code,
            created_date=new_pass.pass_created_dt.strftime('%Y-%m-%d'),
            remaining_games=4
        )

        flash("✅ Pass created successfully, and email sent!", "success")
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
