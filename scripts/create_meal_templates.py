import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.meal_template import MealTemplate, MealTemplateFood

def create_meal_templates():
    # Template 1: Café da Manhã Completo
    breakfast = MealTemplate(
        name="Café da Manhã Completo",
        description="Café da manhã balanceado com carboidratos, proteínas e gorduras",
        meal_type="cafe_da_manha"
    )
    db.session.add(breakfast)
    db.session.flush()  # Para obter o ID do template

    # Itens do café da manhã
    breakfast_items = [
        MealTemplateFood(template_id=breakfast.id, food_code="Abacate", quantity=1),
        MealTemplateFood(template_id=breakfast.id, food_code="Abacaxi", quantity=2),
    ]
    db.session.add_all(breakfast_items)

    # Template 2: Almoço Fitness
    lunch = MealTemplate(
        name="Almoço Fitness",
        description="Refeição rica em proteínas e vegetais",
        meal_type="almoco"
    )
    db.session.add(lunch)
    db.session.flush()

    # Itens do almoço
    lunch_items = [
        MealTemplateFood(template_id=lunch.id, food_code="Abacate", quantity=2),
        MealTemplateFood(template_id=lunch.id, food_code="Abacaxi", quantity=3),
    ]
    db.session.add_all(lunch_items)

    # Template 3: Lanche Proteico
    snack = MealTemplate(
        name="Lanche Proteico",
        description="Lanche rico em proteínas para pós-treino",
        meal_type="lanche_tarde"
    )
    db.session.add(snack)
    db.session.flush()

    # Itens do lanche
    snack_items = [
        MealTemplateFood(template_id=snack.id, food_code="Abacate", quantity=4),
        MealTemplateFood(template_id=snack.id, food_code="Abacaxi", quantity=3),
    ]
    db.session.add_all(snack_items)

    # Salvar todas as alterações
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        create_meal_templates()
        print("Templates de refeições criados com sucesso!") 