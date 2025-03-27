# test_summary.py

from flask import Flask
from models import db, Pass, Redemption
from utils import get_pass_history_summary

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # adjust if needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Replace this with a real pass_code from your database
TEST_PASS_CODE = "7070b68f-a092-4e"

with app.app_context():
    summary = get_pass_history_summary(TEST_PASS_CODE)
    print("\n=== PASS HISTORY SUMMARY ===")
    print(summary)
