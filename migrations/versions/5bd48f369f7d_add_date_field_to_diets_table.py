"""Add date field to diets table

Revision ID: 5bd48f369f7d
Revises: 0598a5c47f1c
Create Date: 2025-11-14 16:39:37.421639

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5bd48f369f7d'
down_revision = '0598a5c47f1c'
branch_labels = None
depends_on = None


def upgrade():
    # Primeiro adiciona a coluna como nullable
    with op.batch_alter_table('diets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date', sa.Date(), nullable=True))
    
    # Preenche a data dos registros existentes com a data de criação
    op.execute("UPDATE diets SET date = DATE(created_at) WHERE date IS NULL")
    
    # Agora torna a coluna NOT NULL e adiciona a constraint única
    with op.batch_alter_table('diets', schema=None) as batch_op:
        batch_op.alter_column('date', nullable=False)
        batch_op.create_unique_constraint('unique_user_diet_date', ['user_id', 'date'])


def downgrade():
    with op.batch_alter_table('diets', schema=None) as batch_op:
        batch_op.drop_constraint('unique_user_diet_date', type_='unique')
        batch_op.drop_column('date')
