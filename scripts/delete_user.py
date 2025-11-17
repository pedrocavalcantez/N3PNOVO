import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, UserFood, Diet
from app.models.meal_template import MealTemplate

if __name__ == "__main__":
    email = "pedrohen.fc@gmail.com"

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if not user:
            print(f"User with email '{email}' not found in database.")
            sys.exit(1)

        # Delete all related records first to avoid foreign key constraint violations
        user_id = user.id

        # Count related records
        user_foods_count = UserFood.query.filter_by(user_id=user_id).count()
        diets_count = Diet.query.filter_by(user_id=user_id).count()
        meal_templates_count = MealTemplate.query.filter_by(user_id=user_id).count()

        print(f"Deleting related data for user '{user.username}':")
        print(f"  - {user_foods_count} user foods")
        print(f"  - {diets_count} diets")
        print(f"  - {meal_templates_count} meal templates")

        # Delete user foods
        UserFood.query.filter_by(user_id=user_id).delete()

        # Delete diets
        Diet.query.filter_by(user_id=user_id).delete()

        # Delete meal templates (only user-specific ones, not global/admin templates)
        MealTemplate.query.filter_by(user_id=user_id).delete()

        # Now delete the user
        db.session.delete(user)
        db.session.commit()

        print(
            f"\nUser '{user.username}' ({email}) and all related data have been successfully deleted."
        )
