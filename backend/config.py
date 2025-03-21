import os

class Config:
    SECRET_KEY = "your_secret_key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # ✅ Auto-commit changes




    """
    # ✅ Email Configuration (Replace with your Gmail details)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "kdresdell@gmail.com"
    MAIL_PASSWORD = "exnx kkcm giar nkwl"  # Use Google App Password (not personal password)
    MAIL_DEFAULT_SENDER = "kdresdell@gmail.com"
    """


    # ✅ Use internal corporate SMTP relay (no TLS, no login)
    MAIL_SERVER = "142.168.84.83"
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = "no-reply@dpm.com"  # Optional


