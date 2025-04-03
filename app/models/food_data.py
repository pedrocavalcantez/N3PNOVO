from app import db


class FoodData(db.Model):
    """Model for storing the food database information"""

    __tablename__ = "food_data"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # Food code/identifier
    name = db.Column(db.String(100), nullable=False)  # Food name
    quantity = db.Column(db.Float, nullable=False)  # Default quantity
    calories = db.Column(db.Float, nullable=False)
    proteins = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<FoodData {self.code} - {self.name}>"
