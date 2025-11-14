from flask import jsonify, request, send_file
from flask_login import login_required, current_user
from app import db
from app.blueprints.api import bp
from app.models import Diet, FoodData, UserFood
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

    # Search in FoodData (global foods)
    foods_start = (
        FoodData.query.filter(FoodData.code.ilike(f"{query}%")).limit(10).all()
    )

    if len(foods_start) < 10:
        start_ids = [food.id for food in foods_start]
        query_obj = FoodData.query.filter(FoodData.code.ilike(f"%{query}%"))
        if start_ids:
            query_obj = query_obj.filter(~FoodData.id.in_(start_ids))
        additional_foods = query_obj.limit(10 - len(foods_start)).all()
        foods = foods_start + additional_foods
    else:
        foods = foods_start
    
    # Search in UserFood (user's custom foods)
    user_foods_start = (
        UserFood.query.filter(
            UserFood.user_id == current_user.id,
            UserFood.code.ilike(f"{query}%")
        ).limit(10).all()
    )
    
    if len(user_foods_start) < 10:
        user_start_ids = [food.id for food in user_foods_start]
        user_query_obj = UserFood.query.filter(
            UserFood.user_id == current_user.id,
            UserFood.code.ilike(f"%{query}%")
        )
        if user_start_ids:
            user_query_obj = user_query_obj.filter(~UserFood.id.in_(user_start_ids))
        additional_user_foods = user_query_obj.limit(10 - len(user_foods_start)).all()
        user_foods = user_foods_start + additional_user_foods
    else:
        user_foods = user_foods_start
    
    # Combine results (limit to 10 total)
    all_foods = foods + user_foods
    
    # Deduplicate by food_code
    seen_codes = set()
    unique_foods = []
    for food in all_foods[:10]:
        if food.code not in seen_codes:
            seen_codes.add(food.code)
            unique_foods.append(food)
    
    return jsonify([{"food_code": food.code, "qtd": food.quantity} for food in unique_foods])


@bp.route("/food_nutrition/<code>")
@login_required
def get_food_nutrition(code):
    try:
        # First try to find in user's custom foods
        user_food = UserFood.query.filter_by(
            code=code, user_id=current_user.id
        ).first()
        
        if user_food:
            quantity = float(request.args.get("quantity", user_food.quantity))
            ratio = quantity / user_food.quantity
            return jsonify(
                {
                    "success": True,
                    "food_code": user_food.code,
                    "calories": user_food.calories * ratio,
                    "proteins": user_food.proteins * ratio,
                    "carbs": user_food.carbs * ratio,
                    "fats": user_food.fats * ratio,
                    "quantity": quantity,
                }
            )
        
        # If not found in custom foods, try global foods
        food = FoodData.query.filter_by(code=code).first()
        if food:
            quantity = float(request.args.get("quantity", food.quantity))
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

        # First try to find in user's custom foods
        user_food = UserFood.query.filter_by(
            code=code, user_id=current_user.id
        ).first()
        
        if user_food:
            # Calculate nutrition values based on quantity
            ratio = quantity / user_food.quantity
            nutrition = {
                "calories": user_food.calories * ratio,
                "proteins": user_food.proteins * ratio,
                "carbs": user_food.carbs * ratio,
                "fats": user_food.fats * ratio,
            }
            
            return jsonify(
                {
                    "success": True,
                    "food": {
                        "id": user_food.id,
                        "food_code": user_food.code,
                        "quantity": quantity,
                        **nutrition,
                    },
                }
            )
        
        # If not found in custom foods, try global foods
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
    """Salva uma dieta modelo (sem data)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        name = data.get("name")
        meals_data = data.get("meals_data")
        diet_id = request.args.get("diet_id")  # Para atualizar dieta modelo existente
        
        if not name or not meals_data:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        if diet_id:
            # Atualiza dieta modelo existente
            diet = Diet.query.filter_by(
                id=diet_id, 
                user_id=current_user.id,
                date=None  # Apenas dietas modelo
            ).first_or_404()
            diet.name = name
            diet.meals_data = meals_data
            diet.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                "success": True, 
                "message": "Dieta modelo atualizada com sucesso!",
                "diet_id": diet.id
            })
        else:
            # Cria nova dieta modelo (sem data)
            diet = Diet(
                name=name, 
                user_id=current_user.id, 
                date=None,  # NULL = dieta modelo
                meals_data=meals_data
            )
            db.session.add(diet)
            db.session.commit()
            return jsonify({
                "success": True, 
                "message": "Dieta modelo salva com sucesso!",
                "diet_id": diet.id
            })
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error saving diet template: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/save_daily_diet", methods=["POST"])
@login_required
def save_daily_diet():
    """Salva uma dieta do dia (com data específica)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        name = data.get("name")
        meals_data = data.get("meals_data")
        diet_date_str = data.get("date")  # Data no formato YYYY-MM-DD
        
        if not name or not meals_data or not diet_date_str:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Parse da data
        from datetime import datetime as dt
        diet_date = dt.strptime(diet_date_str, "%Y-%m-%d").date()

        # Verifica se já existe dieta para esta data
        existing_diet = Diet.query.filter_by(
            user_id=current_user.id,
            date=diet_date
        ).first()

        if existing_diet:
            # Atualiza dieta existente para esta data
            existing_diet.name = name
            existing_diet.meals_data = meals_data
            existing_diet.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                "success": True, 
                "message": "Registro atualizado no diário com sucesso!",
                "diet_id": existing_diet.id,
                "date": existing_diet.date.isoformat()
            })
        else:
            # Cria nova dieta para esta data
            diet = Diet(
                name=name, 
                user_id=current_user.id, 
                date=diet_date,
                meals_data=meals_data
            )
            db.session.add(diet)
            db.session.commit()
            return jsonify({
                "success": True, 
                "message": "Registro salvo no diário com sucesso!",
                "diet_id": diet.id,
                "date": diet.date.isoformat()
            })
    except Exception as e:
        db.session.rollback()
        import traceback
        from sqlalchemy.exc import IntegrityError
        
        # Tratamento específico para violação de constraint único
        if isinstance(e, IntegrityError):
            # Se houver violação do constraint único, tenta atualizar o registro existente
            try:
                existing_diet = Diet.query.filter_by(
                    user_id=current_user.id,
                    date=diet_date
                ).first()
                if existing_diet:
                    existing_diet.name = name
                    existing_diet.meals_data = meals_data
                    existing_diet.updated_at = datetime.utcnow()
                    db.session.commit()
                    return jsonify({
                        "success": True, 
                        "message": "Registro atualizado no diário com sucesso!",
                        "diet_id": existing_diet.id,
                        "date": existing_diet.date.isoformat()
                    })
            except Exception as e2:
                pass
        
        print(f"Error saving daily diet: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/load_diet/<int:diet_id>")
@login_required
def load_diet(diet_id):
    """Carrega dieta por ID (mantido para compatibilidade)"""
    try:
        diet = Diet.query.filter_by(id=diet_id, user_id=current_user.id).first_or_404()
        return jsonify(
            {
                "success": True, 
                "name": diet.name, 
                "meals_data": diet.meals_data,
                "date": diet.date.isoformat() if diet.date else None
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/load_diet_by_date", methods=["GET"])
@login_required
def load_diet_by_date():
    """Carrega dieta por data"""
    try:
        date_str = request.args.get("date")
        if not date_str:
            return jsonify({"success": False, "error": "Data não fornecida"}), 400
        
        from datetime import datetime as dt
        diet_date = dt.strptime(date_str, "%Y-%m-%d").date()
        
        diet = Diet.query.filter_by(
            user_id=current_user.id,
            date=diet_date
        ).first()
        
        if diet:
            return jsonify({
                "success": True,
                "name": diet.name,
                "meals_data": diet.meals_data,
                "date": diet.date.isoformat(),
                "diet_id": diet.id
            })
        else:
            # Não é um erro - simplesmente não há diário para esta data
            return jsonify({
                "success": True,
                "meals_data": {},
                "message": "Nenhum diário encontrado para esta data"
            })
    except ValueError:
        return jsonify({"success": False, "error": "Formato de data inválido. Use YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/list_diets", methods=["GET"])
@login_required
def list_diets():
    """Lista todas as dietas modelo do usuário (sem data)"""
    try:
        diets = Diet.query.filter_by(
            user_id=current_user.id,
            date=None  # Apenas dietas modelo
        ).order_by(Diet.created_at.desc()).all()
        
        diets_list = [{
            "id": diet.id,
            "name": diet.name,
            "created_at": diet.created_at.isoformat() if diet.created_at else None,
            "is_template": True
        } for diet in diets]
        
        return jsonify({
            "success": True,
            "diets": diets_list
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/list_daily_diets", methods=["GET"])
@login_required
def list_daily_diets():
    """Lista todas as dietas do dia do usuário ordenadas por data"""
    try:
        diets = Diet.query.filter(
            Diet.user_id == current_user.id,
            Diet.date.isnot(None)  # Apenas dietas do dia
        ).order_by(Diet.date.desc()).all()
        
        diets_list = [{
            "id": diet.id,
            "name": diet.name,
            "date": diet.date.isoformat() if diet.date else None,
            "created_at": diet.created_at.isoformat() if diet.created_at else None,
            "is_template": False
        } for diet in diets]
        
        return jsonify({
            "success": True,
            "diets": diets_list
        })
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
            code = food_item["code"]
            
            # First try to find in user's custom foods
            user_food = UserFood.query.filter_by(
                code=code, user_id=current_user.id
            ).first()
            
            if user_food:
                foods.append(
                    {
                        "code": user_food.code,
                        "calories_per_100g": 100 * user_food.calories / user_food.quantity,
                        "proteins_per_100g": 100 * user_food.proteins / user_food.quantity,
                        "carbs_per_100g": 100 * user_food.carbs / user_food.quantity,
                        "fats_per_100g": 100 * user_food.fats / user_food.quantity,
                        "min": food_item.get("min"),
                        "max": food_item.get("max"),
                    }
                )
                continue
            
            # If not found in custom foods, try global foods
            food = FoodData.query.filter_by(code=code).first()
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
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Nenhum dado de refeição fornecido"}), 400
        
        meals_data = data.get("meals_data", data)  # Backward compatibility
        date_str = data.get("date")
        
        # Parse the date if provided, otherwise use today
        from datetime import datetime as dt
        if date_str:
            try:
                export_date = dt.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                export_date = datetime.now().date()
        else:
            export_date = datetime.now().date()

        # Create a BytesIO object to store the Excel file
        excel_file = BytesIO()

        # Create an Excel writer object
        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
            # Use MEAL_TYPES from constants
            meal_names = MEAL_TYPES

            # Create summary DataFrame
            # Get user info safely (handle missing attributes)
            user_name = getattr(current_user, 'nome', None) or getattr(current_user, 'username', 'Usuário')
            user_age = getattr(current_user, 'idade', None)
            user_height = getattr(current_user, 'altura', None)
            user_weight = getattr(current_user, 'peso', None)
            user_sex = getattr(current_user, 'sexo', None)
            
            user_info = [f"Usuário: {user_name}"]
            if user_age:
                user_info.append(f"Idade: {user_age} anos")
            if user_height:
                user_info.append(f"Altura: {user_height} cm")
            if user_weight:
                user_info.append(f"Peso: {user_weight} kg")
            if user_sex:
                user_info.append(f"Sexo: {'Masculino' if user_sex == 'M' else 'Feminino'}")
            
            user_info.extend([
                f"Data: {export_date.strftime('%d/%m/%Y')}",
                "",  # Empty row for spacing
                "Resumo por Refeição:",
            ])
            
            summary_data = {
                "Informações do Usuário": user_info
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
                
                # Ensure required columns exist, fill missing ones with empty values
                required_cols = {
                    "food_code": "Alimento",
                    "quantity": "Quantidade (g)",
                    "calories": "Calorias",
                    "proteins": "Proteínas (g)",
                    "carbs": "Carboidratos (g)",
                    "fats": "Gorduras (g)",
                }
                
                # Add missing columns with default values
                for col in required_cols.keys():
                    if col not in df.columns:
                        df[col] = 0 if col != "food_code" else ""

                # Rename columns to Portuguese
                df = df.rename(columns=required_cols)
                
                # Drop 'id' column if it exists
                if "id" in df.columns:
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
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error exporting diet: {error_trace}")
        return jsonify({"error": f"Erro ao exportar dieta: {str(e)}"}), 500


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


@bp.route("/user_foods", methods=["GET"])
@login_required
def list_user_foods():
    """Lista todos os alimentos personalizados do usuário"""
    try:
        foods = UserFood.query.filter_by(user_id=current_user.id).order_by(UserFood.code).all()
        return jsonify({
            "success": True,
            "foods": [{
                "id": food.id,
                "code": food.code,
                "name": food.name,
                "quantity": food.quantity,
                "calories": food.calories,
                "proteins": food.proteins,
                "carbs": food.carbs,
                "fats": food.fats,
                "created_at": food.created_at.isoformat() if food.created_at else None,
            } for food in foods]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/user_foods", methods=["POST"])
@login_required
def create_user_food():
    """Cria um novo alimento personalizado"""
    try:
        data = request.get_json()
        
        code = data.get("code", "").strip()
        name = data.get("name", "").strip()
        quantity = data.get("quantity")
        proteins = data.get("proteins")
        carbs = data.get("carbs")
        fats = data.get("fats")
        
        # Validação: pelo menos um dos dois (código ou nome) deve ser preenchido
        if not code and not name:
            return jsonify({
                "success": False,
                "error": "Por favor, preencha pelo menos o código ou o nome do alimento"
            }), 400
        
        # Se não tiver código, usa o nome como código
        if not code:
            code = name
        # Se não tiver nome, usa o código como nome
        if not name:
            name = code
        
        # Validação dos campos obrigatórios
        if quantity is None or proteins is None or carbs is None or fats is None:
            return jsonify({
                "success": False,
                "error": "Quantidade, proteínas, carboidratos e gorduras são obrigatórios"
            }), 400
        
        if quantity <= 0:
            return jsonify({
                "success": False,
                "error": "A quantidade deve ser maior que zero"
            }), 400
        
        # Calcula calorias automaticamente: Calorias = 4 × Proteínas + 4 × Carboidratos + 9 × Gorduras
        calories = (4 * float(proteins)) + (4 * float(carbs)) + (9 * float(fats))
        
        # Verifica se já existe um alimento com o mesmo código para este usuário
        existing = UserFood.query.filter_by(
            user_id=current_user.id,
            code=code
        ).first()
        
        if existing:
            return jsonify({
                "success": False,
                "error": f"Já existe um alimento com o código '{code}'"
            }), 400
        
        # Cria o alimento
        user_food = UserFood(
            user_id=current_user.id,
            code=code,
            name=name,
            quantity=float(quantity),
            calories=round(calories, 1),
            proteins=float(proteins),
            carbs=float(carbs),
            fats=float(fats)
        )
        
        db.session.add(user_food)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Alimento criado com sucesso!",
            "food": {
                "id": user_food.id,
                "code": user_food.code,
                "name": user_food.name,
                "quantity": user_food.quantity,
                "calories": user_food.calories,
                "proteins": user_food.proteins,
                "carbs": user_food.carbs,
                "fats": user_food.fats,
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/user_foods/<int:food_id>", methods=["PUT"])
@login_required
def update_user_food(food_id):
    """Atualiza um alimento personalizado"""
    try:
        food = UserFood.query.filter_by(
            id=food_id,
            user_id=current_user.id
        ).first_or_404()
        
        data = request.get_json()
        
        code = data.get("code", "").strip()
        name = data.get("name", "").strip()
        quantity = data.get("quantity")
        proteins = data.get("proteins")
        carbs = data.get("carbs")
        fats = data.get("fats")
        
        # Validação: pelo menos um dos dois (código ou nome) deve ser preenchido
        if not code and not name:
            return jsonify({
                "success": False,
                "error": "Por favor, preencha pelo menos o código ou o nome do alimento"
            }), 400
        
        # Se não tiver código, usa o nome como código
        if not code:
            code = name
        # Se não tiver nome, usa o código como nome
        if not name:
            name = code
        
        # Validação dos campos obrigatórios
        if quantity is None or proteins is None or carbs is None or fats is None:
            return jsonify({
                "success": False,
                "error": "Quantidade, proteínas, carboidratos e gorduras são obrigatórios"
            }), 400
        
        if quantity <= 0:
            return jsonify({
                "success": False,
                "error": "A quantidade deve ser maior que zero"
            }), 400
        
        # Calcula calorias automaticamente: Calorias = 4 × Proteínas + 4 × Carboidratos + 9 × Gorduras
        calories = (4 * float(proteins)) + (4 * float(carbs)) + (9 * float(fats))
        
        # Verifica se o código já existe em outro alimento do mesmo usuário
        if code != food.code:
            existing = UserFood.query.filter_by(
                user_id=current_user.id,
                code=code
            ).first()
            
            if existing:
                return jsonify({
                    "success": False,
                    "error": f"Já existe um alimento com o código '{code}'"
                }), 400
        
        # Atualiza o alimento
        food.code = code
        food.name = name
        food.quantity = float(quantity)
        food.calories = round(calories, 1)
        food.proteins = float(proteins)
        food.carbs = float(carbs)
        food.fats = float(fats)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Alimento atualizado com sucesso!",
            "food": {
                "id": food.id,
                "code": food.code,
                "name": food.name,
                "quantity": food.quantity,
                "calories": food.calories,
                "proteins": food.proteins,
                "carbs": food.carbs,
                "fats": food.fats,
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/user_foods/<int:food_id>", methods=["DELETE"])
@login_required
def delete_user_food(food_id):
    """Deleta um alimento personalizado"""
    try:
        food = UserFood.query.filter_by(
            id=food_id,
            user_id=current_user.id
        ).first_or_404()
        
        db.session.delete(food)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Alimento deletado com sucesso!"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


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
