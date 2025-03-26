import os
from datetime import timedelta


class Config:
    # Basic Flask Config
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-here"

    # Database Config
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///users.db"
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
