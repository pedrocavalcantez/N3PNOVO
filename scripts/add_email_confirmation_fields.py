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
        # Add email_confirmed column
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN email_confirmed BOOLEAN NOT NULL DEFAULT FALSE"))
            print("Added email_confirmed column")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("email_confirmed column already exists")
            else:
                raise e
        
        # Add confirmation_token column
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN confirmation_token VARCHAR(100) UNIQUE"))
            print("Added confirmation_token column")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("confirmation_token column already exists")
            else:
                raise e
        
        # Add confirmation_token_expires column
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN confirmation_token_expires TIMESTAMP"))
            print("Added confirmation_token_expires column")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("confirmation_token_expires column already exists")
            else:
                raise e
        
        db.session.commit()
        print("\nSuccessfully added email confirmation fields to users table!")
        
        # Set existing users as confirmed (optional - you may want to keep them unconfirmed)
        db.session.execute(db.text("UPDATE users SET email_confirmed = TRUE WHERE email_confirmed IS NULL OR email_confirmed = FALSE"))
        db.session.commit()
        print("Set existing users as email confirmed")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding columns: {str(e)}")
        import traceback
        traceback.print_exc()

