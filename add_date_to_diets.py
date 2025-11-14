"""Script para adicionar campo date à tabela diets"""
from app import create_app, db
from app.models import Diet
from datetime import datetime

app = create_app()

with app.app_context():
    # Adiciona a coluna date se não existir
    try:
        # Verifica se a coluna já existe
        with db.engine.connect() as conn:
            result = conn.execute(db.text("PRAGMA table_info(diets)"))
            columns = [row[1] for row in result]
            
            if 'date' not in columns:
                print("Adicionando coluna date...")
                conn.execute(db.text("ALTER TABLE diets ADD COLUMN date DATE"))
                conn.commit()
                print("Coluna date adicionada!")
                
                # Preenche a data dos registros existentes
                print("Preenchendo datas dos registros existentes...")
                conn.execute(db.text("UPDATE diets SET date = DATE(created_at) WHERE date IS NULL"))
                conn.commit()
                print("Datas preenchidas!")
                print("Migration concluída!")
            else:
                print("Coluna date já existe!")
            
    except Exception as e:
        print(f"Erro: {e}")
        db.session.rollback()

