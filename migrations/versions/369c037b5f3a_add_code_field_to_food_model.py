"""Add code field to Food model

Revision ID: 369c037b5f3a
Revises:
Create Date: 2024-04-01 22:33:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "369c037b5f3a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create a new table with all columns including the new one
    op.create_table(
        "food_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("proteins", sa.Float(), nullable=False),
        sa.Column("carbs", sa.Float(), nullable=False),
        sa.Column("fats", sa.Float(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("meal_type", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data from the old table to the new one
    op.execute(
        "INSERT INTO food_new (id, code, name, quantity, calories, proteins, carbs, fats, user_id, date, meal_type) "
        'SELECT id, "LEGACY_" || id, name, quantity, calories, proteins, carbs, fats, user_id, date, meal_type FROM food'
    )

    # Drop the old table
    op.drop_table("food")

    # Rename the new table to the original name
    op.rename_table("food_new", "food")


def downgrade():
    # Create the old table structure
    op.create_table(
        "food_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("proteins", sa.Float(), nullable=False),
        sa.Column("carbs", sa.Float(), nullable=False),
        sa.Column("fats", sa.Float(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("meal_type", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data back, excluding the code column
    op.execute(
        "INSERT INTO food_old (id, name, quantity, calories, proteins, carbs, fats, user_id, date, meal_type) "
        "SELECT id, name, quantity, calories, proteins, carbs, fats, user_id, date, meal_type FROM food"
    )

    # Drop the new table
    op.drop_table("food")

    # Rename the old table back to the original name
    op.rename_table("food_old", "food")
