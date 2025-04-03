from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.blueprints.api import bp
from app.models import Diet, FoodData


@bp.route("/search_food")
@login_required
def search_food():
    query = request.args.get("query", "").strip()
    print(query)

    if len(query) < 2:
        return jsonify([])

    # Search only in code field
    foods = FoodData.query.filter(FoodData.code.ilike(f"%{query}%")).limit(10).all()
    # print([{"food_code": food.code, "qtd": food.quantity} for food in foods])
    return jsonify([{"food_code": food.code, "qtd": food.quantity} for food in foods])


@bp.route("/food_nutrition/<code>")
@login_required
def get_food_nutrition(code):
    try:
        food = FoodData.query.filter_by(code=code).first()
        if food:
            # Get quantity from query parameters, default to food's base quantity
            quantity = float(request.args.get("quantity", food.quantity))

            # Calculate proportional nutritional values
            ratio = quantity / food.quantity
            return jsonify(
                {
                    "success": True,
                    "food_code": food.code,
                    "calories": food.calories * ratio,
                    "proteins": food.proteins * ratio,
                    "carbs": food.carbs * ratio,
                    "fats": food.fats * ratio,
                    "quantity": quantity,
                }
            )
        return jsonify({"success": False, "error": "Food not found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@bp.route("/add_food", methods=["POST"])
@login_required
def add_food():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        code = data.get("food_code")
        quantity = data.get("quantity")
        meal_type = data.get("meal_type")

        if not all([code, quantity is not None, meal_type]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Get food data
        food = FoodData.query.filter_by(code=code).first()

        if not food:
            return jsonify({"success": False, "error": "Food not found"}), 404

        # Calculate nutrition values based on quantity
        nutrition = {
            "calories": food.calories * (quantity / food.quantity),
            "proteins": food.proteins * (quantity / food.quantity),
            "carbs": food.carbs * (quantity / food.quantity),
            "fats": food.fats * (quantity / food.quantity),
        }

        return jsonify(
            {
                "success": True,
                "food": {
                    "id": food.id,
                    "food_code": food.code,
                    "quantity": quantity,
                    **nutrition,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/delete_food/<int:food_id>", methods=["DELETE"])
@login_required
def delete_food(food_id):
    try:
        # In this case, we don't actually delete from the database
        # since we're just removing from the UI
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/save_diet", methods=["POST"])
@login_required
def save_diet():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        name = data.get("name")
        meals_data = data.get("meals_data")
        diet_id = request.args.get("diet_id")

        if not name or not meals_data:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        if diet_id:
            # Update existing diet
            diet = Diet.query.filter_by(
                id=diet_id, user_id=current_user.id
            ).first_or_404()
            diet.name = name
            diet.meals_data = meals_data
        else:
            # Create new diet
            diet = Diet(name=name, user_id=current_user.id, meals_data=meals_data)
            db.session.add(diet)

        db.session.commit()
        return jsonify({"success": True, "message": "Diet saved successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/load_diet/<int:diet_id>")
@login_required
def load_diet(diet_id):
    try:
        diet = Diet.query.filter_by(id=diet_id, user_id=current_user.id).first_or_404()
        return jsonify(
            {"success": True, "name": diet.name, "meals_data": diet.meals_data}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/delete_diet/<int:diet_id>", methods=["DELETE"])
@login_required
def delete_diet(diet_id):
    try:
        # Find the diet and ensure it belongs to the current user
        diet = Diet.query.filter_by(id=diet_id, user_id=current_user.id).first_or_404()

        # Delete the diet
        db.session.delete(diet)
        db.session.commit()

        return jsonify({"success": True, "message": "Diet deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
