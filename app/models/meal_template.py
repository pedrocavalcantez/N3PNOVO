from datetime import datetime
from app import db

class MealTemplate(db.Model):
    __tablename__ = 'meal_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    meal_type = db.Column(db.String(20), nullable=False, index=True, default='cafe_da_manha')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com os alimentos do template
    foods = db.relationship('MealTemplateFood', backref='template', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'meal_type': self.meal_type,
            'foods': [food.to_dict() for food in self.foods]
        }

class MealTemplateFood(db.Model):
    __tablename__ = 'meal_template_items'

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('meal_templates.id', ondelete='CASCADE'), nullable=False)
    food_code = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'food_code': self.food_code,
            'quantity': self.quantity
        } 