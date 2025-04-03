from app import create_app, db
from flask_migrate import Migrate
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Update the alembic_version table
    db.session.execute(
        text("UPDATE alembic_version SET version_num='initial_migration'")
    )
    db.session.commit()
    print("Alembic version updated successfully!")
