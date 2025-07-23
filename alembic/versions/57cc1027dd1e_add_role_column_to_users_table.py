"""Add role column to users table

Revision ID: 57cc1027dd1e
Revises: 238c4779b4d7
Create Date: 2025-07-11 17:22:32.670116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57cc1027dd1e'
down_revision: Union[str, Sequence[str], None] = '238c4779b4d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
