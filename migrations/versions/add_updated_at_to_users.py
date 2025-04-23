"""add updated_at to users

Revision ID: add_updated_at_to_users
Revises: add_meal_type_to_templates
Create Date: 2024-03-21 09:17:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_updated_at_to_users'
down_revision = 'add_meal_type_to_templates'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona a coluna updated_at
    op.add_column('users',
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )

def downgrade():
    op.drop_column('users', 'updated_at') 