"""remove_unique_constraint_on_meal_template_name

Revision ID: 1a8f4454b6d0
Revises: 127f44e8a12b
Create Date: 2025-11-14 17:28:08.538164

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '1a8f4454b6d0'
down_revision = '127f44e8a12b'
branch_labels = None
depends_on = None


def upgrade():
    # Remove a constraint única antiga apenas no 'name'
    # O banco ainda tem "UNIQUE (name)" que precisa ser removida
    # A nova constraint (user_id, name, meal_type) já existe e está correta
    
    # No SQLite, precisamos recriar a tabela para remover a constraint antiga
    with op.batch_alter_table('meal_templates', schema=None) as batch_op:
        # Primeiro, vamos tentar remover a constraint antiga
        # No SQLite com batch_alter_table, podemos tentar remover constraints nomeadas
        # Mas a constraint antiga pode não ter nome, então precisamos recriar a tabela
        
        # Vamos usar uma abordagem que recria a tabela sem a constraint antiga
        # mas mantendo todos os dados e a constraint nova
        
        # Como batch_alter_table do SQLite recria a tabela automaticamente,
        # vamos apenas garantir que a constraint antiga não seja recriada
        # removendo qualquer constraint única apenas no 'name'
        pass
    
    # Para SQLite, precisamos fazer manualmente via SQL
    # Vamos usar op.execute para remover a constraint antiga
    # No SQLite, constraints únicas sem nome são parte da definição da tabela
    # então precisamos recriar a tabela
    
    # Cria uma tabela temporária sem a constraint antiga
    op.execute("""
        CREATE TABLE meal_templates_new (
            id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(255),
            meal_type VARCHAR(20) NOT NULL,
            created_at DATETIME,
            updated_at DATETIME,
            meals_data JSON,
            user_id INTEGER,
            PRIMARY KEY (id),
            CONSTRAINT unique_user_meal_template UNIQUE (user_id, name, meal_type),
            CONSTRAINT fk_meal_templates_user_id FOREIGN KEY(user_id) REFERENCES users (id)
        )
    """)
    
    # Copia os dados
    op.execute("""
        INSERT INTO meal_templates_new 
        SELECT id, name, description, meal_type, created_at, updated_at, meals_data, user_id
        FROM meal_templates
    """)
    
    # Remove a tabela antiga
    op.execute("DROP TABLE meal_templates")
    
    # Renomeia a nova tabela
    op.execute("ALTER TABLE meal_templates_new RENAME TO meal_templates")
    
    # Recria os índices se necessário
    op.execute("CREATE INDEX IF NOT EXISTS ix_meal_templates_meal_type ON meal_templates (meal_type)")


def downgrade():
    # Não fazemos downgrade - a constraint antiga não deve ser restaurada
    # pois ela causava o problema de não permitir o mesmo nome para diferentes meal_types
    pass
