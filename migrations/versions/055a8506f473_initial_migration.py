"""initial migration

Revision ID: 055a8506f473
Revises: 
Create Date: 2025-04-02 17:14:15.056704

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '055a8506f473'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('food_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('quantity', sa.Float(), nullable=False),
    sa.Column('calories', sa.Float(), nullable=False),
    sa.Column('proteins', sa.Float(), nullable=False),
    sa.Column('carbs', sa.Float(), nullable=False),
    sa.Column('fats', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('idade', sa.Integer(), nullable=False),
    sa.Column('altura', sa.Float(), nullable=False),
    sa.Column('peso', sa.Float(), nullable=False),
    sa.Column('sexo', sa.String(length=1), nullable=False),
    sa.Column('fator_atividade', sa.String(length=20), nullable=False),
    sa.Column('objetivo', sa.String(length=50), nullable=False),
    sa.Column('calories_goal', sa.Float(), nullable=True),
    sa.Column('proteins_goal', sa.Float(), nullable=True),
    sa.Column('carbs_goal', sa.Float(), nullable=True),
    sa.Column('fats_goal', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('diets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('meals_data', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('diets')
    op.drop_table('users')
    op.drop_table('food_data')
    # ### end Alembic commands ###
