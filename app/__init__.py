from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = "Por favor, faça login para acessar esta página."
login.login_message_category = "info"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # Register blueprints
    from app.blueprints.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.blueprints.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.blueprints.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from app.blueprints.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    # Load user model for Flask-Login
    from app.models import User

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


from app import models
