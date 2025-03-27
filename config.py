from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Config:
    SECRET_KEY = "your_secret_key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # ✅ Auto-commit changes

    @staticmethod
    def get_setting(app, key, default=None):
        """ Fetch setting from database, but avoid querying if table does not exist """
        with app.app_context():
            from models import Setting  # ✅ Import inside function to avoid circular import
            try:
                if db.engine.dialect.has_table(db.engine, "setting"):  # ✅ Check if table exists
                    setting = Setting.query.filter_by(key=key).first()
                    return setting.value if setting else default
            except Exception:
                pass  # ✅ Ignore errors if table does not exist yet

        return default  # ✅ Use default value if settings table is unavailable
