from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from app.models.meal_template import MealTemplate, MealTemplateFood
from app.extensions import db
from app.decorators import admin_required

bp = Blueprint("main", __name__)


@bp.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    return render_template("admin/admin.html")


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
            meal_type=data.get("meal_type"),
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
