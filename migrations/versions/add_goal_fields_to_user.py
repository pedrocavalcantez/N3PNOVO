"""Add nutrition goal fields to User model

Revision ID: add_goal_fields_to_user
Revises: 369c037b5f3a
Create Date: 2024-04-01 23:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_goal_fields_to_user"
down_revision = "369c037b5f3a"
branch_labels = None
depends_on = None


def upgrade():
    # Create a new table with all columns including the new ones
    op.create_table(
        "user_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(length=120), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("idade", sa.Integer(), nullable=False),
        sa.Column("altura", sa.Float(), nullable=False),
        sa.Column("peso", sa.Float(), nullable=False),
        sa.Column("sexo", sa.String(length=1), nullable=False),
        sa.Column("fator_atividade", sa.String(length=20), nullable=False),
        sa.Column("objetivo", sa.String(length=50), nullable=False),
        sa.Column("calories_goal", sa.Float(), nullable=True),
        sa.Column("proteins_goal", sa.Float(), nullable=True),
        sa.Column("carbs_goal", sa.Float(), nullable=True),
        sa.Column("fats_goal", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data from the old table to the new one
    op.execute(
        "INSERT INTO user_new (id, username, password_hash, nome, idade, altura, peso, sexo, fator_atividade, objetivo) "
        "SELECT id, username, password_hash, nome, idade, altura, peso, sexo, fator_atividade, objetivo FROM user"
    )

    # Drop the old table
    op.drop_table("user")

    # Rename the new table to the original name
    op.rename_table("user_new", "user")


def downgrade():
    # Create the old table structure
    op.create_table(
        "user_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(length=120), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("idade", sa.Integer(), nullable=False),
        sa.Column("altura", sa.Float(), nullable=False),
        sa.Column("peso", sa.Float(), nullable=False),
        sa.Column("sexo", sa.String(length=1), nullable=False),
        sa.Column("fator_atividade", sa.String(length=20), nullable=False),
        sa.Column("objetivo", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data back, excluding the new columns
    op.execute(
        "INSERT INTO user_old (id, username, password_hash, nome, idade, altura, peso, sexo, fator_atividade, objetivo) "
        "SELECT id, username, password_hash, nome, idade, altura, peso, sexo, fator_atividade, objetivo FROM user"
    )

    # Drop the new table
    op.drop_table("user")

    # Rename the old table back to the original name
    op.rename_table("user_old", "user")
