#!/usr/bin/env python3
"""
Quick password reset utility for admin users
"""
import bcrypt
from app import app, db
from models import Admin

def reset_password(email, new_password):
    """Reset password for an admin user"""
    with app.app_context():
        admin = Admin.query.filter_by(email=email).first()

        if not admin:
            print(f"❌ No admin found with email: {email}")
            return False

        # Hash the new password
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        # Update the password
        admin.password_hash = hashed
        db.session.commit()

        print(f"✅ Password reset successfully for {email}")
        print(f"🔑 New password: {new_password}")

        # Verify the password works
        if bcrypt.checkpw(new_password.encode(), hashed.encode()):
            print("✅ Password verification successful!")
        else:
            print("❌ Password verification failed!")

        return True

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <email> <new_password>")
        print("Example: python reset_password.py kdresdell@gmail.com admin123")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    reset_password(email, password)
