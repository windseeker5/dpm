# models.py (UPDATED - TIMEZONE AWARE)
import uuid
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone   
 


# ✅ Define db here (not in app.py)
db = SQLAlchemy()


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class Pass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_code = db.Column(db.String(16), unique=True, nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    sold_amt = db.Column(db.Float, default=50)
    games_remaining = db.Column(db.Integer, default=4)
    phone_number = db.Column(db.String(20), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    # pass_created_dt = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # ✅ UTC-aware

    pass_created_dt = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)  # ✅ FIXED!
    )

    paid_ind = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.DateTime, nullable=True)  # ✅ manually set with UTC
    activity = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # in models.py (Pass model)
    marked_paid_by = db.Column(db.String(120), nullable=True)

 









class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=False)
    date_used = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # ✅ UTC-aware
    redeemed_by = db.Column(db.String(100), nullable=True)


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)


class EbankPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # ✅ UTC-aware
    from_email = db.Column(db.String(150))
    subject = db.Column(db.Text)
    bank_info_name = db.Column(db.String(100))
    bank_info_amt = db.Column(db.Float)
    matched_pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=True)
    matched_name = db.Column(db.String(100))
    matched_amt = db.Column(db.Float)
    name_score = db.Column(db.Integer)
    result = db.Column(db.String(50))
    mark_as_paid = db.Column(db.Boolean, default=False)
    note = db.Column(db.Text, nullable=True)



class ReminderLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=False)
    reminder_sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    to_email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    pass_code = db.Column(db.String(16), nullable=True)
    template_name = db.Column(db.String(100), nullable=True)
    context_json = db.Column(db.Text)
    result = db.Column(db.String(50))  # SENT or FAILED
    error_message = db.Column(db.Text, nullable=True)
