import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Diet, FoodData, UserFood
from app.models.meal_template import MealTemplate

app = create_app()

with app.app_context():
    print("=" * 60)
    print("POSTGRESQL DATABASE CHECK")
    print("=" * 60)
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    print()

    # Check Users
    users_count = User.query.count()
    print(f"USERS: {users_count} total")
    if users_count > 0:
        users = User.query.all()
        for user in users:
            print(
                f"   - ID: {user.id} | Username: {user.username} | Email: {user.email} | Admin: {user.admin}"
            )
    print()

    # Check Diets
    diets_count = Diet.query.count()
    print(f"DIETS: {diets_count} total")
    if diets_count > 0:
        diets = Diet.query.limit(5).all()
        for diet in diets:
            date_str = diet.date.strftime("%Y-%m-%d") if diet.date else "Template"
            print(
                f"   - ID: {diet.id} | Name: {diet.name} | User ID: {diet.user_id} | Date: {date_str}"
            )
    print()

    # Check Food Data
    food_data_count = FoodData.query.count()
    print(f"FOOD DATA: {food_data_count} total")
    if food_data_count > 0:
        foods = FoodData.query.limit(5).all()
        for food in foods:
            print(
                f"   - Code: {food.code} | Name: {food.name} | Calories: {food.calories}"
            )
    print()

    # Check User Foods
    user_foods_count = UserFood.query.count()
    print(f"USER FOODS: {user_foods_count} total")
    if user_foods_count > 0:
        user_foods = UserFood.query.limit(5).all()
        for uf in user_foods:
            print(
                f"   - ID: {uf.id} | User ID: {uf.user_id} | Name: {uf.name} | Code: {uf.code}"
            )
    print()

    # Check Meal Templates
    meal_templates_count = MealTemplate.query.count()
    print(f"MEAL TEMPLATES: {meal_templates_count} total")
    if meal_templates_count > 0:
        templates = MealTemplate.query.limit(5).all()
        for template in templates:
            print(
                f"   - ID: {template.id} | Name: {template.name} | Type: {template.meal_type} | User ID: {template.user_id}"
            )
    print()

    print("=" * 60)
    print("Database connection successful!")
    print("=" * 60)
