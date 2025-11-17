import os
from datetime import timedelta


class Config:
    # Basic Flask Config
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-here"

    # Database Config
    # Default to PostgreSQL (for both local development and production)
    # To use SQLite locally instead, uncomment the line below and comment out the PostgreSQL URL
    # default_db_url = "sqlite:///users.db"
    default_db_url = "postgresql://admin:KaEGuaHnOM3eTTgTi9OdbgD7r5u45S2N@dpg-d4dje97gi27c73dmc9d0-a.oregon-postgres.render.com/db_foods_f8x9"

    # Handle PostgreSQL URL format (Render uses postgres://, SQLAlchemy needs postgresql://)
    database_url = os.environ.get("DATABASE_URL") or default_db_url
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
    MAIL_USERNAME = "n3psa7@gmail.com"  # os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = "mcor eush curw fhmu"  # os.environ.get("MAIL_PASSWORD")
    # Default sender - use MAIL_DEFAULT_SENDER env var, or MAIL_USERNAME, or a default
    MAIL_DEFAULT_SENDER = (
        os.environ.get("MAIL_DEFAULT_SENDER") or MAIL_USERNAME or "noreply@n3p.com"
    )

    # App URL for email links
    APP_URL = os.environ.get("APP_URL") or "http://localhost:5000"
