from datetime import datetime
from flask import render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.blueprints.main import bp
from app.models import Diet, FoodData
from app.constants import MEAL_TYPES


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
    saved_diets = (
        Diet.query.filter_by(user_id=current_user.id)
        .order_by(Diet.created_at.desc())
        .all()
    )

    # Initialize empty meals and totals
    meals = {meal_type: [] for meal_type in MEAL_TYPES}
    meal_totals = {
        meal_type: {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}
        for meal_type in MEAL_TYPES
    }
    daily_totals = {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}

    # If there are saved diets, load the most recent one
    if saved_diets:
        most_recent_diet = saved_diets[0]
        meals_data = most_recent_diet.meals_data

        # Calculate meal totals and daily totals
        for meal_type, foods in meals_data.items():
            meal_total = {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}
            meal_foods = []

            for food in foods:
                # Get food data from FoodData table
                food_data = FoodData.query.filter_by(code=food["food_code"]).first()
                print("Search FoodData", food_data)
                if food_data:
                    # Create food entry with code from FoodData
                    food_entry = {
                        "id": food_data.id,
                        "food_code": food_data.code,
                        "quantity": food["quantity"],
                        "calories": food["calories"],
                        "proteins": food["proteins"],
                        "carbs": food["carbs"],
                        "fats": food["fats"],
                    }
                    meal_foods.append(food_entry)

                    # Add to totals
                    meal_total["calories"] += float(food["calories"])
                    meal_total["proteins"] += float(food["proteins"])
                    meal_total["carbs"] += float(food["carbs"])
                    meal_total["fats"] += float(food["fats"])

            meals[meal_type] = meal_foods
            meal_totals[meal_type] = meal_total
            daily_totals["calories"] += meal_total["calories"]
            daily_totals["proteins"] += meal_total["proteins"]
            daily_totals["carbs"] += meal_total["carbs"]
            daily_totals["fats"] += meal_total["fats"]

    # Get user goals from the current user
    user_goals = {
        "calories": current_user.calories_goal or 0,
        "proteins": current_user.proteins_goal or 0,
        "carbs": current_user.carbs_goal or 0,
        "fats": current_user.fats_goal or 0,
    }

    return render_template(
        "main/dashboard.html",
        saved_diets=saved_diets,
        daily_totals=daily_totals,
        user_goals=user_goals,
        meal_types=MEAL_TYPES,
        meals=meals,
        meal_totals=meal_totals,
    )


@bp.route("/calculator")
@login_required
def calculator():
    return render_template("main/calculator.html")
