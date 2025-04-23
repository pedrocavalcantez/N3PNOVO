"""Add meals_data to meal_templates

Revision ID: 23456789abcd
Revises: 123456789abc
Create Date: 2024-04-24 03:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "23456789abcd"
down_revision = "123456789abc"
branch_labels = None
depends_on = None


def upgrade():
    # Add meals_data column to meal_templates
    op.add_column(
        "meal_templates",
        sa.Column("meals_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )


def downgrade():
    # Remove meals_data column
    op.drop_column("meal_templates", "meals_data")
