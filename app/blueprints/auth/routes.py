from flask import render_template, redirect, url_for, flash, request
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
        current_user.nome = form.nome.data
        current_user.idade = form.idade.data
        current_user.altura = form.altura.data
        current_user.peso = form.peso.data
        current_user.sexo = form.sexo.data
        current_user.fator_atividade = form.fator_atividade.data
        current_user.objetivo = form.objetivo.data

        try:
            db.session.commit()
            flash("Perfil atualizado com sucesso!", "success")
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao atualizar perfil. Por favor, tente novamente.", "danger")

    return render_template("auth/profile.html", title="Editar Perfil", form=form)
