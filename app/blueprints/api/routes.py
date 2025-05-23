from flask import jsonify, request, send_file
from flask_login import login_required, current_user
from app import db
from app.blueprints.api import bp
from app.models import Diet, FoodData
from datetime import datetime
import pandas as pd
from io import BytesIO
from app.constants import MEAL_TYPES


@bp.route("/search_food")
@login_required
def search_food():
    query = request.args.get("query", "").strip()
    print(query)

    if len(query) < 2:
        return jsonify([])

    # First, search for elements that start with the query
    foods_start = (
        FoodData.query.filter(FoodData.code.ilike(f"{query}%")).limit(10).all()
    )

    # If less than 10 results, search for elements that contain the query
    if len(foods_start) < 10:
        additional_foods = (
            FoodData.query.filter(FoodData.code.ilike(f"%{query}%"))
            .limit(10 - len(foods_start))
            .all()
        )
        foods = foods_start + additional_foods
    else:
        foods = foods_start
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


@bp.route("/calculate_portions", methods=["POST"])
@login_required
def calculate_portions():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        targets = data.get("targets")
        foods_data = data.get("foods")
        tolerance = data.get("tolerance", 0.1)  # Default to 10% if not provided

        if not targets or not foods_data:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Get food data for all selected foods
        foods = []
        for food_item in foods_data:
            food = FoodData.query.filter_by(code=food_item["code"]).first()
            if food:
                foods.append(
                    {
                        "code": food.code,
                        "calories_per_100g": 100 * food.calories / food.quantity,
                        "proteins_per_100g": 100 * food.proteins / food.quantity,
                        "carbs_per_100g": 100 * food.carbs / food.quantity,
                        "fats_per_100g": 100 * food.fats / food.quantity,
                        "min": food_item.get("min"),
                        "max": food_item.get("max"),
                    }
                )

        if not foods:
            return jsonify({"success": False, "error": "No valid foods found"}), 400

        # Use scipy's optimize to find portions
        try:
            from scipy.optimize import minimize
            import numpy as np

            # Initial guess: equal distribution
            n_foods = len(foods)
            x0 = np.ones(n_foods) * 100  # Start with 100g each

            # Objective function: minimize the sum of squared differences from all targets
            def objective(x):
                total_error = 0

                if targets["calories"] > 0:
                    total_calories = sum(
                        x[i] * foods[i]["calories_per_100g"] / 100
                        for i in range(n_foods)
                    )
                    total_error += (
                        (total_calories - targets["calories"]) / targets["calories"]
                    ) ** 2

                if targets["proteins"] > 0:
                    total_proteins = sum(
                        x[i] * foods[i]["proteins_per_100g"] / 100
                        for i in range(n_foods)
                    )
                    total_error += (
                        (total_proteins - targets["proteins"]) / targets["proteins"]
                    ) ** 2

                if targets["carbs"] > 0:
                    total_carbs = sum(
                        x[i] * foods[i]["carbs_per_100g"] / 100 for i in range(n_foods)
                    )
                    total_error += (
                        (total_carbs - targets["carbs"]) / targets["carbs"]
                    ) ** 2

                if targets["fats"] > 0:
                    total_fats = sum(
                        x[i] * foods[i]["fats_per_100g"] / 100 for i in range(n_foods)
                    )
                    total_error += (
                        (total_fats - targets["fats"]) / targets["fats"]
                    ) ** 2

                return total_error

            # Constraints for each target with tolerance
            constraints = []

            if targets["calories"] > 0:
                min_calories = targets["calories"] * (1 - tolerance)
                max_calories = targets["calories"] * (1 + tolerance)
                constraints.extend(
                    [
                        {
                            "type": "ineq",
                            "fun": lambda x: sum(
                                x[i] * foods[i]["calories_per_100g"] / 100
                                for i in range(n_foods)
                            )
                            - min_calories,
                        },
                        {
                            "type": "ineq",
                            "fun": lambda x: max_calories
                            - sum(
                                x[i] * foods[i]["calories_per_100g"] / 100
                                for i in range(n_foods)
                            ),
                        },
                    ]
                )

            if targets["proteins"] > 0:
                min_proteins = targets["proteins"] * (1 - tolerance)
                max_proteins = targets["proteins"] * (1 + tolerance)
                constraints.extend(
                    [
                        {
                            "type": "ineq",
                            "fun": lambda x: sum(
                                x[i] * foods[i]["proteins_per_100g"] / 100
                                for i in range(n_foods)
                            )
                            - min_proteins,
                        },
                        {
                            "type": "ineq",
                            "fun": lambda x: max_proteins
                            - sum(
                                x[i] * foods[i]["proteins_per_100g"] / 100
                                for i in range(n_foods)
                            ),
                        },
                    ]
                )

            if targets["carbs"] > 0:
                min_carbs = targets["carbs"] * (1 - tolerance)
                max_carbs = targets["carbs"] * (1 + tolerance)
                constraints.extend(
                    [
                        {
                            "type": "ineq",
                            "fun": lambda x: sum(
                                x[i] * foods[i]["carbs_per_100g"] / 100
                                for i in range(n_foods)
                            )
                            - min_carbs,
                        },
                        {
                            "type": "ineq",
                            "fun": lambda x: max_carbs
                            - sum(
                                x[i] * foods[i]["carbs_per_100g"] / 100
                                for i in range(n_foods)
                            ),
                        },
                    ]
                )

            if targets["fats"] > 0:
                min_fats = targets["fats"] * (1 - tolerance)
                max_fats = targets["fats"] * (1 + tolerance)
                constraints.extend(
                    [
                        {
                            "type": "ineq",
                            "fun": lambda x: sum(
                                x[i] * foods[i]["fats_per_100g"] / 100
                                for i in range(n_foods)
                            )
                            - min_fats,
                        },
                        {
                            "type": "ineq",
                            "fun": lambda x: max_fats
                            - sum(
                                x[i] * foods[i]["fats_per_100g"] / 100
                                for i in range(n_foods)
                            ),
                        },
                    ]
                )

            # Bounds for each food
            bounds = []
            for food in foods:
                min_val = food["min"] if food["min"] is not None else 0
                max_val = food["max"] if food["max"] is not None else None
                bounds.append((min_val, max_val))

            # Solve optimization problem
            result = minimize(
                objective, x0, method="SLSQP", constraints=constraints, bounds=bounds
            )

            if not result.success:
                error_msg = "Não foi possível encontrar uma solução com as restrições fornecidas.\n"
                error_msg += f"Tolerância atual: ±{tolerance * 100:.0f}%. Tente aumentar a tolerância ou ajustar os limites dos alimentos."

                # Check which targets can't be met
                impossible_targets = []
                for nutrient, target in targets.items():
                    if target > 0:
                        min_value = sum(
                            (food["min"] if food["min"] is not None else 0)
                            * food[f"{nutrient}_per_100g"]
                            / 100
                            for food in foods
                        )
                        max_value = sum(
                            (food["max"] if food["max"] is not None else float("inf"))
                            * food[f"{nutrient}_per_100g"]
                            / 100
                            for food in foods
                        )

                        target_min = target * (1 - tolerance)
                        target_max = target * (1 + tolerance)

                        if target_min < min_value:
                            impossible_targets.append(
                                f"{nutrient.title()}: o mínimo possível ({min_value:.1f}) é maior que o alvo mínimo ({target_min:.1f})"
                            )
                        elif max_value < float("inf") and target_max > max_value:
                            impossible_targets.append(
                                f"{nutrient.title()}: o máximo possível ({max_value:.1f}) é menor que o alvo máximo ({target_max:.1f})"
                            )

                if impossible_targets:
                    error_msg += "\n\nValores impossíveis de atingir:\n" + "\n".join(
                        impossible_targets
                    )

                return jsonify({"success": False, "error": error_msg}), 400

            # Prepare portions data
            portions = []
            for i, food in enumerate(foods):
                quantity = float(result.x[i])
                portion = {
                    "food_code": food["code"],
                    "quantity": quantity,
                    "calories": quantity * food["calories_per_100g"] / 100,
                    "proteins": quantity * food["proteins_per_100g"] / 100,
                    "carbs": quantity * food["carbs_per_100g"] / 100,
                    "fats": quantity * food["fats_per_100g"] / 100,
                }
                portions.append(portion)

            return jsonify({"success": True, "portions": portions})

        except ImportError:
            return jsonify(
                {
                    "success": False,
                    "error": "Required optimization package not available",
                }
            ), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/export_diet", methods=["POST"])
@login_required
def export_diet():
    try:
        # Get the diet data from the request
        meals_data = request.get_json()

        # Create a BytesIO object to store the Excel file
        excel_file = BytesIO()

        # Create an Excel writer object
        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
            # Use MEAL_TYPES from constants
            meal_names = MEAL_TYPES

            # Create summary DataFrame
            summary_data = {
                "Informações do Usuário": [
                    f"Nome: {current_user.nome}",
                    f"Idade: {current_user.idade} anos",
                    f"Altura: {current_user.altura} cm",
                    f"Peso: {current_user.peso} kg",
                    f"Sexo: {'Masculino' if current_user.sexo == 'M' else 'Feminino'}",
                    f"Data: {datetime.now().strftime('%d/%m/%Y')}",
                    "",  # Empty row for spacing
                    "Resumo por Refeição:",
                ]
            }

            # Calculate totals for each meal
            meal_totals = []
            for meal_type, foods in meals_data.items():
                if not foods:
                    continue

                meal_name = meal_names.get(meal_type, meal_type)
                total_calories = sum(food.get("calories", 0) for food in foods)
                total_proteins = sum(food.get("proteins", 0) for food in foods)
                total_carbs = sum(food.get("carbs", 0) for food in foods)
                total_fats = sum(food.get("fats", 0) for food in foods)

                meal_totals.append(
                    {
                        "Refeição": meal_name,
                        "Calorias": total_calories,
                        "Proteínas (g)": total_proteins,
                        "Carboidratos (g)": total_carbs,
                        "Gorduras (g)": total_fats,
                    }
                )

            # Create summary sheet
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Resumo", index=False)

            # Add meal totals table to summary sheet
            if meal_totals:
                totals_df = pd.DataFrame(meal_totals)
                # Add daily totals row
                daily_totals = {
                    "Refeição": "Total Diário",
                    "Calorias": sum(float(m["Calorias"]) for m in meal_totals),
                    "Proteínas (g)": sum(
                        float(m["Proteínas (g)"]) for m in meal_totals
                    ),
                    "Carboidratos (g)": sum(
                        float(m["Carboidratos (g)"]) for m in meal_totals
                    ),
                    "Gorduras (g)": sum(float(m["Gorduras (g)"]) for m in meal_totals),
                }
                totals_df = pd.concat([totals_df, pd.DataFrame([daily_totals])])
                totals_df.to_excel(
                    writer, sheet_name="Resumo", startrow=10, index=False
                )

            # Format summary sheet
            worksheet = writer.sheets["Resumo"]
            for idx in range(1, 20):  # Adjust column widths
                worksheet.column_dimensions[chr(64 + idx)].width = 20

            # Create individual meal sheets
            for meal_type, foods in meals_data.items():
                if not foods:  # Skip empty meals
                    continue

                # Convert the foods list to a DataFrame
                df = pd.DataFrame(foods)

                # Rename columns to Portuguese
                df = df.rename(
                    columns={
                        "food_code": "Alimento",
                        "quantity": "Quantidade (g)",
                        "calories": "Calorias",
                        "proteins": "Proteínas (g)",
                        "carbs": "Carboidratos (g)",
                        "fats": "Gorduras (g)",
                    }
                )
                df.drop("id", axis=1, inplace=True)

                # Write the DataFrame to a sheet
                sheet_name = meal_names.get(meal_type, meal_type)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Get the worksheet to adjust column widths
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df.columns):
                    # Calculate max width needed
                    max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                    # Set column width
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length

        # Seek to the beginning of the file
        excel_file.seek(0)

        # Return the file
        return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"dieta_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/diets", methods=["POST"])
@login_required
def create_diet():
    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"error": "Nome da dieta é obrigatório"}), 400

    diet = Diet(name=name, user_id=current_user.id)
    db.session.add(diet)
    db.session.commit()

    return jsonify({"success": True, "name": diet.name})


@bp.route("/diets/<int:diet_id>", methods=["PUT"])
@login_required
def update_diet(diet_id):
    diet = Diet.query.get_or_404(diet_id)
    if diet.user_id != current_user.id:
        return jsonify({"error": "Não autorizado"}), 403

    data = request.get_json()
    name = data.get("name")

    if name:
        diet.name = name
        db.session.commit()

    return jsonify({"success": True, "name": diet.name})


@bp.route("/last_diet")
@login_required
def last_diet():
    """Retorna a dieta mais recente do usuário logado"""
    diet = (
        Diet.query.filter_by(user_id=current_user.id)
        .order_by(Diet.created_at.desc())
        .first()
    )
    if diet:
        return jsonify(
            {
                "success": True,
                "id": diet.id,
                "name": diet.name,
                "meals_data": diet.meals_data,
            }
        )
    # Nenhuma dieta salva ainda
    return jsonify({"success": False, "error": "Nenhuma dieta encontrada"})


@bp.route("/chatbot", methods=["POST"])
@login_required
def chatbot():
    from openai import OpenAI

    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Mensagem não fornecida"}), 400

    # Use dados do usuário
    user = current_user
    user_profile = {
        "nome": user.nome,
        "idade": user.idade,
        "peso": user.peso,
        "altura": user.altura,
        "objetivo": user.get_objetivo_display(),
        "atividade": user.get_fator_atividade_display(),
    }

    prompt = f"""
    O usuário deseja orientação nutricional. Perfil:
    - Nome: {user_profile["nome"]}
    - Idade: {user_profile["idade"]}
    - Peso: {user_profile["peso"]} kg
    - Altura: {user_profile["altura"]} m
    - Objetivo: {user_profile["objetivo"]}
    - Nível de atividade: {user_profile["atividade"]}

    Pergunta do usuário: "{user_message}"
    """

    # Chamada à API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return jsonify({"response": response["choices"][0]["message"]["content"]})
