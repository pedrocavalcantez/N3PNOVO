"""
Script para corrigir o estado das migrations quando o banco já existe
"""
from app import create_app, db
from flask_migrate import stamp, upgrade

app = create_app()

with app.app_context():
    # Marca as migrations existentes como aplicadas
    print("Marcando migrations existentes como aplicadas...")
    try:
        # Marca a última migration conhecida como aplicada
        stamp(revision='23456789abcd')
        print("✓ Migrations marcadas com sucesso!")
    except Exception as e:
        print(f"Erro ao marcar migrations: {e}")
        # Se falhar, tenta marcar a inicial
        try:
            stamp(revision='123456789abc')
            print("✓ Migration inicial marcada!")
        except Exception as e2:
            print(f"Erro: {e2}")
    
    # Agora aplica a nova migration
    print("\nAplicando nova migration (user_foods)...")
    try:
        upgrade()
        print("✓ Migration aplicada com sucesso!")
    except Exception as e:
        print(f"Erro ao aplicar migration: {e}")

