from flask import Blueprint

bp = Blueprint("errors", __name__)

# Import handlers after blueprint creation to avoid circular imports
from app.blueprints.errors import handlers
