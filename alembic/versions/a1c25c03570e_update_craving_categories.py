"""update_craving_categories

Revision ID: a1c25c03570e
Revises: d502fd1f34f9
Create Date: 2026-02-23 20:58:38.415815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c25c03570e'
down_revision: Union[str, Sequence[str], None] = 'd502fd1f34f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Handle the Enum change for Postgres
    # First rename the old type to avoid conflict
    op.execute("ALTER TYPE cravingcategory RENAME TO cravingcategory_old")
    
    # Create the new enum type
    new_enum = sa.Enum('food_snacks', 'gadgets', 'furniture', 'electronics', 'clothing', 'beauty_health', 'books', 'other', name='cravingcategory')
    new_enum.create(op.get_bind())
    
    # Alter the column to use the new type with a cast (defaulting to 'other' for incompatible types)
    op.execute("ALTER TABLE cravings ALTER COLUMN category TYPE cravingcategory USING (CASE WHEN category::text IN ('food_snacks', 'gadgets', 'furniture', 'electronics', 'clothing', 'beauty_health', 'books', 'other') THEN category::text::cravingcategory ELSE 'other'::cravingcategory END)")
    
    # Drop the old type
    op.execute("DROP TYPE cravingcategory_old")


def downgrade() -> None:
    # Rename current to avoid conflict
    op.execute("ALTER TYPE cravingcategory RENAME TO cravingcategory_old")
    
    # Recreate the old enum type
    old_categories = ('local_delicacies', 'continental', 'street_food', 'desserts', 'beverages', 'snacks', 'healthy', 'breakfast', 'night_cravings', 'seafood', 'grills', 'fast_food', 'other')
    old_enum = sa.Enum(*old_categories, name='cravingcategory')
    old_enum.create(op.get_bind())
    
    # Alter column back with cast
    op.execute(f"ALTER TABLE cravings ALTER COLUMN category TYPE cravingcategory USING (CASE WHEN category::text IN {old_categories} THEN category::text::cravingcategory ELSE 'other'::cravingcategory END)")
    
    # Drop renamed old type
    op.execute("DROP TYPE cravingcategory_old")
