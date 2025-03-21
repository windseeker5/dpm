from app import app, db
from models import Admin
import bcrypt

def add_admin(email, password):
    """Function to add a new admin user"""
    with app.app_context():
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Create new admin
        new_admin = Admin(email=email, password_hash=hashed_password)
        db.session.add(new_admin)
        db.session.commit()

        print(f"✅ Admin created: {email}")

# Example usage
if __name__ == "__main__":
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    add_admin(email, password)
