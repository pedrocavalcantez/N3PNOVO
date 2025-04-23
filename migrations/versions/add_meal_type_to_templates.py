"""add meal type to templates

Revision ID: add_meal_type_to_templates
Revises: create_meal_templates
Create Date: 2024-03-21 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_meal_type_to_templates'
down_revision = 'create_meal_templates'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona a coluna meal_type
    op.add_column('meal_templates',
        sa.Column('meal_type', sa.String(length=20), nullable=False, server_default='cafe_da_manha')
    )

    # Cria um índice para melhorar a performance das consultas por tipo de refeição
    op.create_index(op.f('ix_meal_templates_meal_type'), 'meal_templates', ['meal_type'])

def downgrade():
    # Remove o índice
    op.drop_index(op.f('ix_meal_templates_meal_type'), table_name='meal_templates')
    
    # Remove a coluna
    op.drop_column('meal_templates', 'meal_type') 