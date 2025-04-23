from app import create_app, db
from app.models.user import User

def make_admin(email):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.admin = True
            db.session.commit()
            print(f"Usuário {email} agora é administrador!")
        else:
            print(f"Usuário {email} não encontrado!")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Uso: python -m scripts.make_admin <email>")
        sys.exit(1)
    make_admin(sys.argv[1]) 