from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.constants import ACTIVITY_FACTORS, OBJECTIVES, GENDER_CHOICES
from datetime import datetime


class User(UserMixin, db.Model):
    """User model for storing user account information"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    altura = db.Column(db.Float, nullable=False)  # altura em metros
    peso = db.Column(db.Float, nullable=False)  # peso em kg
    sexo = db.Column(
        db.String(1), nullable=False
    )  # 'M' para masculino, 'F' para feminino
    fator_atividade = db.Column(db.String(20), nullable=False)
    objetivo = db.Column(db.String(50), nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    # Nutrition goals
    calories_goal = db.Column(db.Float, nullable=True)
    proteins_goal = db.Column(db.Float, nullable=True)
    carbs_goal = db.Column(db.Float, nullable=True)
    fats_goal = db.Column(db.Float, nullable=True)

    # Relationships
    diets = db.relationship("Diet", lazy=True)

    def get_objetivo_display(self):
        """Get the display name for the user's objective"""
        objetivo_names = {
            "perder_peso": "Perder Peso",
            "manter_peso": "Manter Peso",
            "ganhar_peso": "Ganhar Peso",
            "ganhar_massa": "Ganhar Massa",
        }
        return objetivo_names.get(self.objetivo, self.objetivo)

    def get_fator_atividade_display(self):
        """Get the display name for the user's activity factor"""
        activity_names = {
            "sedentario": "Sedentário",
            "leve": "Levemente Ativo",
            "moderado": "Moderadamente Ativo",
            "muito_ativo": "Muito Ativo",
            "extremamente_ativo": "Extremamente Ativo",
        }
        return activity_names.get(self.fator_atividade, self.fator_atividade)

    def get_sexo_display(self):
        """Get the display name for the user's gender"""
        return GENDER_CHOICES.get(self.sexo, self.sexo)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # Set default goals based on calculated values
        if not self.calories_goal and all(
            [self.peso, self.altura, self.idade, self.sexo]
        ):
            self.update_goals()

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

    def update_goals(
        self,
        calories_goal=None,
        proteins_percentage=0.3,
        carbs_percentage=0.4,
        fats_percentage=0.3,
        commit=False,
    ):
        """Update nutrition goals with custom values"""
        # Validate that percentages sum to 100%
        total_percentage = proteins_percentage + carbs_percentage + fats_percentage
        if abs(total_percentage - 1) > 0.1:
            raise ValueError("A soma das porcentagens deve ser igual a 100%")

        # Update calories goal
        if calories_goal is None:
            calories_goal = self.calculate_daily_calories()

        self.calories_goal = calories_goal

        # Calculate macronutrient goals based on custom percentages
        self.proteins_goal = round((self.calories_goal * (proteins_percentage)) / 4)
        self.carbs_goal = round((self.calories_goal * (carbs_percentage)) / 4)
        self.fats_goal = round((self.calories_goal * (fats_percentage)) / 9)

        # Save changes to database
        if commit:
            db.session.commit()

    def __repr__(self):
        return f"<User {self.username}>"
