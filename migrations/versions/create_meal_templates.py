"""create meal templates

Revision ID: create_meal_templates
Revises: add_admin_field
Create Date: 2024-03-21 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'create_meal_templates'
down_revision = 'add_admin_field'
branch_labels = None
depends_on = None

def upgrade():
    # Cria a tabela meal_templates
    op.create_table('meal_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Cria a tabela meal_template_items
    op.create_table('meal_template_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('food_code', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['meal_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('meal_template_items')
    op.drop_table('meal_templates') 