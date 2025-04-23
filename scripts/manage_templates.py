from app import create_app, db
from app.models.meal_template import MealTemplate, MealTemplateFood

# Criar a aplicação e o contexto
app = create_app()
app.app_context().push()

def criar_template_cafe():
    """Cria um template de café da manhã"""
    foods = [
        {"food_code": "Pão Integral", "quantity": 50},
        {"food_code": "Ovos", "quantity": 100},
        {"food_code": "Café", "quantity": 200}
    ]
    
    template = MealTemplate(
        name="Café da Manhã Proteico",
        description="Café da manhã rico em proteínas",
        meal_type="cafe_da_manha"
    )
    db.session.add(template)
    db.session.flush()
    
    for food in foods:
        food_item = MealTemplateFood(
            template_id=template.id,
            food_code=food["food_code"],
            quantity=food["quantity"]
        )
        db.session.add(food_item)
    
    db.session.commit()
    print("Template de café da manhã criado!")

def criar_template_almoco():
    """Cria um template de almoço"""
    foods = [
        {"food_code": "Arroz", "quantity": 100},
        {"food_code": "Feijão", "quantity": 80},
        {"food_code": "Frango", "quantity": 150}
    ]
    
    template = MealTemplate(
        name="Almoço Tradicional",
        description="Almoço tradicional brasileiro",
        meal_type="almoco"
    )
    db.session.add(template)
    db.session.flush()
    
    for food in foods:
        food_item = MealTemplateFood(
            template_id=template.id,
            food_code=food["food_code"],
            quantity=food["quantity"]
        )
        db.session.add(food_item)
    
    db.session.commit()
    print("Template de almoço criado!")

def listar_templates():
    """Lista todos os templates"""
    templates = MealTemplate.query.all()
    
    if not templates:
        print("Nenhum template encontrado!")
        return
        
    for template in templates:
        print(f"\nTemplate: {template.name}")
        print(f"Tipo: {template.meal_type}")
        print(f"Descrição: {template.description}")
        print("Alimentos:")
        for food in template.foods:
            print(f"  - {food.food_code}: {food.quantity}g")

def deletar_todos_templates():
    """Deleta todos os templates"""
    try:
        num_deleted = MealTemplate.query.delete()
        num_deleted = MealTemplateFood.query.delete()

        db.session.commit()
        print(f"{num_deleted} templates deletados!")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar templates: {str(e)}")

if __name__ == "__main__":
    # Menu simples
    while True:
        print("\nGerenciador de Templates de Refeição")
        print("1. Criar template de café da manhã")
        print("2. Criar template de almoço")
        print("3. Listar todos os templates")
        print("4. Deletar todos os templates")
        print("5. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            criar_template_cafe()
        elif opcao == "2":
            criar_template_almoco()
        elif opcao == "3":
            listar_templates()
        elif opcao == "4":
            deletar_todos_templates()
        elif opcao == "5":
            print("Saindo...")
            break
        else:
            print("Opção inválida!") 