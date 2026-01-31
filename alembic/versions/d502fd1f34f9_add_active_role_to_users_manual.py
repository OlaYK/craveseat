"""add_active_role_to_users_manual

Revision ID: d502fd1f34f9
Revises: 4ea9b4884e7f
Create Date: 2026-01-26 22:00:30.148069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd502fd1f34f9'
down_revision: Union[str, Sequence[str], None] = '02babf1282b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # First, ensure the usertype enum has 'both' value
    # We use execute with text() to be safe
    op.execute("ALTER TYPE usertype ADD VALUE IF NOT EXISTS 'both'")
    
    # Add active_role column (nullable)
    op.add_column('users', sa.Column('active_role', sa.Enum('user', 'vendor', 'both', name='usertype'), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'active_role')
