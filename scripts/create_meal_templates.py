import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.meal_template import MealTemplate


def create_meal_templates():
    # Template 1: Café da Manhã Completo
    breakfast = MealTemplate(
        name="Café da Manhã Completo",
        description="Café da manhã balanceado com carboidratos, proteínas e gorduras",
        meal_type="cafe_da_manha",
        meals_data=[
            {"food_code": "Abacate", "quantity": 1},
            {"food_code": "Abacaxi", "quantity": 2},
        ],
    )
    db.session.add(breakfast)

    # Template 2: Almoço Fitness
    lunch = MealTemplate(
        name="Almoço Fitness",
        description="Refeição rica em proteínas e vegetais",
        meal_type="almoco",
        meals_data=[
            {"food_code": "Abacate", "quantity": 2},
            {"food_code": "Abacaxi", "quantity": 3},
        ],
    )
    db.session.add(lunch)

    # Template 3: Lanche Proteico
    snack = MealTemplate(
        name="Lanche Proteico",
        description="Lanche rico em proteínas para pós-treino",
        meal_type="lanche_tarde",
        meals_data=[
            {"food_code": "Abacate", "quantity": 4},
            {"food_code": "Abacaxi", "quantity": 3},
        ],
    )
    db.session.add(snack)

    # Salvar todas as alterações
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_meal_templates()
        print("Templates de refeições criados com sucesso!")
