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
