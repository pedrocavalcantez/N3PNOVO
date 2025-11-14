"""
Script para criar a tabela user_foods diretamente no banco de dados
Use este script se as migrations não funcionarem
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Verifica se a tabela já existe
        result = db.session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_foods'"
        ))
        if result.fetchone():
            print("A tabela user_foods já existe!")
        else:
            # Cria a tabela
            db.session.execute(text("""
                CREATE TABLE user_foods (
                    id INTEGER NOT NULL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    code VARCHAR(20) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    quantity FLOAT NOT NULL,
                    calories FLOAT NOT NULL,
                    proteins FLOAT NOT NULL,
                    carbs FLOAT NOT NULL,
                    fats FLOAT NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users (id),
                    UNIQUE(user_id, code)
                )
            """))
            db.session.commit()
            print("✓ Tabela user_foods criada com sucesso!")
            
            # Marca a migration como aplicada
            try:
                from flask_migrate import stamp
                stamp(revision='3456789abcde')
                print("✓ Migration marcada como aplicada!")
            except Exception as e:
                print(f"Aviso: Não foi possível marcar a migration ({e})")
                print("Execute manualmente: flask db stamp 3456789abcde")
    except Exception as e:
        db.session.rollback()
        print(f"Erro: {e}")

