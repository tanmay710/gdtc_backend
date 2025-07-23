"""Add role column to users table

Revision ID: 427dba13018b
Revises: 57cc1027dd1e
Create Date: 2025-07-11 17:36:37.910696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '427dba13018b'
down_revision: Union[str, Sequence[str], None] = '57cc1027dd1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
