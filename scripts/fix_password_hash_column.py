import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

app = create_app()

with app.app_context():
    # Alter the password_hash column to support longer scrypt hashes
    try:
        # Use raw SQL to alter the column
        db.session.execute(db.text("ALTER TABLE users ALTER COLUMN password_hash TYPE VARCHAR(255)"))
        db.session.commit()
        print("Successfully updated password_hash column to VARCHAR(255)")
    except Exception as e:
        db.session.rollback()
        print(f"Error updating column: {str(e)}")
        # If column doesn't exist or other error, try to get more info
        import traceback
        traceback.print_exc()

