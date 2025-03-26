from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange
from app.constants import MEAL_TYPES


class FoodForm(FlaskForm):
    """Form for food entry"""

    name = StringField("Nome do Alimento", validators=[DataRequired(), Length(max=100)])
    quantity = FloatField(
        "Quantidade (g)", validators=[DataRequired(), NumberRange(min=0.1)]
    )
    calories = FloatField("Calorias", validators=[DataRequired(), NumberRange(min=0)])
    proteins = FloatField(
        "Proteínas (g)", validators=[DataRequired(), NumberRange(min=0)]
    )
    carbs = FloatField(
        "Carboidratos (g)", validators=[DataRequired(), NumberRange(min=0)]
    )
    fats = FloatField("Gorduras (g)", validators=[DataRequired(), NumberRange(min=0)])
    meal_type = SelectField(
        "Tipo de Refeição",
        choices=list(MEAL_TYPES.items()),
        validators=[DataRequired()],
    )
