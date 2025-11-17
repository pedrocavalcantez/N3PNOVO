import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import config first to set up environment
from config import Config

# Temporarily set a dummy mail config to avoid import errors
import os
os.environ.setdefault('MAIL_SERVER', 'smtp.gmail.com')
os.environ.setdefault('MAIL_PORT', '587')
os.environ.setdefault('MAIL_USE_TLS', 'true')

from app import create_app, db

app = create_app()

with app.app_context():
    try:
        # Add password_reset_token column
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(100) UNIQUE"))
            print("Added password_reset_token column")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("password_reset_token column already exists")
            else:
                raise e
        
        # Add password_reset_token_expires column
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN password_reset_token_expires TIMESTAMP"))
            print("Added password_reset_token_expires column")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("password_reset_token_expires column already exists")
            else:
                raise e
        
        db.session.commit()
        print("\nSuccessfully added password reset fields to users table!")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding columns: {str(e)}")
        import traceback
        traceback.print_exc()

