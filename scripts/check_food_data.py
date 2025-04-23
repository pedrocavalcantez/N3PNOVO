from app import create_app, db
from app.models import FoodData

app = create_app()


def check_food_data():
    with app.app_context():
        count = FoodData.query.count()
        print(f"Number of food records in database: {count}")

        # Print first few records as sample
        print("\nSample records:")
        for food in FoodData.query.limit(5).all():
            print(f"Code: {food.code}, Name: {food.name}, Quantity: {food.quantity}g")


if __name__ == "__main__":
    check_food_data()
