from app import app
from models import db, Income

with app.app_context():
    # Run raw SQL to add table (only if not exists)
    if not db.engine.dialect.has_table(db.engine, 'income'):
        Income.__table__.create(bind=db.engine)
        print("✅ Income table created.")
    else:
        print("ℹ️ Income table already exists.")
