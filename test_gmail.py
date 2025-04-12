import os
import imaplib
import email
from flask import Flask
from models import db
from config import Config
from utils import get_setting

# === Minimal Flask App Context ===
app = Flask(__name__)
env = os.environ.get("FLASK_ENV", "dev").lower()
db_path = os.path.join("instance", "dev_database.db" if env != "prod" else "prod_database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config.from_object(Config)
db.init_app(app)

# === Simple Email Listing Function ===
def list_all_emails():
    with app.app_context():
        user = get_setting("MAIL_USERNAME")
        pwd = get_setting("MAIL_PASSWORD")

        if not user or not pwd:
            print("❌ MAIL_USERNAME or MAIL_PASSWORD missing in settings")
            return

        print(f"📬 Connecting to Gmail as: {user}")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, pwd)
        mail.select("inbox")

        status, data = mail.search(None, "ALL")
        if status != "OK":
            print("❌ Failed to search inbox.")
            return

        print(f"📦 Found {len(data[0].split())} emails.\n")

        for idx, num in enumerate(data[0].split(), 1):
            status, msg_data = mail.fetch(num, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            from_email = email.utils.parseaddr(msg.get("From"))[1]
            subject_raw = msg["Subject"]
            subject = email.header.decode_header(subject_raw)[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode(errors="replace")

            print(f"{idx:03d}. From: {from_email}")
            print(f"     Subject: {subject}")
            print("")

        mail.logout()

# === Run ===
if __name__ == "__main__":
    list_all_emails()
