import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Drop all tables if they exist
    db.drop_all()
    # Create all tables
    db.create_all()

    # Create admin user
    admin = User(
        username="admin",
        email="admin@admin.com",
        nome="Administrador",
        idade=30,
        altura=170,
        peso=70,
        sexo="M",
        fator_atividade="moderado",
        objetivo="manter",
        calories_goal=2000,
        proteins_goal=150,
        is_admin=True,
        carbs_goal=250,
        fats_goal=70,
    )
    admin.set_password("123456")

    db.session.add(admin)
    db.session.commit()

    print("Database tables created successfully!")
    print("Admin user created with credentials:")
    print("Username: admin")
    print("Password: admin")
