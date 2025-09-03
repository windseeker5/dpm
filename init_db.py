#!/usr/bin/env python
from app import app, db
from models import Admin
import os

with app.app_context():
    # Create database tables
    db.create_all()
    
    # Check if admin exists
    if not Admin.query.first():
        # Create default admin
        from werkzeug.security import generate_password_hash
        admin = Admin(
            email='kdresdell@gmail.com',
            password_hash=generate_password_hash('admin123'),
            first_name='Test',
            last_name='Admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Created default admin: kdresdell@gmail.com / admin123")
    
    print("Database initialized successfully!")