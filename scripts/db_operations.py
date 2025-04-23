from app import create_app, db
from app.models.meal_template import MealTemplate, MealTemplateFood

def list_templates():
    """Lista todos os templates de refeição"""
    templates = MealTemplate.query.all()
    for template in templates:
        print(f"\nTemplate: {template.name}")
        print(f"Tipo: {template.meal_type}")
        print(f"Descrição: {template.description}")
        print("Alimentos:")
        for food in template.foods:
            print(f"  - {food.food_code}: {food.quantity}g")

def create_template(name, description, meal_type, foods):
    """
    Cria um novo template de refeição
    
    Exemplo de uso:
    foods = [
        {"food_code": "Arroz", "quantity": 100},
        {"food_code": "Feijão", "quantity": 50}
    ]
    create_template("Almoço Básico", "Almoço simples e nutritivo", "almoco", foods)
    """
    try:
        template = MealTemplate(
            name=name,
            description=description,
            meal_type=meal_type
        )
        db.session.add(template)
        db.session.flush()

        for food in foods:
            template_food = MealTemplateFood(
                template_id=template.id,
                food_code=food["food_code"],
                quantity=food["quantity"]
            )
            db.session.add(template_food)
        
        db.session.commit()
        print(f"Template '{name}' criado com sucesso!")
        return template
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar template: {str(e)}")
        return None

def delete_template(name):
    """Deleta um template pelo nome"""
    try:
        template = MealTemplate.query.filter_by(name=name).first()
        if template:
            db.session.delete(template)
            db.session.commit()
            print(f"Template '{name}' deletado com sucesso!")
        else:
            print(f"Template '{name}' não encontrado.")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar template: {str(e)}")

def update_template(name, new_foods):
    """
    Atualiza os alimentos de um template
    
    Exemplo de uso:
    new_foods = [
        {"food_code": "Arroz Integral", "quantity": 100},
        {"food_code": "Feijão Preto", "quantity": 50}
    ]
    update_template("Almoço Básico", new_foods)
    """
    try:
        template = MealTemplate.query.filter_by(name=name).first()
        if not template:
            print(f"Template '{name}' não encontrado.")
            return

        # Remove alimentos existentes
        MealTemplateFood.query.filter_by(template_id=template.id).delete()

        # Adiciona novos alimentos
        for food in new_foods:
            template_food = MealTemplateFood(
                template_id=template.id,
                food_code=food["food_code"],
                quantity=food["quantity"]
            )
            db.session.add(template_food)

        db.session.commit()
        print(f"Template '{name}' atualizado com sucesso!")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar template: {str(e)}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # # Exemplo de uso:
        # print("\nListando templates existentes:")
        # list_templates()

        # # Criando um novo template
        # print("\nCriando novo template:")
        # foods = [
        #     {"food_code": "Arroz", "quantity": 100},
        #     {"food_code": "Feijão", "quantity": 50},
        #     {"food_code": "Frango", "quantity": 150}
        # ]
        # create_template(
        #     "Almoço Completo",
        #     "Refeição balanceada com proteína e carboidratos",
        #     "almoco",
        #     foods
        # )

        # print("\nListando templates após criação:")
        # list_templates()

        # # Atualizando o template
        # print("\nAtualizando template:")
        # new_foods = [
        #     {"food_code": "Arroz Integral", "quantity": 100},
        #     {"food_code": "Feijão Preto", "quantity": 50},
        #     {"food_code": "Peito de Frango", "quantity": 150}
        # ]
        # update_template("Almoço Completo", new_foods)

        print("\nListando templates após atualização:")
        list_templates()

        # Deletando o template
        print("\nDeletando template:")
        delete_template("Almoço Completo")

        print("\nListando templates após deleção:")
        list_templates() 