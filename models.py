# models.py (UPDATED)
import uuid
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime




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
    pass_created_dt = db.Column(db.DateTime, default=datetime.utcnow)
    paid_ind = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.DateTime, nullable=True)   
    activity = db.Column(db.String(100), nullable=True)   
    notes = db.Column(db.Text, nullable=True)



class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=False)
    date_used = db.Column(db.DateTime, default=datetime.utcnow)
    redeemed_by = db.Column(db.String(100), nullable=True)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)


class EbankPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    from_email = db.Column(db.String(150))  # ✅ NEW
    subject = db.Column(db.Text)
    bank_info_name = db.Column(db.String(100))
    bank_info_amt = db.Column(db.Float)
    matched_pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=True)
    matched_name = db.Column(db.String(100))
    matched_amt = db.Column(db.Float)
    name_score = db.Column(db.Integer)
    result = db.Column(db.String(50))
    mark_as_paid = db.Column(db.Boolean, default=False)  # ✅ NEW
    note = db.Column(db.Text, nullable=True)


