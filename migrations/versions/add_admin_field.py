"""add admin field

Revision ID: add_admin_field
Revises: create_meals
Create Date: 2024-03-21 09:11:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_admin_field'
down_revision = 'create_meals'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona a coluna admin
    op.add_column('users',
        sa.Column('admin', sa.Boolean(), nullable=False, server_default='0')
    )

def downgrade():
    op.drop_column('users', 'admin') 