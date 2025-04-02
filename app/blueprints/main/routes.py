from datetime import datetime
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    abort,
    send_file,
)
from flask_login import login_required, current_user
from app import db
from app.blueprints.main import bp
from app.models import Food
from app.forms import FoodForm
from app.constants import MEAL_TYPES
import pandas as pd
import os
import json
from io import BytesIO


def load_food_data():
    try:
        excel_path = os.path.join("data", "food.xlsx")
        return pd.read_excel(excel_path).sort_values(by="identificador")
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
    return render_template("main/guest_dashboard.html")


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

    # Calculate meal totals
    meal_totals = {}
    for meal_type, foods_list in foods_by_meal.items():
        meal_totals[meal_type] = type(
            "MealTotals",
            (),
            {
                "calories": sum(food.calories for food in foods_list),
                "proteins": sum(food.proteins for food in foods_list),
                "carbs": sum(food.carbs for food in foods_list),
                "fats": sum(food.fats for food in foods_list),
            },
        )

    # Get user goals
    user_goals = type(
        "UserGoals",
        (),
        {
            "calories": current_user.calories_goal or 0,
            "proteins": current_user.proteins_goal or 0,
            "carbs": current_user.carbs_goal or 0,
            "fats": current_user.fats_goal or 0,
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
        daily_totals=type(
            "DailyTotals",
            (),
            {
                "calories": total_calories,
                "proteins": total_proteins,
                "carbs": total_carbs,
                "fats": total_fats,
            },
        ),
        user_goals=user_goals,
        meal_types=MEAL_TYPES,
        meals=foods_by_meal,
        meal_totals=meal_totals,
    )


@bp.route("/api/search_food")
def search_food():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify([])

    df = load_food_data()
    if df.empty:
        return jsonify([])

    # Search in both code and name columns
    # First find exact matches at start
    starts_with_mask = (
        df["identificador"]
        .astype(str)
        .str.lower()
        .str.startswith(query.lower(), na=False)
    )
    # Then find partial matches
    contains_mask = (
        df["identificador"].astype(str).str.contains(query, case=False, na=False)
    )
    # Combine masks with OR, but prioritize exact matches by putting them first
    mask = starts_with_mask | contains_mask
    results = pd.concat([df[starts_with_mask].head(5), df[contains_mask].head(5)]).head(
        5
    )

    return jsonify(
        [
            {
                "code": str(row["identificador"]),
                "qtd": str(row["Quantidade"]),
                "name": row["identificador"],
                "calories": float(row["Calorias"]),
                "proteins": float(row["Proteínas"]),
                "carbs": float(row["Carboidratos"]),
                "fats": float(row["Gorduras"]),
            }
            for _, row in results.iterrows()
        ]
    )


@bp.route("/api/food_nutrition/<code>")
def get_food_nutrition(code):
    quantity = float(request.args.get("quantity", 100))
    df = load_food_data()

    if df.empty:
        return jsonify({"error": "Food database not available"}), 500

    food = df[df["identificador"].astype(str) == str(code)]
    if food.empty:
        return jsonify({"error": "Food not found"}), 404

    row = food.iloc[0]
    multiplier = quantity / 100  # Use the requested quantity for the multiplier

    return jsonify(
        {
            "calories": float(row["Calorias"]) * multiplier,
            "proteins": float(row["Proteínas"]) * multiplier,
            "carbs": float(row["Carboidratos"]) * multiplier,
            "fats": float(row["Gorduras"]) * multiplier,
        }
    )


@bp.route("/api/add_food", methods=["POST"])
def add_food():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        code = data.get("code")
        quantity = float(data.get("quantity", 32))
        meal_type = data.get("meal_type")

        if not all([code, quantity, meal_type]):
            return jsonify({"error": "Missing required fields"}), 400

        if meal_type not in MEAL_TYPES:
            return jsonify({"error": "Invalid meal type"}), 400

        # Get food nutrition data
        df = load_food_data()
        if df.empty:
            return jsonify({"error": "Food database not available"}), 500

        food = df[df["identificador"].astype(str) == str(code)]
        if food.empty:
            return jsonify({"error": "Food not found"}), 404

        row = food.iloc[0]
        multiplier = quantity / 100

        new_food = None
        if current_user.is_authenticated:
            # Create new food entry for authenticated users
            new_food = Food(
                user_id=current_user.id,
                code=code,
                name=row["identificador"],
                quantity=quantity,
                calories=float(row["Calorias"]) * multiplier,
                proteins=float(row["Proteínas"]) * multiplier,
                carbs=float(row["Carboidratos"]) * multiplier,
                fats=float(row["Gorduras"]) * multiplier,
                meal_type=meal_type,
                date=datetime.utcnow(),
            )

            db.session.add(new_food)
            db.session.commit()

        # For both authenticated and guest users, return success
        return jsonify(
            {
                "success": True,
                "message": "Food added successfully",
                "food": {
                    "id": getattr(new_food, "id", None),  # None for guests
                    "name": row["identificador"],
                    "quantity": quantity,
                    "calories": float(row["Calorias"]) * multiplier,
                    "proteins": float(row["Proteínas"]) * multiplier,
                    "carbs": float(row["Carboidratos"]) * multiplier,
                    "fats": float(row["Gorduras"]) * multiplier,
                },
            }
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in add_food: {str(e)}")
        # Always return JSON, even for errors
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@bp.route("/api/delete_food/<int:food_id>", methods=["DELETE"])
def delete_food(food_id):
    if current_user.is_authenticated:
        food = Food.query.get_or_404(food_id)
        if food.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
        db.session.delete(food)
        db.session.commit()

    # For both authenticated and guest users, return success
    return jsonify({"success": True, "message": "Food deleted successfully"})


@bp.route("/export_food_data")
@login_required
def export_food_data():
    try:
        # Get all food entries for the current user
        foods = Food.query.filter_by(user_id=current_user.id).all()

        # Convert to DataFrame
        data = []
        for food in foods:
            data.append(
                {
                    "Data": food.date.strftime("%Y-%m-%d"),
                    "Refeição": MEAL_TYPES.get(food.meal_type, food.meal_type),
                    "Alimento": food.name,
                    "Quantidade (g)": food.quantity,
                    "Calorias": food.calories,
                    "Proteínas": food.proteins,
                    "Carboidratos": food.carbs,
                    "Gorduras": food.fats,
                }
            )

        df = pd.DataFrame(data)

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Registro Alimentar", index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets["Registro Alimentar"]
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).apply(len).max(), len(str(col)))
                worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

        output.seek(0)

        # Generate filename with current date
        filename = f"registro_alimentar_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        flash(f"Erro ao exportar dados: {str(e)}", "error")
        return redirect(url_for("main.dashboard"))
