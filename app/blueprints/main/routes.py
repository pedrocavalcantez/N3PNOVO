from datetime import datetime
from flask import render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.blueprints.main import bp
from app.models import Diet, FoodData, UserFood
from app.constants import MEAL_TYPES, MACRO_TYPES
from app.models.meal_template import MealTemplate
from app.decorators import admin_required


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/index.html", title="Início")


@bp.route("/guest")
def guest():
    return redirect(url_for("main.guest_dashboard"))


@bp.route("/guest_dashboard")
def guest_dashboard():
    return render_template("main/guest_dashboard.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    from datetime import date, datetime
    
    # Aceita parâmetro de data na URL, ou usa hoje como padrão
    date_str = request.args.get("date")
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # Busca o diário da data selecionada (não busca dietas modelo ou de outros dias)
    diary_for_date = (
        Diet.query.filter_by(user_id=current_user.id, date=selected_date)
        .first()
    )

    # Busca todas as dietas modelo do usuário (sem data)
    saved_diets = (
        Diet.query.filter_by(user_id=current_user.id, date=None)
        .order_by(Diet.created_at.desc())
        .all()
    )

    # Data de hoje para o seletor
    today = date.today()
    
    # Inicializa os totais diários e metas do usuário
    daily_totals = {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}

    user_goals = {
        "calories": current_user.calories_goal or 0,
        "proteins": current_user.proteins_goal or 0,
        "carbs": current_user.carbs_goal or 0,
        "fats": current_user.fats_goal or 0,
    }

    # Inicializa as refeições como dicionário vazio (não lista)
    meals = {}

    meal_totals = {}
    for y in MEAL_TYPES.keys():
        meal_totals[y] = {}
        for x in MACRO_TYPES.keys():
            meal_totals[y][x] = 0

    # Se houver um diário para a data selecionada, carrega os dados das refeições
    if diary_for_date and diary_for_date.meals_data:
        meals = diary_for_date.meals_data or {}
        # Atualiza os totais diários com base nas refeições
        for meal_type, foods in meals.items():
            for food in foods:
                daily_totals["calories"] += float(food.get("calories", 0))
                daily_totals["proteins"] += float(food.get("proteins", 0))
                daily_totals["carbs"] += float(food.get("carbs", 0))
                daily_totals["fats"] += float(food.get("fats", 0))

                # Atualiza os totais por refeição
                if meal_type in meal_totals:
                    meal_totals[meal_type]["calories"] += float(food.get("calories", 0))
                    meal_totals[meal_type]["proteins"] += float(food.get("proteins", 0))
                    meal_totals[meal_type]["carbs"] += float(food.get("carbs", 0))
                    meal_totals[meal_type]["fats"] += float(food.get("fats", 0))

    # Sempre renderiza, mas diet=None se não houver diário para a data selecionada
    return render_template(
        "main/dashboard.html",
        title="Dashboard",
        diet=diary_for_date,  # Pode ser None se não houver diário para a data
        meal_types=MEAL_TYPES,
        daily_totals=daily_totals,
        user_goals=user_goals,
        meals=meals,
        meal_totals=meal_totals,
        saved_diets=saved_diets,
        today=selected_date,  # Usa a data selecionada (pode ser hoje ou outra data)
    )


@bp.route("/calculator")
@login_required
def calculator():
    return render_template("main/calculator.html", MEAL_TYPES=MEAL_TYPES)


@bp.route("/chat")
@login_required
def chat():
    """Página do chatbot nutricional"""
    return render_template("main/chat.html", title="Nutri AI - Chat")


@bp.route("/meals")
@login_required
def meals():
    """Página para gerenciar refeições salvas"""
    # Filtra apenas templates do usuário atual
    templates = MealTemplate.query.filter_by(
        user_id=current_user.id
    ).order_by(MealTemplate.meal_type, MealTemplate.name).all()
    
    # Calcular valores nutricionais para cada template
    templates_with_nutrition = []
    for template in templates:
        total_calories = 0
        total_proteins = 0
        total_carbs = 0
        total_fats = 0
        
        if template.meals_data:
            for food_item in template.meals_data:
                food_code = food_item.get("food_code")
                quantity = food_item.get("quantity", 0)
                
                if food_code and quantity:
                    # Buscar dados nutricionais do alimento
                    # First try user's custom foods
                    food_data = UserFood.query.filter_by(
                        code=food_code, user_id=current_user.id
                    ).first()
                    
                    # If not found, try global foods
                    if not food_data:
                        food_data = FoodData.query.filter_by(code=food_code).first()
                    
                    if food_data:
                        # Calcular valores proporcionais baseados na quantidade
                        ratio = quantity / food_data.quantity
                        total_calories += food_data.calories * ratio
                        total_proteins += food_data.proteins * ratio
                        total_carbs += food_data.carbs * ratio
                        total_fats += food_data.fats * ratio
        
        templates_with_nutrition.append({
            "template": template,
            "nutrition": {
                "calories": round(total_calories, 1),
                "proteins": round(total_proteins, 1),
                "carbs": round(total_carbs, 1),
                "fats": round(total_fats, 1),
            }
        })
    
    return render_template("main/meals.html", templates_with_nutrition=templates_with_nutrition, MEAL_TYPES=MEAL_TYPES)


@bp.route("/history")
@login_required
def history():
    """Página para visualizar histórico de diários"""
    # Busca todos os diários do usuário (com date não nulo), ordenados por data (mais recente primeiro)
    diaries = (
        Diet.query.filter_by(user_id=current_user.id)
        .filter(Diet.date.isnot(None))
        .order_by(Diet.date.desc())
        .all()
    )
    
    # Calcula os totais nutricionais para cada diário
    history_data = []
    for diary in diaries:
        total_calories = 0
        total_proteins = 0
        total_carbs = 0
        total_fats = 0
        
        if diary.meals_data:
            for meal_type, foods in diary.meals_data.items():
                for food in foods:
                    total_calories += float(food.get("calories", 0))
                    total_proteins += float(food.get("proteins", 0))
                    total_carbs += float(food.get("carbs", 0))
                    total_fats += float(food.get("fats", 0))
        
        history_data.append({
            "date": diary.date,
            "name": diary.name,
            "calories": round(total_calories, 1),
            "proteins": round(total_proteins, 1),
            "carbs": round(total_carbs, 1),
            "fats": round(total_fats, 1),
        })
    
    return render_template("main/history.html", history_data=history_data)


@bp.route("/api/meal_templates")
@login_required
def get_meal_templates():
    meal_type = request.args.get("meal_type")
    # Filtra apenas templates do usuário atual ou templates globais (user_id is None)
    query = MealTemplate.query.filter(
        (MealTemplate.user_id == current_user.id) | (MealTemplate.user_id.is_(None))
    )
    
    if meal_type:
        query = query.filter_by(meal_type=meal_type)
    
    templates = query.order_by(MealTemplate.created_at.desc()).all()
    return jsonify(
        {"success": True, "templates": [template.to_dict() for template in templates]}
    )


@bp.route("/api/meal_templates/<int:template_id>")
@login_required
def get_meal_template(template_id):
    # Só permite acessar templates do próprio usuário ou templates globais
    template = MealTemplate.query.filter(
        MealTemplate.id == template_id,
        ((MealTemplate.user_id == current_user.id) | (MealTemplate.user_id.is_(None)))
    ).first_or_404()
    return jsonify({"success": True, "template": template.to_dict()})


@bp.route("/admin/meal_templates")
@login_required
@admin_required
def meal_templates():
    return render_template(
        "admin/meal_templates.html", MEAL_TYPES=MEAL_TYPES, MACRO_TYPES=MACRO_TYPES
    )


@bp.route("/api/save_meal_template", methods=["POST"])
@login_required
def save_meal_template():
    """Permite usuários salvarem suas próprias refeições como templates"""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    try:
        base_name = data.get("name", "").strip()
        if not base_name:
            return jsonify({"success": False, "error": "Nome da refeição é obrigatório"}), 400

        meal_type = data.get("meal_type")
        if not meal_type:
            return jsonify({"success": False, "error": "Tipo de refeição é obrigatório"}), 400

        # Verificar se já existe um template com o mesmo nome e tipo de refeição para este usuário
        # Se existir, sobrescrever ao invés de criar um novo
        existing_template = MealTemplate.query.filter_by(
            user_id=current_user.id,
            name=base_name, 
            meal_type=meal_type
        ).first()

        if existing_template:
            # Atualizar template existente
            existing_template.description = data.get("description", "").strip()
            existing_template.meals_data = data.get("meals_data", [])
            existing_template.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({"success": True, "template": existing_template.to_dict(), "updated": True})
        else:
            # Criar novo template
            template = MealTemplate(
                user_id=current_user.id,
                name=base_name,
                description=data.get("description", "").strip(),
                meal_type=meal_type,
                meals_data=data.get("meals_data", []),
            )
            db.session.add(template)
            db.session.commit()
            return jsonify({"success": True, "template": template.to_dict(), "updated": False})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


@bp.route("/api/meal_templates", methods=["POST"])
@login_required
@admin_required
def create_meal_template():
    data = request.get_json()

    try:
        template = MealTemplate(
            name=data["name"],
            description=data.get("description"),
            meal_type=data.get("meal_type"),
            meals_data=data.get("meals_data", []),
        )
        db.session.add(template)
        db.session.commit()
        return jsonify({"success": True, "template": template.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


@bp.route("/api/meal_templates/<int:template_id>", methods=["PUT"])
@login_required
@admin_required
def update_meal_template(template_id):
    template = MealTemplate.query.get_or_404(template_id)
    data = request.get_json()

    try:
        template.name = data["name"]
        template.description = data.get("description")
        template.meal_type = data.get("meal_type", template.meal_type)
        template.meals_data = data.get("meals_data", template.meals_data)

        db.session.commit()
        return jsonify({"success": True, "template": template.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


@bp.route("/api/delete_meal_template/<int:template_id>", methods=["DELETE"])
@login_required
def delete_meal_template_user(template_id):
    """Permite usuários excluírem suas próprias refeições"""
    # Só permite deletar templates do próprio usuário
    template = MealTemplate.query.filter_by(
        id=template_id,
        user_id=current_user.id
    ).first_or_404()

    try:
        db.session.delete(template)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


@bp.route("/api/meal_templates/<int:template_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_meal_template(template_id):
    template = MealTemplate.query.get_or_404(template_id)

    try:
        db.session.delete(template)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


@bp.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    return render_template("admin/admin.html")


@bp.route("/api/constants")
def get_constants():
    return jsonify(
        {"success": True, "meal_types": MEAL_TYPES, "macro_types": MACRO_TYPES}
    )
