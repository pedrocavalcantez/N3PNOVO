from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.blueprints.auth import bp
from app.models import User
from app.forms import LoginForm, SignupForm, EditProfileForm


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Nome de usuário ou senha inválidos", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for("main.dashboard")
        return redirect(next_page)

    return render_template("auth/login.html", title="Login", form=form)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Nome de usuário já existe", "danger")
            return redirect(url_for("auth.signup"))

        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                nome=form.nome.data,
                idade=form.idade.data,
                altura=form.altura.data,
                peso=form.peso.data,
                sexo=form.sexo.data,
                fator_atividade=form.fator_atividade.data,
                objetivo=form.objetivo.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao criar usuário. Por favor, verifique os dados.", "danger")
            return redirect(url_for("auth.signup"))

    return render_template("auth/signup.html", title="Cadastro", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Store old values to check if relevant fields changed
        old_peso = current_user.peso
        old_altura = current_user.altura
        old_idade = current_user.idade
        old_sexo = current_user.sexo
        old_fator_atividade = current_user.fator_atividade
        old_objetivo = current_user.objetivo

        # Update user information
        current_user.nome = form.nome.data
        current_user.idade = form.idade.data
        current_user.altura = form.altura.data
        current_user.peso = form.peso.data
        current_user.sexo = form.sexo.data
        current_user.fator_atividade = form.fator_atividade.data
        current_user.objetivo = form.objetivo.data

        # Check if any relevant fields changed
        if (
            old_peso != current_user.peso
            or old_altura != current_user.altura
            or old_idade != current_user.idade
            or old_sexo != current_user.sexo
            or old_fator_atividade != current_user.fator_atividade
            or old_objetivo != current_user.objetivo
        ):
            # Update nutritional goals if relevant fields changed
            current_user.update_goals()

        try:
            db.session.commit()
            flash("Perfil atualizado com sucesso!", "success")
            return redirect(url_for("auth.profile"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao atualizar perfil. Por favor, tente novamente.", "danger")

    # Create user_goals object
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
        "auth/profile.html",
        title="Editar Perfil",
        form=form,
        user_goals=user_goals,
        user=current_user,
    )


@bp.route("/profile/update_goals", methods=["POST"])
@login_required
def update_goals():
    try:
        calories_goal = request.form.get("calories_goal")
        proteins_percentage = request.form.get("proteins_percentage")
        carbs_percentage = request.form.get("carbs_percentage")
        fats_percentage = request.form.get("fats_percentage")

        # Valida se os campos foram enviados
        if not calories_goal or not proteins_percentage or not carbs_percentage or not fats_percentage:
            return jsonify({
                "success": False,
                "message": "Todos os campos são obrigatórios."
            }), 400

        calories_goal = float(calories_goal)
        proteins_percentage = float(proteins_percentage) / 100
        carbs_percentage = float(carbs_percentage) / 100
        fats_percentage = float(fats_percentage) / 100

        current_user.update_goals(
            calories_goal=calories_goal,
            proteins_percentage=proteins_percentage,
            carbs_percentage=carbs_percentage,
            fats_percentage=fats_percentage,
            commit=True,
        )

        return jsonify(
            {"success": True, "message": "Metas nutricionais atualizadas com sucesso!"}
        )
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        import traceback
        print(f"Erro ao atualizar metas: {str(e)}")
        print(traceback.format_exc())
        return jsonify(
            {
                "success": False,
                "message": f"Erro ao atualizar metas nutricionais: {str(e)}",
            }
        ), 500
