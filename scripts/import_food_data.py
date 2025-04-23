import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app import create_app, db
from app.models import FoodData


def import_food_data():
    app = create_app()
    with app.app_context():
        try:
            # Read Excel file
            excel_path = os.path.join("data", "food.xlsx")
            df = pd.read_excel(excel_path)

            # Print column names to debug
            print("Available columns in Excel file:")
            print(df.columns.tolist())

            # Clear existing data
            FoodData.query.delete()

            # Import new data
            for _, row in df.iterrows():
                food = FoodData(
                    code=str(row["identificador"]),
                    name=row["alimento"],
                    quantity=float(row["Quantidade"]),
                    calories=float(row["Calorias"]),
                    proteins=float(row["Proteínas"]),
                    carbs=float(row["Carboidratos"]),
                    fats=float(row["Gorduras"]),
                )
                db.session.add(food)

            db.session.commit()
            print("Food data imported successfully!")

        except Exception as e:
            db.session.rollback()
            print(f"Error importing food data: {str(e)}")


if __name__ == "__main__":
    import_food_data()
