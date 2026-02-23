"""update_craving_categories_v2

Revision ID: 1e9ef979997a
Revises: a1c25c03570e
Create Date: 2026-02-23 21:45:58.833903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e9ef979997a'
down_revision: Union[str, Sequence[str], None] = 'a1c25c03570e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Handle the Enum change for Postgres
    # First rename the old type to avoid conflict
    op.execute("ALTER TYPE cravingcategory RENAME TO cravingcategory_v1")
    
    # Create the new enum type
    new_categories = ('food', 'snacks', 'drinks', 'gadgets', 'furniture', 'electronics', 'clothing', 'beauty_health', 'books', 'other')
    new_enum = sa.Enum(*new_categories, name='cravingcategory')
    new_enum.create(op.get_bind())
    
    # Alter the column to use the new type with a cast
    # We map old values to new ones where possible, otherwise 'other'
    op.execute("""
        ALTER TABLE cravings ALTER COLUMN category TYPE cravingcategory 
        USING (
            CASE 
                WHEN category::text = 'food_snacks' THEN 'food'::cravingcategory
                WHEN category::text IN ('food', 'snacks', 'drinks', 'gadgets', 'furniture', 'electronics', 'clothing', 'beauty_health', 'books', 'other') 
                THEN category::text::cravingcategory 
                ELSE 'other'::cravingcategory 
            END
        )
    """)
    
    # Drop the old type
    op.execute("DROP TYPE cravingcategory_v1")


def downgrade() -> None:
    # Rename current to avoid conflict
    op.execute("ALTER TYPE cravingcategory RENAME TO cravingcategory_v2")
    
    # Recreate the previous enum type
    prev_categories = ('food_snacks', 'gadgets', 'furniture', 'electronics', 'clothing', 'beauty_health', 'books', 'other')
    prev_enum = sa.Enum(*prev_categories, name='cravingcategory')
    prev_enum.create(op.get_bind())
    
    # Alter column back with cast
    op.execute("""
        ALTER TABLE cravings ALTER COLUMN category TYPE cravingcategory 
        USING (
            CASE 
                WHEN category::text = 'food' THEN 'food_snacks'::cravingcategory
                WHEN category::text IN ('food_snacks', 'gadgets', 'furniture', 'electronics', 'clothing', 'beauty_health', 'books', 'other') 
                THEN category::text::cravingcategory 
                ELSE 'other'::cravingcategory 
            END
        )
    """)
    
    # Drop renamed v2 type
    op.execute("DROP TYPE cravingcategory_v2")
