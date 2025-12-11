import os
from datetime import timedelta
from dotenv import load_dotenv

# Garantir que o .env seja carregado mesmo se importado diretamente
load_dotenv()


class Config:
    # Basic Flask Config
    # SECRET_KEY é obrigatória - deve ser definida no .env ou variável de ambiente
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY não configurada. Configure no arquivo .env ou como variável de ambiente."
        )

    # Database Config
    # Para desenvolvimento local, use SQLite: sqlite:///users.db
    # Para produção, use PostgreSQL (Render fornece DATABASE_URL automaticamente)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Fallback para SQLite em desenvolvimento local
        database_url = "sqlite:///users.db"

    # Handle PostgreSQL URL format (Render uses postgres://, SQLAlchemy needs postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File Paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    FOOD_DATA_PATH = os.path.join(BASE_DIR, "data", "food.xlsx")

    # Session Config
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SESSION_PROTECTION = "strong"

    # Custom Config
    ITEMS_PER_PAGE = 10
    MAX_SEARCH_RESULTS = 5

    # Email Configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "smtp.gmail.com"
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in ["true", "on", "1"]

    # Email credentials devem estar no .env
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    # Default sender - use MAIL_DEFAULT_SENDER env var, or MAIL_USERNAME, or a default
    MAIL_DEFAULT_SENDER = (
        os.environ.get("MAIL_DEFAULT_SENDER") or MAIL_USERNAME or "noreply@n3p.com"
    )

    # App URL for email links
    APP_URL = os.environ.get("APP_URL") or "http://localhost:5000"

    # OpenAI API Configuration
    # OPENAI_API_KEY deve estar no .env ou variável de ambiente
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
