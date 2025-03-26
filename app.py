from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import os
import json

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here"  # Change this to a secure secret key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    altura = db.Column(db.Float, nullable=False)  # altura em metros
    peso = db.Column(db.Float, nullable=False)  # peso em kg
    sexo = db.Column(
        db.String(1), nullable=False
    )  # 'M' para masculino, 'F' para feminino
    fator_atividade = db.Column(db.String(20), nullable=False)
    objetivo = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    proteins = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        nome = request.form.get("nome")
        idade = int(request.form.get("idade"))  # Convert to integer
        altura = float(request.form.get("altura"))  # Convert to float
        peso = float(request.form.get("peso"))  # Convert to float
        sexo = request.form.get("sexo")
        fator_atividade = request.form.get("fator_atividade")
        objetivo = request.form.get("objetivo")

        if User.query.filter_by(username=username).first():
            flash("Nome de usuário já existe")
            return redirect(url_for("signup"))

        try:
            user = User(
                username=username,
                nome=nome,
                idade=idade,
                altura=altura,
                peso=peso,
                sexo=sexo,
                fator_atividade=fator_atividade,
                objetivo=objetivo,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Cadastro realizado com sucesso!")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao criar usuário. Por favor, verifique os dados.")
            return redirect(url_for("signup"))

    return render_template("signup.html")


@app.route("/guest")
def guest():
    return render_template("guest.html")


@app.route("/dashboard")
@login_required
def dashboard():
    today = datetime.utcnow().date()
    foods = Food.query.filter(
        Food.user_id == current_user.id, db.func.date(Food.date) == today
    ).all()

    # Calculate totals
    total_calories = sum(food.calories for food in foods)
    total_proteins = sum(food.proteins for food in foods)
    total_carbs = sum(food.carbs for food in foods)
    total_fats = sum(food.fats for food in foods)

    return render_template(
        "dashboard.html",
        user=current_user,
        foods=foods,
        total_calories=total_calories,
        total_proteins=total_proteins,
        total_carbs=total_carbs,
        total_fats=total_fats,
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# Load food data from Excel
def load_food_data():
    try:
        excel_path = os.path.join("data", "food.xlsx.xlsx")
        return pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error loading food data: {str(e)}")
        return pd.DataFrame()


# Search food in the database
@app.route("/search_food")
def search_food():
    query = request.args.get("query", "").lower()
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
            "id": str(row["identificador"]),
            "text": str(row["identificador"]),
            "nutritionalInfo": {
                "Quantidade": float(row["Quantidade"]),
                "Calori": float(row["Calori"]),
                "Proteina": float(row["Proteina"]),
                "Carboidrat": float(row["Carboidrat"]),
                "Gordura": float(row["Gordura"]),
            },
        }
        for row in results
    ]

    return jsonify(formatted_results)


@app.route("/add_food", methods=["POST"])
@login_required
def add_food():
    if request.method == "POST":
        # Check if we're receiving multiple foods
        foods_json = request.form.get("foods")
        if foods_json:
            foods_data = json.loads(foods_json)
            for food_item in foods_data:
                food = Food(
                    name=str(food_item["code"]),
                    quantity=food_item["quantity"],
                    calories=food_item["calories"],
                    proteins=food_item["proteins"],
                    carbs=food_item["carbs"],
                    fats=food_item["fats"],
                    user_id=current_user.id,
                )
                db.session.add(food)

            try:
                db.session.commit()
                flash("Alimentos adicionados com sucesso!", "success")
            except Exception as e:
                db.session.rollback()
                flash("Erro ao adicionar alimentos. Tente novamente.", "error")

            return jsonify({"status": "success"})

        # Handle single food submission
        food_id = request.form.get("food_id")
        quantity_consumed = float(request.form.get("quantity", 0))

        df = load_food_data()
        if df.empty:
            flash("Erro ao carregar dados dos alimentos.", "error")
            return redirect(url_for("dashboard"))

        food_data = df[df["identificador"] == int(food_id)].iloc[0]
        base_quantity = food_data["Quantidade"]

        # Calculate the proportion
        proportion = quantity_consumed / base_quantity

        food = Food(
            name=str(food_data["identificador"]),
            quantity=quantity_consumed,
            calories=food_data["Calori"] * proportion,
            proteins=food_data["Proteina"] * proportion,
            carbs=food_data["Carboidrat"] * proportion,
            fats=food_data["Gordura"] * proportion,
            user_id=current_user.id,
        )

        try:
            db.session.add(food)
            db.session.commit()
            flash("Alimento adicionado com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao adicionar alimento. Tente novamente.", "error")

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
