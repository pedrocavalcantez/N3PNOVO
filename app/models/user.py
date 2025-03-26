from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.constants import ACTIVITY_FACTORS, OBJECTIVES, GENDER_CHOICES


class User(UserMixin, db.Model):
    """User model for storing user account information"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    altura = db.Column(db.Float, nullable=False)  # altura em metros
    peso = db.Column(db.Float, nullable=False)  # peso em kg
    sexo = db.Column(
        db.String(1), nullable=False
    )  # 'M' para masculino, 'F' para feminino
    fator_atividade = db.Column(db.String(20), nullable=False)
    objetivo = db.Column(db.String(50), nullable=False)

    # Relationships
    foods = db.relationship("Food", backref="user", lazy=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def set_password(self, password):
        """Set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        return check_password_hash(self.password_hash, password)

    def calculate_bmr(self):
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
        if self.sexo == "M":
            return (10 * self.peso) + (6.25 * self.altura * 100) - (5 * self.idade) + 5
        else:
            return (
                (10 * self.peso) + (6.25 * self.altura * 100) - (5 * self.idade) - 161
            )

    def get_activity_multiplier(self):
        """Get activity multiplier based on activity level"""
        return ACTIVITY_FACTORS.get(
            self.fator_atividade, 1.2
        )  # Default to sedentary if not found

    def get_objective_multiplier(self):
        """Get objective multiplier based on goal"""
        return OBJECTIVES.get(self.objetivo, 1.0)  # Default to maintain if not found

    def calculate_daily_calories(self):
        """Calculate daily calorie needs based on BMR, activity, and goal"""
        bmr = self.calculate_bmr()
        activity_multiplier = self.get_activity_multiplier()
        objective_multiplier = self.get_objective_multiplier()

        return round(bmr * activity_multiplier * objective_multiplier)

    def __repr__(self):
        return f"<User {self.username}>"
