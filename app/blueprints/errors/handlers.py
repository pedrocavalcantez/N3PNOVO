from flask import render_template
from app.blueprints.errors import bp


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template("errors/error.html", error=error), 404


@bp.app_errorhandler(500)
def internal_error(error):
    return render_template("errors/error.html", error=error), 500


@bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template("errors/error.html", error=error), 403
