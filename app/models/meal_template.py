from datetime import datetime
from app import db


class MealTemplate(db.Model):
    __tablename__ = "meal_templates"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # Nullable para templates globais/admin
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    meal_type = db.Column(db.String(20), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    meals_data = db.Column(db.JSON, nullable=True)

    # Relationship
    user = db.relationship("User", backref="meal_templates")

    # Unique constraint: user_id + name + meal_type combination must be unique
    __table_args__ = (db.UniqueConstraint("user_id", "name", "meal_type", name="unique_user_meal_template"),)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "meal_type": self.meal_type,
            "meals_data": self.meals_data or [],
        }
