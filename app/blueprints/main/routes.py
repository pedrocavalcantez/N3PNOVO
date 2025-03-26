from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.blueprints.main import bp
from app.models import Food
from app.forms import FoodForm
from app.constants import MEAL_TYPES
import pandas as pd
import os
import json


def load_food_data():
    try:
        excel_path = os.path.join("data", "food.xlsx")
        return pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error loading food data: {str(e)}")
        return pd.DataFrame()


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
    # For guests, we'll show empty totals since they don't have a history
    empty_foods_by_meal = {
        "cafe_da_manha": [],
        "lanche_manha": [],
        "almoco": [],
        "lanche_tarde": [],
        "janta": [],
        "ceia": [],
    }

    # Calculate empty meal totals
    empty_meal_totals = {
        meal_type: type(
            "MealTotals", (), {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}
        )
        for meal_type in MEAL_TYPES.keys()
    }

    return render_template(
        "main/dashboard.html",
        user=None,  # No user for guests
        foods_by_meal=empty_foods_by_meal,
        total_calories=0,
        total_proteins=0,
        total_carbs=0,
        total_fats=0,
        daily_totals=type(
            "DailyTotals", (), {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}
        ),
        user_goals=type(
            "UserGoals", (), {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}
        ),
        meal_types=MEAL_TYPES,
        meals=empty_foods_by_meal,
        meal_totals=empty_meal_totals,
    )


@bp.route("/dashboard")
@login_required
def dashboard():
    today = datetime.utcnow().date()
    foods = Food.query.filter(
        Food.user_id == current_user.id, db.func.date(Food.date) == today
    ).all()

    # Group foods by meal type
    foods_by_meal = {
        "cafe_da_manha": [],
        "lanche_manha": [],
        "almoco": [],
        "lanche_tarde": [],
        "janta": [],
        "ceia": [],
    }

    for food in foods:
        foods_by_meal[food.meal_type].append(food)

    # Calculate totals
    total_calories = sum(food.calories for food in foods)
    total_proteins = sum(food.proteins for food in foods)
    total_carbs = sum(food.carbs for food in foods)
    total_fats = sum(food.fats for food in foods)

    # Get daily totals from the model
    daily_totals = Food.get_daily_totals(current_user.id, today)

    # Calculate user's daily goals
    user_goals = type(
        "UserGoals",
        (),
        {
            "calories": current_user.calculate_daily_calories(),
            "proteins": current_user.calculate_daily_calories()
            * 0.3
            / 4,  # 30% of calories from protein
            "carbs": current_user.calculate_daily_calories()
            * 0.4
            / 4,  # 40% of calories from carbs
            "fats": current_user.calculate_daily_calories()
            * 0.3
            / 9,  # 30% of calories from fats
        },
    )

    # Calculate meal totals
    meal_totals = {}
    for meal_type in MEAL_TYPES.keys():
        meal_foods = foods_by_meal[meal_type]
        meal_totals[meal_type] = type(
            "MealTotals",
            (),
            {
                "calories": sum(food.calories for food in meal_foods),
                "proteins": sum(food.proteins for food in meal_foods),
                "carbs": sum(food.carbs for food in meal_foods),
                "fats": sum(food.fats for food in meal_foods),
            },
        )

    return render_template(
        "main/dashboard.html",
        user=current_user,
        foods_by_meal=foods_by_meal,
        total_calories=total_calories,
        total_proteins=total_proteins,
        total_carbs=total_carbs,
        total_fats=total_fats,
        daily_totals=daily_totals,
        user_goals=user_goals,
        meal_types=MEAL_TYPES,
        meals=foods_by_meal,
        meal_totals=meal_totals,
    )


@bp.route("/search_food")
def search_food():
    query = request.args.get("q", "").lower()
    if not query:
        return jsonify([])

    df = load_food_data()
    if df.empty:
        return jsonify([])

    # Convert identificador to string and search for matches
    df["identificador"] = df["identificador"].astype(str)
    matches = df[df["identificador"].str.lower().str.contains(query, na=False)]

    # Get top 5 matches
    results = matches.head(5).to_dict("records")

    # Format results for dropdown
    formatted_results = [
        {
            "name": str(row["identificador"]),
            "Quantidade": float(row["Quantidade"]),
            "Calorias": float(row["Calorias"]),
            "Proteínas": float(row["Proteínas"]),
            "Carboidratos": float(row["Carboidratos"]),
            "Gorduras": float(row["Gorduras"]),
        }
        for row in results
    ]

    return jsonify(formatted_results)


@bp.route("/add_food", methods=["POST"])
def add_food():
    if request.method == "POST":
        # Check if we're receiving multiple foods
        foods_json = request.form.get("foods")
        if foods_json:
            foods_data = json.loads(foods_json)
            meal_type = request.form.get("meal_type")  # Get meal type from form

            # If user is logged in, save to database
            if current_user.is_authenticated:
                for food_item in foods_data:
                    food = Food(
                        name=str(food_item["code"]),
                        quantity=food_item["quantity"],
                        calories=food_item["calories"],
                        proteins=food_item["proteins"],
                        carbs=food_item["carbs"],
                        fats=food_item["fats"],
                        user_id=current_user.id,
                        meal_type=meal_type,  # Add meal type to food entry
                    )
                    db.session.add(food)

                try:
                    db.session.commit()
                    flash("Alimentos adicionados com sucesso!", "success")
                except Exception as e:
                    db.session.rollback()
                    flash("Erro ao adicionar alimentos. Tente novamente.", "error")
            else:
                # For guests, just return success without saving
                flash("Alimentos calculados com sucesso!", "success")

            return jsonify({"status": "success"})

        # Handle single food submission
        food_id = request.form.get("food_id")
        quantity_consumed = float(request.form.get("quantity", 0))
        meal_type = request.form.get("meal_type")  # Get meal type from form

        df = load_food_data()
        if df.empty:
            flash("Erro ao carregar dados dos alimentos.", "error")
            return redirect(url_for("main.dashboard"))

        # Convert food_id to string for comparison
        food_id = str(food_id)
        df["identificador"] = df["identificador"].astype(str)
        food_data = df[df["identificador"] == food_id].iloc[0]
        base_quantity = food_data["Quantidade"]

        # Calculate the proportion
        proportion = quantity_consumed / base_quantity

        food = Food(
            name=str(food_data["identificador"]),
            quantity=quantity_consumed,
            calories=food_data["Calorias"] * proportion,
            proteins=food_data["Proteínas"] * proportion,
            carbs=food_data["Carboidratos"] * proportion,
            fats=food_data["Gorduras"] * proportion,
            user_id=current_user.id,
            meal_type=meal_type,  # Add meal type to food entry
        )

        try:
            db.session.add(food)
            db.session.commit()
            flash("Alimento adicionado com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao adicionar alimento. Tente novamente.", "error")

    return redirect(url_for("main.dashboard"))


@bp.route("/delete_food/<int:food_id>", methods=["POST"])
@login_required
def delete_food(food_id):
    food = Food.query.get_or_404(food_id)

    # Verificar se o alimento pertence ao usuário atual
    if food.user_id != current_user.id:
        abort(403)  # Forbidden

    try:
        db.session.delete(food)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
