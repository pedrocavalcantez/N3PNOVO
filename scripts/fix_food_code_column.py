import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

app = create_app()

with app.app_context():
    # Alter the code column to support longer codes
    try:
        # Use raw SQL to alter the column
        db.session.execute(db.text("ALTER TABLE food_data ALTER COLUMN code TYPE VARCHAR(255)"))
        db.session.commit()
        print("Successfully updated food_data.code column to VARCHAR(255)")
    except Exception as e:
        db.session.rollback()
        print(f"Error updating column: {str(e)}")
        # If column doesn't exist or other error, try to get more info
        import traceback
        traceback.print_exc()

