from datetime import datetime
from flask import render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.blueprints.main import bp
from app.models import Diet, FoodData
from app.constants import MEAL_TYPES
from app.models.meal_template import MealTemplate, MealTemplateFood
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
    # Busca a dieta mais recente do usuário
    most_recent_diet = (
        Diet.query.filter_by(user_id=current_user.id)
        .order_by(Diet.created_at.desc())
        .first()
    )

    # Busca todas as dietas do usuário
    saved_diets = (
        Diet.query.filter_by(user_id=current_user.id)
        .order_by(Diet.created_at.desc())
        .all()
    )

    # Inicializa os totais diários e metas do usuário
    daily_totals = {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}

    user_goals = {
        "calories": current_user.calories_goal or 0,
        "proteins": current_user.proteins_goal or 0,
        "carbs": current_user.carbs_goal or 0,
        "fats": current_user.fats_goal or 0,
    }

    # Inicializa as refeições
    meals = []

    # Inicializa os totais por refeição
    meal_totals = {
        "cafe_da_manha": {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0},
        "lanche_manha": {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0},
        "almoco": {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0},
        "lanche_tarde": {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0},
        "janta": {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0},
        "ceia": {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0},
    }

    # Se houver uma dieta mais recente, carrega os dados das refeições
    if most_recent_diet and most_recent_diet.meals_data:
        meals = most_recent_diet.meals_data
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

    if not most_recent_diet:
        return render_template(
            "main/dashboard.html",
            title="Dashboard",
            diet=None,
            meal_types=MEAL_TYPES,
            daily_totals=daily_totals,
            user_goals=user_goals,
            meals=meals,
            meal_totals=meal_totals,
            saved_diets=saved_diets,
        )

    return render_template(
        "main/dashboard.html",
        title="Dashboard",
        diet=most_recent_diet,
        meal_types=MEAL_TYPES,
        daily_totals=daily_totals,
        user_goals=user_goals,
        meals=meals,
        meal_totals=meal_totals,
        saved_diets=saved_diets,
    )


@bp.route("/calculator")
@login_required
def calculator():
    return render_template("main/calculator.html", MEAL_TYPES=MEAL_TYPES)


@bp.route("/api/meal_templates")
@login_required
def get_meal_templates():
    meal_type = request.args.get("meal_type")
    if meal_type:
        templates = MealTemplate.query.filter_by(meal_type=meal_type).all()
    else:
        templates = MealTemplate.query.all()
    return jsonify(
        {"success": True, "templates": [template.to_dict() for template in templates]}
    )


@bp.route("/api/meal_templates/<int:template_id>")
@login_required
def get_meal_template(template_id):
    template = MealTemplate.query.get_or_404(template_id)
    return jsonify({"success": True, "template": template.to_dict()})


@bp.route("/admin/meal_templates")
@login_required
@admin_required
def meal_templates():
    return render_template("admin/meal_templates.html")


@bp.route("/api/meal_templates", methods=["POST"])
@login_required
@admin_required
def create_meal_template():
    data = request.get_json()

    try:
        template = MealTemplate(
            name=data["name"],
            description=data.get("description"),
            meal_type=data.get("meal_type", "cafe_da_manha"),
        )
        db.session.add(template)
        db.session.flush()  # Para obter o ID do template

        for food in data["foods"]:
            template_food = MealTemplateFood(
                template_id=template.id,
                food_code=food["food_code"],
                quantity=food["quantity"],
            )
            db.session.add(template_food)

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

        # Remover alimentos existentes
        MealTemplateFood.query.filter_by(template_id=template.id).delete()

        # Adicionar novos alimentos
        for food in data["foods"]:
            template_food = MealTemplateFood(
                template_id=template.id,
                food_code=food["food_code"],
                quantity=food["quantity"],
            )
            db.session.add(template_food)

        db.session.commit()
        return jsonify({"success": True, "template": template.to_dict()})
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
    return render_template("admin/dashboard.html")
