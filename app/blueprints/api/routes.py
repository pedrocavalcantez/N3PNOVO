from flask import jsonify, request, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.blueprints.api import bp
from app.models import Diet, FoodData, UserFood
from datetime import datetime
import pandas as pd
from io import BytesIO
from app.constants import MEAL_TYPES


@bp.route("/search_food")
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

    # Search in UserFood (user's custom foods) - only if user is authenticated
    user_foods = []
    if current_user.is_authenticated:
        user_foods_start = (
            UserFood.query.filter(
                UserFood.user_id == current_user.id, UserFood.code.ilike(f"{query}%")
            )
            .limit(10)
            .all()
        )

        if len(user_foods_start) < 10:
            user_start_ids = [food.id for food in user_foods_start]
            user_query_obj = UserFood.query.filter(
                UserFood.user_id == current_user.id, UserFood.code.ilike(f"%{query}%")
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

    return jsonify(
        [{"food_code": food.code, "qtd": food.quantity} for food in unique_foods]
    )


@bp.route("/food_nutrition", methods=["GET"])
def get_food_nutrition():
    try:
        # Obtém o código do alimento do query parameter
        code = request.args.get("code")
        if not code:
            return jsonify(
                {"success": False, "error": "Código do alimento não fornecido"}
            ), 400

        # First try to find in user's custom foods (only if authenticated)
        user_food = None
        if current_user.is_authenticated:
            user_food = UserFood.query.filter_by(code=code, user_id=current_user.id).first()

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

        # First try to find in user's custom foods (only if authenticated)
        user_food = None
        if current_user.is_authenticated:
            user_food = UserFood.query.filter_by(code=code, user_id=current_user.id).first()

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
def delete_food(food_id):
    try:
        # In this case, we don't actually delete from the database
        # since we're just removing from the UI
        # Works for both authenticated and guest users
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
                date=None,  # Apenas dietas modelo
            ).first_or_404()
            diet.name = name
            diet.meals_data = meals_data
            diet.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify(
                {
                    "success": True,
                    "message": "Dieta modelo atualizada com sucesso!",
                    "diet_id": diet.id,
                }
            )
        else:
            # Cria nova dieta modelo (sem data)
            diet = Diet(
                name=name,
                user_id=current_user.id,
                date=None,  # NULL = dieta modelo
                meals_data=meals_data,
            )
            db.session.add(diet)
            db.session.commit()
            return jsonify(
                {
                    "success": True,
                    "message": "Dieta modelo salva com sucesso!",
                    "diet_id": diet.id,
                }
            )
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
            user_id=current_user.id, date=diet_date
        ).first()

        if existing_diet:
            # Atualiza dieta existente para esta data
            existing_diet.name = name
            existing_diet.meals_data = meals_data
            existing_diet.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify(
                {
                    "success": True,
                    "message": "Registro atualizado no diário com sucesso!",
                    "diet_id": existing_diet.id,
                    "date": existing_diet.date.isoformat(),
                }
            )
        else:
            # Cria nova dieta para esta data
            diet = Diet(
                name=name,
                user_id=current_user.id,
                date=diet_date,
                meals_data=meals_data,
            )
            db.session.add(diet)
            db.session.commit()
            return jsonify(
                {
                    "success": True,
                    "message": "Registro salvo no diário com sucesso!",
                    "diet_id": diet.id,
                    "date": diet.date.isoformat(),
                }
            )
    except Exception as e:
        db.session.rollback()
        import traceback
        from sqlalchemy.exc import IntegrityError

        # Tratamento específico para violação de constraint único
        if isinstance(e, IntegrityError):
            # Se houver violação do constraint único, tenta atualizar o registro existente
            try:
                existing_diet = Diet.query.filter_by(
                    user_id=current_user.id, date=diet_date
                ).first()
                if existing_diet:
                    existing_diet.name = name
                    existing_diet.meals_data = meals_data
                    existing_diet.updated_at = datetime.utcnow()
                    db.session.commit()
                    return jsonify(
                        {
                            "success": True,
                            "message": "Registro atualizado no diário com sucesso!",
                            "diet_id": existing_diet.id,
                            "date": existing_diet.date.isoformat(),
                        }
                    )
            except Exception:
                pass

        print(f"Error saving daily diet: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/add_recommendation_to_diary", methods=["POST"])
@login_required
def add_recommendation_to_diary():
    """Adiciona uma recomendação do chatbot ao diário do dia"""
    try:
        from datetime import date

        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        meals_data = data.get("meals_data")  # Formato: {meal_type: [foods]}
        target_date_str = data.get(
            "date"
        )  # Data no formato YYYY-MM-DD (opcional, usa hoje se não fornecido)

        if not meals_data:
            return jsonify({"success": False, "error": "Meals data is required"}), 400

        # Determinar data (hoje por padrão)
        if target_date_str:
            from datetime import datetime as dt

            try:
                target_date = dt.strptime(target_date_str, "%Y-%m-%d").date()
            except ValueError:
                target_date = date.today()
        else:
            target_date = date.today()

        # Buscar ou criar dieta do dia
        daily_diet = Diet.query.filter_by(
            user_id=current_user.id, date=target_date
        ).first()

        # Preparar dados de refeições
        # meals_data vem no formato: {meal_type: [foods]}
        # Precisamos mesclar com dados existentes
        existing_meals = {}
        if daily_diet and daily_diet.meals_data:
            # Fazer uma cópia profunda para não modificar o original
            import copy

            existing_meals = copy.deepcopy(daily_diet.meals_data)
            print(f"📋 Carregando diário existente com {len(existing_meals)} refeições")
            for meal_type, foods in existing_meals.items():
                print(f"   - {meal_type}: {len(foods)} alimento(s) existente(s)")

        # Importar modelos necessários para buscar valores nutricionais
        from app.models import FoodData, UserFood

        # Adicionar novos alimentos às refeições existentes
        foods_not_found = []  # Lista de alimentos não encontrados para debug

        for meal_type, foods in meals_data.items():
            if meal_type not in existing_meals:
                existing_meals[meal_type] = []

            # Adicionar novos alimentos (evitar duplicatas se necessário)
            for food in foods:
                # Verificar se já existe (por código e quantidade similar)
                food_code = food.get("code")
                food_quantity = float(food.get("quantity", 0))

                # Adicionar o alimento
                # Usar food_code ou code (dependendo do formato recebido)
                food_code_to_use = (
                    food.get("food_code") or food.get("code") or food_code
                )

                if not food_code_to_use:
                    foods_not_found.append(
                        f"Alimento sem código na refeição {meal_type}"
                    )
                    continue

                # Buscar valores nutricionais do banco de dados baseado no código do alimento
                # Isso garante que os valores estão corretos mesmo se o chatbot fornecer valores incorretos
                calories = food.get("calories", 0)
                proteins = food.get("proteins", 0)
                carbs = food.get("carbs", 0)
                fats = food.get("fats", 0)

                # Sempre buscar do banco de dados quando houver um código válido
                food_found = False
                if food_code_to_use:
                    # Primeiro tentar buscar nos alimentos personalizados do usuário
                    user_food = UserFood.query.filter_by(
                        code=food_code_to_use, user_id=current_user.id
                    ).first()

                    if user_food:
                        food_found = True
                        # Calcular valores nutricionais baseado na quantidade
                        if user_food.quantity > 0 and food_quantity > 0:
                            ratio = food_quantity / user_food.quantity
                            calories = user_food.calories * ratio
                            proteins = user_food.proteins * ratio
                            carbs = user_food.carbs * ratio
                            fats = user_food.fats * ratio
                    else:
                        # Se não encontrou nos alimentos personalizados, buscar nos alimentos globais
                        food_data = FoodData.query.filter_by(
                            code=food_code_to_use
                        ).first()
                        if food_data:
                            food_found = True
                            # Calcular valores nutricionais baseado na quantidade
                            if food_data.quantity > 0 and food_quantity > 0:
                                ratio = food_quantity / food_data.quantity
                                calories = food_data.calories * ratio
                                proteins = food_data.proteins * ratio
                                carbs = food_data.carbs * ratio
                                fats = food_data.fats * ratio

                if not food_found:
                    foods_not_found.append(
                        f"Alimento com código '{food_code_to_use}' não encontrado no banco de dados"
                    )
                    # Continuar mesmo assim, usando os valores fornecidos pelo chatbot
                    print(
                        f"AVISO: Alimento '{food_code_to_use}' não encontrado no banco de dados. Usando valores fornecidos pelo chatbot."
                    )

                existing_meals[meal_type].append(
                    {
                        "food_code": food_code_to_use,
                        "quantity": food_quantity,
                        "calories": float(calories),
                        "proteins": float(proteins),
                        "carbs": float(carbs),
                        "fats": float(fats),
                    }
                )

        # Salvar ou atualizar dieta
        if daily_diet:
            daily_diet.meals_data = existing_meals
            daily_diet.updated_at = datetime.utcnow()
            if not daily_diet.name:
                daily_diet.name = (
                    f"Registro do Dia - {target_date.strftime('%d/%m/%Y')}"
                )
        else:
            daily_diet = Diet(
                name=f"Registro do Dia - {target_date.strftime('%d/%m/%Y')}",
                user_id=current_user.id,
                date=target_date,
                meals_data=existing_meals,
            )
            db.session.add(daily_diet)

        # Fazer flush antes do commit para garantir que os dados sejam persistidos
        db.session.flush()

        # Fazer commit e garantir que foi salvo
        db.session.commit()

        # Verificar se foi salvo corretamente fazendo uma nova query
        # Expirar a sessão para forçar uma nova leitura do banco
        db.session.expire_all()
        verification = Diet.query.filter_by(
            user_id=current_user.id, date=target_date
        ).first()

        # Log para debug
        print(f"✅ Diário atualizado com sucesso para a data {target_date}")
        print(f"   Diet ID: {daily_diet.id}")
        print(f"   Total de refeições: {len(existing_meals)}")
        for meal_type, foods in existing_meals.items():
            print(f"   - {meal_type}: {len(foods)} alimento(s)")

        if verification:
            print(
                f"   ✅ Verificação: Diário encontrado no banco com {len(verification.meals_data or {})} refeições"
            )
        else:
            print("   ⚠️ AVISO: Diário não encontrado na verificação!")

        response_data = {
            "success": True,
            "message": "Recomendação adicionada ao diário com sucesso!",
            "date": target_date.isoformat(),
            "diet_id": daily_diet.id,
            "meals_count": len(existing_meals),
            "total_foods": sum(len(foods) for foods in existing_meals.values()),
        }

        # Adicionar avisos se houver alimentos não encontrados
        if foods_not_found:
            response_data["warnings"] = foods_not_found
            print(f"AVISOS ao adicionar recomendação: {foods_not_found}")

        return jsonify(response_data)

    except Exception as e:
        db.session.rollback()
        import traceback

        error_trace = traceback.format_exc()
        print(f"Error adding recommendation to diary: {error_trace}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "details": error_trace if current_app.debug else None,
            }
        ), 500


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
                "date": diet.date.isoformat() if diet.date else None,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/load_diet_by_date", methods=["GET"])
@login_required
def load_diet_by_date():
    """Carrega dieta por data"""
    try:
        # Forçar expiração de cache da sessão para garantir dados frescos
        db.session.expire_all()

        date_str = request.args.get("date")
        if not date_str:
            return jsonify({"success": False, "error": "Data não fornecida"}), 400

        from datetime import datetime as dt

        diet_date = dt.strptime(date_str, "%Y-%m-%d").date()

        diet = Diet.query.filter_by(user_id=current_user.id, date=diet_date).first()

        if diet:
            return jsonify(
                {
                    "success": True,
                    "name": diet.name,
                    "meals_data": diet.meals_data,
                    "date": diet.date.isoformat(),
                    "diet_id": diet.id,
                }
            )
        else:
            # Não é um erro - simplesmente não há diário para esta data
            return jsonify(
                {
                    "success": True,
                    "meals_data": {},
                    "message": "Nenhum diário encontrado para esta data",
                }
            )
    except ValueError:
        return jsonify(
            {"success": False, "error": "Formato de data inválido. Use YYYY-MM-DD"}
        ), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/list_diets", methods=["GET"])
@login_required
def list_diets():
    """Lista todas as dietas modelo do usuário (sem data)"""
    try:
        diets = (
            Diet.query.filter_by(
                user_id=current_user.id,
                date=None,  # Apenas dietas modelo
            )
            .order_by(Diet.created_at.desc())
            .all()
        )

        diets_list = [
            {
                "id": diet.id,
                "name": diet.name,
                "created_at": diet.created_at.isoformat() if diet.created_at else None,
                "is_template": True,
            }
            for diet in diets
        ]

        return jsonify({"success": True, "diets": diets_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/list_daily_diets", methods=["GET"])
@login_required
def list_daily_diets():
    """Lista todas as dietas do dia do usuário ordenadas por data"""
    try:
        diets = (
            Diet.query.filter(
                Diet.user_id == current_user.id,
                Diet.date.isnot(None),  # Apenas dietas do dia
            )
            .order_by(Diet.date.desc())
            .all()
        )

        diets_list = [
            {
                "id": diet.id,
                "name": diet.name,
                "date": diet.date.isoformat() if diet.date else None,
                "created_at": diet.created_at.isoformat() if diet.created_at else None,
                "is_template": False,
            }
            for diet in diets
        ]

        return jsonify({"success": True, "diets": diets_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/delete_diary_by_date", methods=["DELETE"])
@login_required
def delete_diary_by_date():
    """Deleta um diário pela data"""
    try:
        date_str = request.args.get("date")
        if not date_str:
            return jsonify({"success": False, "error": "Data não fornecida"}), 400

        from datetime import datetime as dt

        diet_date = dt.strptime(date_str, "%Y-%m-%d").date()

        # Busca o diário do usuário para esta data
        diet = Diet.query.filter_by(user_id=current_user.id, date=diet_date).first()

        if not diet:
            return jsonify({"success": False, "error": "Diário não encontrado"}), 404

        # Delete the diet
        db.session.delete(diet)
        db.session.commit()

        return jsonify({"success": True, "message": "Diário deletado com sucesso"})
    except ValueError:
        return jsonify(
            {"success": False, "error": "Formato de data inválido. Use YYYY-MM-DD"}
        ), 400
    except Exception as e:
        db.session.rollback()
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
                        "calories_per_100g": 100
                        * user_food.calories
                        / user_food.quantity,
                        "proteins_per_100g": 100
                        * user_food.proteins
                        / user_food.quantity,
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
            # Get user info safely (handle missing attributes and guest users)
            if current_user.is_authenticated:
                user_name = getattr(current_user, "nome", None) or getattr(
                    current_user, "username", "Usuário"
                )
                user_age = getattr(current_user, "idade", None)
                user_height = getattr(current_user, "altura", None)
                user_weight = getattr(current_user, "peso", None)
                user_sex = getattr(current_user, "sexo", None)
            else:
                # Guest user - use default values
                user_name = "Visitante"
                user_age = None
                user_height = None
                user_weight = None
                user_sex = None

            user_info = [f"Usuário: {user_name}"]
            if user_age:
                user_info.append(f"Idade: {user_age} anos")
            if user_height:
                user_info.append(f"Altura: {user_height} cm")
            if user_weight:
                user_info.append(f"Peso: {user_weight} kg")
            if user_sex:
                user_info.append(
                    f"Sexo: {'Masculino' if user_sex == 'M' else 'Feminino'}"
                )

            user_info.extend(
                [
                    f"Data: {export_date.strftime('%d/%m/%Y')}",
                    "",  # Empty row for spacing
                    "Resumo por Refeição:",
                ]
            )

            summary_data = {"Informações do Usuário": user_info}

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
        foods = (
            UserFood.query.filter_by(user_id=current_user.id)
            .order_by(UserFood.code)
            .all()
        )
        return jsonify(
            {
                "success": True,
                "foods": [
                    {
                        "id": food.id,
                        "code": food.code,
                        "name": food.name,
                        "quantity": food.quantity,
                        "calories": food.calories,
                        "proteins": food.proteins,
                        "carbs": food.carbs,
                        "fats": food.fats,
                        "created_at": food.created_at.isoformat()
                        if food.created_at
                        else None,
                    }
                    for food in foods
                ],
            }
        )
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
            return jsonify(
                {
                    "success": False,
                    "error": "Por favor, preencha pelo menos o código ou o nome do alimento",
                }
            ), 400

        # Se não tiver código, usa o nome como código
        if not code:
            code = name
        # Se não tiver nome, usa o código como nome
        if not name:
            name = code

        # Validação dos campos obrigatórios
        if quantity is None or proteins is None or carbs is None or fats is None:
            return jsonify(
                {
                    "success": False,
                    "error": "Quantidade, proteínas, carboidratos e gorduras são obrigatórios",
                }
            ), 400

        if quantity <= 0:
            return jsonify(
                {"success": False, "error": "A quantidade deve ser maior que zero"}
            ), 400

        # Calcula calorias automaticamente: Calorias = 4 × Proteínas + 4 × Carboidratos + 9 × Gorduras
        calories = (4 * float(proteins)) + (4 * float(carbs)) + (9 * float(fats))

        # Verifica se já existe um alimento com o mesmo código para este usuário
        existing = UserFood.query.filter_by(user_id=current_user.id, code=code).first()

        if existing:
            return jsonify(
                {
                    "success": False,
                    "error": f"Já existe um alimento com o código '{code}'",
                }
            ), 400

        # Cria o alimento
        user_food = UserFood(
            user_id=current_user.id,
            code=code,
            name=name,
            quantity=float(quantity),
            calories=round(calories, 1),
            proteins=float(proteins),
            carbs=float(carbs),
            fats=float(fats),
        )

        db.session.add(user_food)
        db.session.commit()

        return jsonify(
            {
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
                },
            }
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/user_foods/<int:food_id>", methods=["PUT"])
@login_required
def update_user_food(food_id):
    """Atualiza um alimento personalizado"""
    try:
        food = UserFood.query.filter_by(
            id=food_id, user_id=current_user.id
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
            return jsonify(
                {
                    "success": False,
                    "error": "Por favor, preencha pelo menos o código ou o nome do alimento",
                }
            ), 400

        # Se não tiver código, usa o nome como código
        if not code:
            code = name
        # Se não tiver nome, usa o código como nome
        if not name:
            name = code

        # Validação dos campos obrigatórios
        if quantity is None or proteins is None or carbs is None or fats is None:
            return jsonify(
                {
                    "success": False,
                    "error": "Quantidade, proteínas, carboidratos e gorduras são obrigatórios",
                }
            ), 400

        if quantity <= 0:
            return jsonify(
                {"success": False, "error": "A quantidade deve ser maior que zero"}
            ), 400

        # Calcula calorias automaticamente: Calorias = 4 × Proteínas + 4 × Carboidratos + 9 × Gorduras
        calories = (4 * float(proteins)) + (4 * float(carbs)) + (9 * float(fats))

        # Verifica se o código já existe em outro alimento do mesmo usuário
        if code != food.code:
            existing = UserFood.query.filter_by(
                user_id=current_user.id, code=code
            ).first()

            if existing:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Já existe um alimento com o código '{code}'",
                    }
                ), 400

        # Atualiza o alimento
        food.code = code
        food.name = name
        food.quantity = float(quantity)
        food.calories = round(calories, 1)
        food.proteins = float(proteins)
        food.carbs = float(carbs)
        food.fats = float(fats)

        db.session.commit()

        return jsonify(
            {
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
                },
            }
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/user_foods/<int:food_id>", methods=["DELETE"])
@login_required
def delete_user_food(food_id):
    """Deleta um alimento personalizado"""
    try:
        food = UserFood.query.filter_by(
            id=food_id, user_id=current_user.id
        ).first_or_404()

        db.session.delete(food)
        db.session.commit()

        return jsonify({"success": True, "message": "Alimento deletado com sucesso!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/chatbot", methods=["POST"])
@login_required
def chatbot():
    from flask import current_app
    from openai import OpenAI
    from datetime import date, datetime, timedelta
    import re

    data = request.get_json()
    user_message = data.get("message")
    conversation_history = data.get("history", [])
    requested_date = data.get("date")  # Data específica se fornecida

    if not user_message:
        return jsonify({"error": "Mensagem não fornecida"}), 400

    # Importar modelos necessários
    from app.models import FoodData, UserFood

    # Extrair possíveis nomes de alimentos mencionados na mensagem
    # Buscar palavras que podem ser nomes de alimentos (palavras com mais de 3 caracteres)
    mentioned_foods = []
    words = re.findall(r"\b\w{4,}\b", user_message.lower())

    # Buscar alimentos mencionados na mensagem
    for word in words[:10]:  # Limitar a 10 palavras para não sobrecarregar
        # Buscar por nome (case insensitive)
        food_by_name = (
            FoodData.query.filter(FoodData.name.ilike(f"%{word}%")).limit(5).all()
        )

        for food in food_by_name:
            if food.code not in [f["code"] for f in mentioned_foods]:
                mentioned_foods.append(
                    {
                        "code": food.code,
                        "name": food.name,
                        "calories_per_100g": (food.calories / food.quantity * 100)
                        if food.quantity > 0
                        else 0,
                        "proteins_per_100g": (food.proteins / food.quantity * 100)
                        if food.quantity > 0
                        else 0,
                        "carbs_per_100g": (food.carbs / food.quantity * 100)
                        if food.quantity > 0
                        else 0,
                        "fats_per_100g": (food.fats / food.quantity * 100)
                        if food.quantity > 0
                        else 0,
                        "mentioned": True,  # Flag para indicar que foi mencionado
                    }
                )

        # Buscar também nos alimentos personalizados do usuário
        user_food_by_name = (
            UserFood.query.filter(
                UserFood.user_id == current_user.id, UserFood.name.ilike(f"%{word}%")
            )
            .limit(5)
            .all()
        )

        for food in user_food_by_name:
            if food.code not in [f["code"] for f in mentioned_foods]:
                mentioned_foods.append(
                    {
                        "code": food.code,
                        "name": food.name,
                        "calories_per_100g": (food.calories / food.quantity * 100)
                        if food.quantity > 0
                        else 0,
                        "proteins_per_100g": (food.proteins / food.quantity * 100)
                        if food.quantity > 0
                        else 0,
                        "carbs_per_100g": (food.carbs / food.quantity * 100)
                        if food.quantity > 0
                        else 0,
                        "fats_per_100g": (food.fats / food.quantity * 100)
                        if food.quantity > 0
                        else 0,
                        "mentioned": True,
                    }
                )

    # Obter API key do config (que pode vir de variável de ambiente ou valor padrão)
    api_key = current_app.config.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify(
            {
                "error": "API key não configurada. Configure OPENAI_API_KEY no config.py ou como variável de ambiente."
            }
        ), 500

    # Determinar a data a ser consultada
    # Tenta extrair data da mensagem ou usa a data fornecida ou hoje
    target_date = date.today()
    if requested_date:
        try:
            target_date = datetime.strptime(requested_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    else:
        # Tenta extrair data da mensagem (formato: "hoje", "ontem", "15/01/2024", etc)
        user_msg_lower = user_message.lower()

        # Verifica se menciona "hoje", "atual", "deste dia"
        if re.search(r"hoje|atual|deste dia", user_msg_lower):
            target_date = date.today()
        # Verifica se menciona "ontem"
        elif re.search(r"ontem", user_msg_lower):
            target_date = date.today() - timedelta(days=1)
        # Tenta extrair data no formato DD/MM/YYYY
        else:
            date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", user_message)
            if date_match:
                try:
                    day = int(date_match.group(1))
                    month = int(date_match.group(2))
                    year = int(date_match.group(3))
                    target_date = date(year, month, day)
                except (ValueError, AttributeError):
                    pass

    # Buscar dieta do dia
    from app.models import Diet, FoodData, UserFood
    from app.constants import MEAL_TYPES

    daily_diet = Diet.query.filter_by(user_id=current_user.id, date=target_date).first()

    # Buscar alimentos disponíveis na base de dados
    # Limitar a 500 alimentos mais comuns para não exceder tokens
    all_foods = []

    # Adicionar alimentos mencionados primeiro (prioridade)
    mentioned_codes = {f["code"] for f in mentioned_foods}
    all_foods.extend(mentioned_foods)

    # Buscar alimentos globais (FoodData) - excluindo os já mencionados
    global_foods = (
        FoodData.query.filter(
            ~FoodData.code.in_(mentioned_codes) if mentioned_codes else True
        )
        .limit(300)
        .all()
    )
    for food in global_foods:
        all_foods.append(
            {
                "code": food.code,
                "name": food.name,
                "calories_per_100g": (food.calories / food.quantity * 100)
                if food.quantity > 0
                else 0,
                "proteins_per_100g": (food.proteins / food.quantity * 100)
                if food.quantity > 0
                else 0,
                "carbs_per_100g": (food.carbs / food.quantity * 100)
                if food.quantity > 0
                else 0,
                "fats_per_100g": (food.fats / food.quantity * 100)
                if food.quantity > 0
                else 0,
            }
        )

    # Buscar alimentos personalizados do usuário - excluindo os já mencionados
    user_foods = (
        UserFood.query.filter(
            UserFood.user_id == current_user.id,
            ~UserFood.code.in_(mentioned_codes) if mentioned_codes else True,
        )
        .limit(200)
        .all()
    )
    for food in user_foods:
        all_foods.append(
            {
                "code": food.code,
                "name": food.name,
                "calories_per_100g": (food.calories / food.quantity * 100)
                if food.quantity > 0
                else 0,
                "proteins_per_100g": (food.proteins / food.quantity * 100)
                if food.quantity > 0
                else 0,
                "carbs_per_100g": (food.carbs / food.quantity * 100)
                if food.quantity > 0
                else 0,
                "fats_per_100g": (food.fats / food.quantity * 100)
                if food.quantity > 0
                else 0,
            }
        )

    # Categorizar alimentos por tipo de refeição (lógica brasileira)
    def categorize_food_for_meal(food_name):
        """Categoriza alimento por tipo de refeição baseado em palavras-chave"""
        name_lower = food_name.lower()

        # Café da Manhã - alimentos típicos
        cafe_keywords = [
            "pão",
            "torrada",
            "bolacha",
            "biscoito",
            "cereal",
            "aveia",
            "granola",
            "leite",
            "iogurte",
            "queijo",
            "requeijão",
            "manteiga",
            "margarina",
            "ovo",
            "ovos",
            "omelete",
            "fruta",
            "banana",
            "maçã",
            "laranja",
            "suco",
            "café",
            "chá",
            "mel",
            "geleia",
            "marmelada",
            "creme",
            "tapioca",
            "crepioca",
            "panqueca",
            "waffle",
        ]

        # Almoço/Jantar - prato principal
        almoco_keywords = [
            "arroz",
            "feijão",
            "batata",
            "batata doce",
            "mandioca",
            "aipim",
            "macarrão",
            "massa",
            "lasanha",
            "frango",
            "frango grelhado",
            "carne",
            "bife",
            "peixe",
            "salmão",
            "tilápia",
            "sardinha",
            "salada",
            "alface",
            "tomate",
            "cenoura",
            "brócolis",
            "couve",
            "ovo frito",
            "ovo cozido",
            "hambúrguer",
            "pizza",
            "strogonoff",
            "parmegiana",
            "moqueca",
            "feijoada",
            "churrasco",
            "churrasquinho",
        ]

        # Lanches - alimentos leves
        lanche_keywords = [
            "fruta",
            "banana",
            "maçã",
            "laranja",
            "pera",
            "uva",
            "mamão",
            "iogurte",
            "queijo",
            "bolacha",
            "biscoito",
            "cereal",
            "barra",
            "castanha",
            "amendoim",
            "nozes",
            "suco",
            "vitamina",
            "smoothie",
        ]

        # Ceia - alimentos leves
        ceia_keywords = [
            "chá",
            "leite",
            "iogurte",
            "fruta",
            "banana",
            "bolacha",
            "biscoito",
            "queijo",
            "castanha",
            "amendoim",
        ]

        categories = {
            "cafe_da_manha": any(kw in name_lower for kw in cafe_keywords),
            "almoco": any(kw in name_lower for kw in almoco_keywords),
            "janta": any(kw in name_lower for kw in almoco_keywords),
            "lanche_manha": any(kw in name_lower for kw in lanche_keywords),
            "lanche_tarde": any(kw in name_lower for kw in lanche_keywords),
            "ceia": any(kw in name_lower for kw in ceia_keywords),
        }

        return categories

    # Criar lista de alimentos categorizados (limitado para não exceder tokens)
    foods_by_category = {
        "cafe_da_manha": [],
        "almoco": [],
        "janta": [],
        "lanche_manha": [],
        "lanche_tarde": [],
        "ceia": [],
        "geral": [],  # Alimentos que podem ser usados em qualquer refeição
    }

    # Categorizar até 200 alimentos mais relevantes
    for food in all_foods[:200]:
        categories = categorize_food_for_meal(food["name"])
        categorized = False

        for meal_type, is_suitable in categories.items():
            if is_suitable:
                foods_by_category[meal_type].append(food)
                categorized = True

        if not categorized:
            foods_by_category["geral"].append(food)

    # Criar resumo de alimentos disponíveis por categoria
    foods_summary = "ALIMENTOS DISPONÍVEIS NA BASE DE DADOS (use APENAS estes alimentos nas recomendações):\n\n"

    # Primeiro, mostrar alimentos mencionados pelo usuário (se houver)
    if mentioned_foods:
        foods_summary += "⚠️ ALIMENTOS MENCIONADOS PELO USUÁRIO (PRIORIDADE - use estes se mencionados):\n"
        for food in mentioned_foods:
            foods_summary += f"  - {food['name']} (Código: {food['code']}, {food['calories_per_100g']:.0f} kcal/100g, {food['proteins_per_100g']:.1f}g prot, {food['carbs_per_100g']:.1f}g carb, {food['fats_per_100g']:.1f}g gord)\n"
        foods_summary += "\n"

    for meal_type, meal_name in MEAL_TYPES.items():
        foods_list = foods_by_category.get(meal_type, [])
        if foods_list:
            foods_summary += f"{meal_name} ({len(foods_list)} alimentos):\n"
            # Mostrar apenas primeiros 15 alimentos de cada categoria para não exceder tokens
            for food in foods_list[:15]:
                foods_summary += f"  - {food['name']} (Código: {food['code']}, {food['calories_per_100g']:.0f} kcal/100g, {food['proteins_per_100g']:.1f}g prot, {food['carbs_per_100g']:.1f}g carb, {food['fats_per_100g']:.1f}g gord)\n"
            if len(foods_list) > 15:
                foods_summary += f"  ... e mais {len(foods_list) - 15} alimentos\n"
            foods_summary += "\n"

    if foods_by_category["geral"]:
        foods_summary += (
            f"Alimentos gerais ({len(foods_by_category['geral'])} alimentos):\n"
        )
        for food in foods_by_category["geral"][:10]:
            foods_summary += f"  - {food['name']} (Código: {food['code']})\n"
        foods_summary += "\n"

    foods_summary += "IMPORTANTE: Se o usuário mencionar um alimento específico, SEMPRE verifique se ele está na lista acima (especialmente na seção 'ALIMENTOS MENCIONADOS'). Se estiver, use-o e confirme que está disponível. Se não estiver na lista mas o usuário insistir, informe que você pode recomendar alimentos similares que estão disponíveis na base de dados."

    # Calcular totais do que já foi consumido
    daily_totals = {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}
    meals_summary = []
    meals_detail = {}

    if daily_diet and daily_diet.meals_data:
        for meal_type, foods in daily_diet.meals_data.items():
            meal_name = MEAL_TYPES.get(meal_type, meal_type)
            meal_totals = {"calories": 0, "proteins": 0, "carbs": 0, "fats": 0}
            meal_foods = []

            for food in foods:
                calories = float(food.get("calories", 0))
                proteins = float(food.get("proteins", 0))
                carbs = float(food.get("carbs", 0))
                fats = float(food.get("fats", 0))

                daily_totals["calories"] += calories
                daily_totals["proteins"] += proteins
                daily_totals["carbs"] += carbs
                daily_totals["fats"] += fats

                meal_totals["calories"] += calories
                meal_totals["proteins"] += proteins
                meal_totals["carbs"] += carbs
                meal_totals["fats"] += fats

                food_code = food.get("food_code", "Desconhecido")
                quantity = food.get("quantity", 0)
                meal_foods.append(f"{food_code} ({quantity}g)")

            if meal_totals["calories"] > 0:
                meals_summary.append(
                    f"{meal_name}: {meal_totals['calories']:.0f} kcal, "
                    f"{meal_totals['proteins']:.1f}g proteínas, "
                    f"{meal_totals['carbs']:.1f}g carboidratos, "
                    f"{meal_totals['fats']:.1f}g gorduras"
                )
                meals_detail[meal_name] = {"foods": meal_foods, "totals": meal_totals}

    # Use dados do usuário
    user = current_user
    user_profile = {
        "nome": user.nome,
        "idade": user.idade,
        "peso": user.peso,
        "altura": user.altura,
        "sexo": user.get_sexo_display(),
        "objetivo": user.get_objetivo_display(),
        "atividade": user.get_fator_atividade_display(),
        "calories_goal": user.calories_goal or 0,
        "proteins_goal": user.proteins_goal or 0,
        "carbs_goal": user.carbs_goal or 0,
        "fats_goal": user.fats_goal or 0,
    }

    # Calcular IMC
    imc = user.peso / (user.altura**2) if user.altura > 0 else 0

    # Calcular percentuais consumidos
    calories_percent = (
        (daily_totals["calories"] / user_profile["calories_goal"] * 100)
        if user_profile["calories_goal"] > 0
        else 0
    )
    proteins_percent = (
        (daily_totals["proteins"] / user_profile["proteins_goal"] * 100)
        if user_profile["proteins_goal"] > 0
        else 0
    )
    carbs_percent = (
        (daily_totals["carbs"] / user_profile["carbs_goal"] * 100)
        if user_profile["carbs_goal"] > 0
        else 0
    )
    fats_percent = (
        (daily_totals["fats"] / user_profile["fats_goal"] * 100)
        if user_profile["fats_goal"] > 0
        else 0
    )

    # Formatar data para exibição
    date_str = target_date.strftime("%d/%m/%Y")
    if target_date == date.today():
        date_str = "hoje"

    # Construir resumo do consumo do dia
    consumption_summary = ""
    if daily_totals["calories"] > 0:
        consumption_summary = f"""
CONSUMO DO DIA ({date_str}):
- Total consumido:
  * Calorias: {daily_totals["calories"]:.0f} kcal ({calories_percent:.1f}% da meta de {user_profile["calories_goal"]:.0f} kcal)
  * Proteínas: {daily_totals["proteins"]:.1f} g ({proteins_percent:.1f}% da meta de {user_profile["proteins_goal"]:.0f} g)
  * Carboidratos: {daily_totals["carbs"]:.1f} g ({carbs_percent:.1f}% da meta de {user_profile["carbs_goal"]:.0f} g)
  * Gorduras: {daily_totals["fats"]:.1f} g ({fats_percent:.1f}% da meta de {user_profile["fats_goal"]:.0f} g)

- Restante para atingir as metas:
  * Calorias: {max(0, user_profile["calories_goal"] - daily_totals["calories"]):.0f} kcal
  * Proteínas: {max(0, user_profile["proteins_goal"] - daily_totals["proteins"]):.1f} g
  * Carboidratos: {max(0, user_profile["carbs_goal"] - daily_totals["carbs"]):.1f} g
  * Gorduras: {max(0, user_profile["fats_goal"] - daily_totals["fats"]):.1f} g

- Refeições consumidas:
"""
        for meal in meals_summary:
            consumption_summary += f"  * {meal}\n"
    else:
        consumption_summary = f"\nCONSUMO DO DIA ({date_str}):\nNenhum alimento registrado ainda para este dia."

    # Sistema de prompt para o assistente nutricional
    # Quebrar em partes para evitar f-string aninhada demais
    altura_cm = user_profile["altura"] * 100

    system_prompt_parts = [
        'Você é um assistente nutricional especializado chamado "Nutri AI". Seu papel é fornecer orientações nutricionais personalizadas, recomendar dietas e responder perguntas sobre nutrição.\n\n',
        "INFORMAÇÕES DO USUÁRIO:\n",
        f"- Nome: {user_profile['nome']}\n",
        f"- Idade: {user_profile['idade']} anos\n",
        f"- Peso: {user_profile['peso']} kg\n",
        f"- Altura: {user_profile['altura']} m ({altura_cm:.0f} cm)\n",
        f"- IMC: {imc:.1f}\n",
        f"- Sexo: {user_profile['sexo']}\n",
        f"- Objetivo: {user_profile['objetivo']}\n",
        f"- Nível de atividade: {user_profile['atividade']}\n",
        "- Metas nutricionais diárias:\n",
        f"  * Calorias: {user_profile['calories_goal']:.0f} kcal\n",
        f"  * Proteínas: {user_profile['proteins_goal']:.0f} g\n",
        f"  * Carboidratos: {user_profile['carbs_goal']:.0f} g\n",
        f"  * Gorduras: {user_profile['fats_goal']:.0f} g\n",
        consumption_summary,
        "\n",
        foods_summary,
        "\n",
    ]

    system_prompt = (
        "".join(system_prompt_parts)
        + """

REGRAS CRÍTICAS SOBRE ALIMENTOS E REFEIÇÕES BRASILEIRAS:

1. USE APENAS ALIMENTOS DA BASE DE DADOS:
   - Você DEVE usar APENAS os alimentos listados acima
   - Se o usuário mencionar um alimento específico, verifique PRIMEIRO se ele está na lista (especialmente na seção "ALIMENTOS MENCIONADOS")
   - Se o alimento mencionado estiver na lista, SEMPRE use-o e confirme que ele está disponível
   - Se o alimento mencionado NÃO estiver na lista, informe educadamente que não está disponível na base de dados e sugira alternativas similares que existam
   - Sempre mencione o CÓDIGO do alimento ao recomendar (ex: "Arroz branco (código: ARR001)")
   - NUNCA diga que um alimento não está disponível se ele aparecer na lista acima

2. LÓGICA DE REFEIÇÕES BRASILEIRAS (MUITO IMPORTANTE):
   - CAFÉ DA MANHÃ: Use apenas alimentos típicos de café da manhã brasileiro:
     * Pães, torradas, bolachas, cereais, aveia, granola
     * Leite, iogurte, queijos, requeijão, manteiga
     * Ovos (omelete, mexidos, cozidos)
     * Frutas, sucos, café, chá
     * Tapioca, crepioca, panqueca
     * NUNCA recomende: feijão, arroz, macarrão, carnes principais, pratos quentes pesados
   
   - ALMOÇO: Use alimentos típicos de almoço brasileiro:
     * Arroz, feijão, batata, batata doce, mandioca
     * Carnes (frango, carne bovina, peixe)
     * Saladas e legumes
     * Macarrão, lasanha (ocasionalmente)
     * NUNCA recomende: alimentos típicos de café da manhã como pão com manteiga, cereais
   
   - JANTAR: Similar ao almoço, mas pode ser mais leve:
     * Pode incluir os mesmos alimentos do almoço
     * Pode ser mais leve (sopas, saladas maiores)
     * NUNCA recomende: alimentos típicos de café da manhã
   
   - LANCHE DA MANHÃ/TARDE: Alimentos leves e práticos:
     * Frutas, iogurte, queijo
     * Bolachas, biscoitos, barras de cereal
     * Castanhas, nozes, amendoim
     * Sucos, vitaminas
     * NUNCA recomende: pratos principais como arroz e feijão
   
   - CEIA: Alimentos muito leves:
     * Chá, leite morno
     * Frutas leves, iogurte
     * Bolachas leves
     * NUNCA recomende: pratos pesados ou alimentos típicos de almoço

3. EXEMPLOS DO QUE NÃO FAZER (ERRADO):
   - ❌ Recomendar feijão no café da manhã
   - ❌ Recomendar pão com manteiga no almoço
   - ❌ Recomendar arroz e feijão no lanche
   - ❌ Recomendar alimentos que não estão na base de dados

4. EXEMPLOS DO QUE FAZER (CORRETO):
   - ✅ Café da manhã: Pão integral, queijo, ovo, fruta
   - ✅ Almoço: Arroz, feijão, frango grelhado, salada
   - ✅ Lanche: Banana, iogurte, castanhas
   - ✅ Jantar: Peixe grelhado, batata doce, legumes
   - ✅ Ceia: Chá, fruta leve

FORMATO DE RESPOSTA PARA RECOMENDAÇÕES (OBRIGATÓRIO):
IMPORTANTE: Quando o usuário pedir uma recomendação de dieta, alimentos, ou qualquer sugestão nutricional concreta, você DEVE SEMPRE incluir no final da sua resposta um bloco JSON estruturado com as seguintes informações. SEM EXCEÇÕES.

```json
{
  "recommendation": true,
  "meals": [
    {
      "meal_type": "cafe_da_manha",
      "foods": [
        {
          "code": "CODIGO_DO_ALIMENTO",
          "name": "Nome do Alimento",
          "quantity": 100,
          "calories": 200,
          "proteins": 10,
          "carbs": 30,
          "fats": 5
        }
      ]
    }
  ]
}
```

TIPOS DE REFEIÇÃO VÁLIDOS:
- "cafe_da_manha" - Café da Manhã
- "lanche_manha" - Lanche da Manhã
- "almoco" - Almoço
- "lanche_tarde" - Lanche da Tarde
- "janta" - Jantar
- "ceia" - Ceia

REGRAS CRÍTICAS SOBRE O JSON DE RECOMENDAÇÃO:
- Use APENAS os códigos de alimentos que estão na lista acima
- Calcule as quantidades baseadas nos valores por 100g fornecidos
- SEMPRE inclua o JSON quando o usuário pedir uma recomendação de dieta, alimentos, ou sugestões nutricionais
- O JSON é OBRIGATÓRIO quando você fornecer uma recomendação concreta de alimentos
- O JSON deve estar no final da resposta, após o texto explicativo
- O JSON deve estar dentro de um bloco de código markdown: ```json ... ```
- Após fornecer a recomendação no texto, SEMPRE inclua o JSON e então pergunte: "Gostaria que eu adicione esta recomendação ao seu diário de hoje?"
- Exemplo de estrutura de resposta:
  1. Texto explicativo da recomendação
  2. Bloco JSON com os alimentos
  3. Pergunta se deseja adicionar ao diário

DIRETRIZES GERAIS:
1. Sempre forneça respostas em português brasileiro
2. Seja profissional, mas amigável e encorajador
3. Use as informações do perfil do usuário para personalizar suas recomendações
4. Quando recomendar dietas, considere as metas nutricionais do usuário E o que já foi consumido no dia
5. Se o usuário já consumiu alimentos, considere o que falta para atingir as metas ao fazer recomendações
6. Seja específico com quantidades e porções quando possível
7. Sempre mencione o CÓDIGO do alimento ao recomendar
8. Se não tiver certeza sobre algo, seja honesto e recomende consultar um nutricionista
9. Mantenha as respostas concisas mas informativas
10. Use emojis moderadamente para tornar a conversa mais amigável
11. SEMPRE considere o consumo atual do dia ao fazer recomendações nutricionais
12. RESPEITE A LÓGICA BRASILEIRA DE REFEIÇÕES - não recomende alimentos inadequados para cada horário"""
    )

    # Preparar histórico de conversa
    messages = [{"role": "system", "content": system_prompt}]

    # Adicionar histórico de conversa (últimas 10 mensagens para não exceder tokens)
    for msg in conversation_history[-10:]:
        messages.append(
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
        )

    # Adicionar mensagem atual
    # Se o usuário estiver pedindo uma recomendação de dieta, adicionar instrução extra
    user_message_lower = user_message.lower()
    if any(
        keyword in user_message_lower
        for keyword in [
            "recomende",
            "recomendação",
            "dieta",
            "dietas",
            "sugira",
            "sugestão",
            "me dê",
            "me dê uma",
            "quero",
            "preciso",
            "pode me ajudar com",
        ]
    ):
        # Adicionar uma mensagem do sistema antes da mensagem do usuário para reforçar
        messages.append(
            {
                "role": "system",
                "content": "IMPORTANTE: O usuário está pedindo uma recomendação. Você DEVE incluir um bloco JSON com os alimentos recomendados no formato especificado. O JSON é OBRIGATÓRIO.",
            }
        )

    messages.append({"role": "user", "content": user_message})

    try:
        # Inicializar cliente OpenAI
        # Garantir que apenas api_key seja passado (sem proxies ou outras configurações)
        # Limpar qualquer configuração de proxy que possa estar sendo passada implicitamente
        import os
        # Remover temporariamente variáveis de ambiente de proxy se existirem
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        saved_proxies = {}
        for var in proxy_vars:
            if var in os.environ:
                saved_proxies[var] = os.environ.pop(var)
        
        try:
            # Inicializar cliente apenas com api_key
            client = OpenAI(api_key=api_key)
        finally:
            # Restaurar variáveis de ambiente de proxy se existirem
            for var, value in saved_proxies.items():
                os.environ[var] = value

        # Chamada à API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo mais econômico e rápido
            messages=messages,
            temperature=0.7,
            max_tokens=2000,  # Aumentado para evitar que JSON seja cortado
        )

        assistant_message = response.choices[0].message.content

        # Tentar extrair JSON de recomendação da resposta
        recommendation_data = None
        try:
            import json

            # Procurar por bloco JSON na resposta (entre ```json e ```)
            # Usar DOTALL para capturar múltiplas linhas
            # Modificar para capturar JSON mesmo que esteja incompleto (sem fechar })
            json_match = re.search(
                r"```json\s*(\{[\s\S]*?)(?:\}\s*```|```)", assistant_message
            )
            if json_match:
                json_str = json_match.group(1)
                json_str = json_str.strip()

                # Se não terminar com }, tentar fechar automaticamente
                if not json_str.rstrip().endswith("}"):
                    # Contar chaves abertas vs fechadas
                    open_count = json_str.count("{") - json_str.count("}")
                    if open_count > 0:
                        # Fechar chaves abertas
                        json_str += "}" * open_count
                        # Fechar arrays abertos
                        open_arrays = json_str.count("[") - json_str.count("]")
                        if open_arrays > 0:
                            json_str += "]" * open_arrays

                try:
                    recommendation_data = json.loads(json_str)
                except json.JSONDecodeError:
                    # Se ainda falhar, tentar método de correção abaixo
                    pass
            else:
                # Tentar encontrar JSON sem o bloco de código (caso o modelo não use o formato)
                # Primeiro, tentar encontrar um JSON completo balanceado
                json_match = re.search(
                    r'\{[\s\S]*?"recommendation"[\s\S]*?\}',
                    assistant_message,
                    re.DOTALL,
                )
                if json_match:
                    json_str = json_match.group(0)
                    # Tentar balancear chaves manualmente para garantir JSON válido
                    brace_count = 0
                    start_pos = json_str.find("{")
                    if start_pos != -1:
                        end_pos = start_pos
                        for i, char in enumerate(json_str[start_pos:], start_pos):
                            if char == "{":
                                brace_count += 1
                            elif char == "}":
                                brace_count -= 1
                                if brace_count == 0:
                                    end_pos = i + 1
                                    break
                        if brace_count == 0:
                            json_str = json_str[start_pos:end_pos]
                        else:
                            # Se não conseguiu balancear, usar o match original
                            json_str = json_str.strip()

                    # Limpar possíveis caracteres problemáticos
                    json_str = json_str.strip()
                    # Remover texto antes da primeira chave e depois da última
                    json_str = re.sub(r"^[^{]*", "", json_str)
                    json_str = re.sub(r"[^}]*$", "", json_str)

                    try:
                        recommendation_data = json.loads(json_str)
                    except json.JSONDecodeError as json_err:
                        # Se ainda falhar, tentar corrigir o JSON automaticamente
                        print(f"Tentativa de parse falhou: {json_err}")
                        print(
                            f"JSON problemático (primeiros 500 chars): {json_str[:500]}"
                        )

                        # Tentar corrigir problemas comuns no JSON
                        try:
                            # Remover vírgulas finais antes de } e ]
                            json_str_fixed = re.sub(r",\s*}", "}", json_str)
                            json_str_fixed = re.sub(r",\s*]", "]", json_str_fixed)

                            # Adicionar vírgulas faltando entre objetos em arrays
                            # Padrão: } seguido de { sem vírgula (mas não dentro de strings)
                            json_str_fixed = re.sub(r"}\s*{", "},{", json_str_fixed)

                            # Adicionar vírgulas faltando entre propriedades dentro de objetos
                            # Padrão: número ou string seguido de " sem vírgula
                            # Exemplo: "fats": 8.7\n        } -> precisa de vírgula se houver próximo objeto

                            # Tentar parsear novamente
                            recommendation_data = json.loads(json_str_fixed)
                            print("✅ JSON corrigido e parseado com sucesso!")
                        except (json.JSONDecodeError, ValueError) as fix_err:
                            print(f"Tentativa de correção falhou: {fix_err}")
                            # Se ainda falhar, tentar método mais agressivo
                            try:
                                # Tentar encontrar e extrair apenas a estrutura de meals
                                # Capturar tudo após "meals": [ até encontrar ] ou fim da string
                                meals_match = re.search(
                                    r'"meals"\s*:\s*\[([\s\S]*)',
                                    json_str_fixed,
                                    re.DOTALL,
                                )
                                if meals_match:
                                    # Reconstruir JSON mínimo válido
                                    meals_content = meals_match.group(1)

                                    # Tentar corrigir vírgulas faltando entre objetos
                                    meals_content = re.sub(
                                        r"}\s*{", "},{", meals_content
                                    )

                                    # Tentar fechar estruturas abertas
                                    meals_content = meals_content.rstrip()

                                    # Fechar objetos abertos primeiro
                                    open_braces = meals_content.count(
                                        "{"
                                    ) - meals_content.count("}")
                                    if open_braces > 0:
                                        # Fechar objetos abertos
                                        meals_content += "}" * open_braces

                                    # Fechar arrays abertos
                                    open_arrays = meals_content.count(
                                        "["
                                    ) - meals_content.count("]")
                                    if open_arrays > 0:
                                        meals_content += "]" * open_arrays

                                    # Se não terminar com ], adicionar
                                    if not meals_content.rstrip().endswith("]"):
                                        meals_content += "]"

                                    minimal_json = f'{{"recommendation": true, "meals": [{meals_content}]}}'
                                    recommendation_data = json.loads(minimal_json)
                                    print(
                                        "✅ JSON reconstruído e parseado com sucesso!"
                                    )
                            except (json.JSONDecodeError, ValueError) as recon_err:
                                print(f"Tentativa de reconstrução falhou: {recon_err}")
                                # Se ainda falhar, tentar método alternativo
                                pass

                        # Tentar encontrar o JSON completo procurando do início
                        # Encontrar todas as ocorrências de { que podem ser o início do JSON
                        start_positions = [
                            i for i, char in enumerate(assistant_message) if char == "{"
                        ]
                        for start_pos in start_positions:
                            brace_count = 0
                            end_pos = start_pos
                            in_string = False
                            escape_next = False

                            for i, char in enumerate(
                                assistant_message[start_pos:], start_pos
                            ):
                                if escape_next:
                                    escape_next = False
                                    continue

                                if char == "\\":
                                    escape_next = True
                                    continue

                                if char == '"' and not escape_next:
                                    in_string = not in_string
                                    continue

                                if not in_string:
                                    if char == "{":
                                        brace_count += 1
                                    elif char == "}":
                                        brace_count -= 1
                                        if brace_count == 0:
                                            end_pos = i + 1
                                            break

                            if brace_count == 0:
                                test_json = assistant_message[start_pos:end_pos]
                                if '"recommendation"' in test_json:
                                    try:
                                        # Tentar parsear diretamente
                                        recommendation_data = json.loads(test_json)
                                        print(
                                            "JSON encontrado e parseado com sucesso usando método alternativo"
                                        )
                                        break
                                    except json.JSONDecodeError as json_err:
                                        # Tentar corrigir o JSON antes de parsear
                                        try:
                                            # Remover vírgulas finais
                                            test_json_fixed = re.sub(
                                                r",\s*}", "}", test_json
                                            )
                                            test_json_fixed = re.sub(
                                                r",\s*]", "]", test_json_fixed
                                            )
                                            # Remover vírgulas duplicadas
                                            test_json_fixed = re.sub(
                                                r",\s*,", ",", test_json_fixed
                                            )

                                            recommendation_data = json.loads(
                                                test_json_fixed
                                            )
                                            print(
                                                "JSON corrigido e parseado com sucesso usando método alternativo"
                                            )
                                            break
                                        except (json.JSONDecodeError, ValueError):
                                            continue
                                    except (ValueError, TypeError):
                                        continue
                        pass
        except Exception as e:
            # Se não conseguir parsear, continua sem recomendação
            print(f"Erro ao parsear JSON de recomendação: {e}")
            # Log do conteúdo que causou erro para debug
            if len(assistant_message) > 500:
                print(f"Últimos 500 caracteres da resposta: {assistant_message[-500:]}")
            else:
                print(f"Resposta completa: {assistant_message}")
            pass

        # Log para debug
        if recommendation_data:
            print("✅ JSON de recomendação parseado com sucesso!")
            print(f"   Refeições: {len(recommendation_data.get('meals', []))}")
            for meal in recommendation_data.get("meals", []):
                print(
                    f"   - {meal.get('meal_type')}: {len(meal.get('foods', []))} alimento(s)"
                )
        else:
            print("⚠️ Nenhum JSON de recomendação encontrado na resposta")
            print(f"   Últimos 200 caracteres da resposta: {assistant_message[-200:]}")

        return jsonify(
            {
                "success": True,
                "response": assistant_message,
                "recommendation": recommendation_data,
            }
        )

    except Exception as e:
        import traceback

        print(f"Erro ao chamar OpenAI: {traceback.format_exc()}")
        return jsonify(
            {"success": False, "error": f"Erro ao processar mensagem: {str(e)}"}
        ), 500
