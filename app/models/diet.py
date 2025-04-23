from datetime import datetime
from app import db
from .user import User


class Diet(db.Model):
    __tablename__ = "diets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    meals_data = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"<Diet {self.name}>"
