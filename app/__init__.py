from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config

# Inicialização das extensões
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()

# Configuração do LoginManager
login.login_view = "auth.login"
login.login_message = "Por favor, faça login para acessar esta página."
login.login_message_category = "info"

def register_blueprints(app):
    """Registra todos os blueprints da aplicação."""
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.main import bp as main_bp
    from app.blueprints.errors import bp as errors_bp
    from app.blueprints.api import bp as api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

def create_app(config_class=Config):
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializa as extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)

    # Registra os blueprints
    register_blueprints(app)

    # Configura o carregador de usuário para o Flask-Login
    from app.models import User

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

# Importa os modelos para que o Flask-Migrate possa detectá-los
from app import models
