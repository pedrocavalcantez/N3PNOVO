from datetime import datetime
from app import db
from app.constants import MEAL_TYPES, DEFAULT_PORTION_SIZE
from sqlalchemy import func


class Food(db.Model):
    """Food model for storing food entries"""

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)  # Food code from Excel file
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=DEFAULT_PORTION_SIZE)
    calories = db.Column(db.Float, nullable=False)
    proteins = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    meal_type = db.Column(db.String(20), nullable=False)

    def __init__(self, **kwargs):
        super(Food, self).__init__(**kwargs)
        self.adjust_nutrients_for_quantity()

    def adjust_nutrients_for_quantity(self):
        """Adjust nutritional values based on the quantity"""
        ratio = self.quantity / DEFAULT_PORTION_SIZE
        self.calories *= ratio
        self.proteins *= ratio
        self.carbs *= ratio
        self.fats *= ratio

    @property
    def formatted_time(self):
        """Return formatted time string"""
        return self.date.strftime("%H:%M")

    def to_dict(self):
        """Convert food entry to dictionary"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "quantity": self.quantity,
            "calories": round(self.calories),
            "proteins": round(self.proteins),
            "carbs": round(self.carbs),
            "fats": round(self.fats),
            "meal_type": self.meal_type,
            "time": self.formatted_time,
        }

    @staticmethod
    def get_daily_totals(user_id, date):
        """Get total nutritional values for a specific day"""
        totals = (
            db.session.query(
                func.coalesce(func.sum(Food.calories), 0).label("calories"),
                func.coalesce(func.sum(Food.proteins), 0).label("proteins"),
                func.coalesce(func.sum(Food.carbs), 0).label("carbs"),
                func.coalesce(func.sum(Food.fats), 0).label("fats"),
            )
            .filter(Food.user_id == user_id, func.date(Food.date) == date)
            .first()
        )

        return (
            totals
            if totals
            else type(
                "DailyTotals", (), {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}
            )
        )

    def __repr__(self):
        return f"<Food {self.name} ({self.quantity}g)>"
