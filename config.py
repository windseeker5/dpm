import os


class Config:
    # SECRET_KEY is deliberately not set here: app.py reads it from FLASK_SECRET_KEY and
    # refuses to start without it.
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "instance", "minipass.db")

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
