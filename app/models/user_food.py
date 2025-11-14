from app import db
from datetime import datetime


class UserFood(db.Model):
    """Model for storing user's custom foods"""

    __tablename__ = "user_foods"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    code = db.Column(db.String(20), nullable=False)  # Food code/identifier (unique per user)
    name = db.Column(db.String(100), nullable=False)  # Food name
    quantity = db.Column(db.Float, nullable=False)  # Default quantity
    calories = db.Column(db.Float, nullable=False)
    proteins = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship("User", backref="custom_foods")

    # Unique constraint: user_id + code combination must be unique
    __table_args__ = (db.UniqueConstraint("user_id", "code", name="unique_user_food_code"),)

    def __repr__(self):
        return f"<UserFood {self.code} - {self.name} (User: {self.user_id})>"

