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
    pass_code = db.Column(db.String(16), unique=True, nullable=False, default=lambda: str(uuid.uuid4())[:16])  # ✅ More secure pass_code
    user_name = db.Column(db.String(100), nullable=True)
    user_email = db.Column(db.String(100), nullable=True)  # ✅ Replaced user_contact
    games_remaining = db.Column(db.Integer, default=4)
    sold_amt = db.Column(db.Float, default=50.0)  # ✅ Added sold amount
    pass_created_dt = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ Added creation date
    paid_ind = db.Column(db.Boolean, default=False)  # ✅ 0 = unpaid, 1 = paid

    # ✅ Relationship to Redemption table
    redemptions = db.relationship("Redemption", backref="pass", lazy=True)




class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=False)
    date_used = db.Column(db.DateTime, default=datetime.utcnow)
    redeemed_by = db.Column(db.String(100), nullable=True)  # ✅ Allow NULL initially

 

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)